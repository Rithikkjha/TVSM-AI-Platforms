"""SLM Engine Service - Ollama client wrapper with OpenRouter fallback.

Manages the embedded Small Language Model lifecycle: loading, inference,
health checks, and resource management. Primary: local inference via Ollama.
Fallback: OpenRouter API when Ollama is unavailable.

Requirements: 8.1, 8.3, 8.4, 8.5, 8.6, 17.1, 17.2, 17.3, 17.5, 17.8, 21.3, 21.11, 21.12, 21.13
"""

import asyncio
import logging
import os
import time
from typing import Optional

import httpx
import ollama
from ollama import ResponseError

from app.models.schemas import SLMConfig, SLMModelInfo, SLMOptions, SLMResponse

logger = logging.getLogger(__name__)

# Environment variable defaults
DEFAULT_MODEL_NAME = "qwen3:4b"
DEFAULT_CONTEXT_WINDOW = 8192
DEFAULT_TEMPERATURE = 0.1
INFERENCE_TIMEOUT_SECONDS = 300  # was 120; raised for large estimation prompts on the shared Azure OpenAI (POC) endpoint
MAX_RETRIES = 2

# OpenRouter fallback config
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-2-9b-it:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Azure OpenAI fallback config (priority: Ollama → Azure OpenAI → OpenRouter)
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT_GPT4O", "gpt-4o-mini")
# API version — GPT-5.6 family (gpt-5.6-luna) needs a recent version. Overridable via env.
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")


class SLMEngineError(Exception):
    """Base exception for SLM engine errors."""

    pass


class SLMStartupError(SLMEngineError):
    """Raised when the SLM engine cannot start (Ollama unreachable or model not pulled)."""

    pass


class SLMResourceError(SLMEngineError):
    """Raised when there are insufficient resources (RAM, disk) for the model."""

    pass


class SLMInferenceError(SLMEngineError):
    """Raised when inference fails (timeout or malformed output after retries)."""

    pass


class ModelNotLoadedError(SLMInferenceError):
    """Raised when inference is attempted but no model is loaded."""

    pass


class InsufficientRAMError(SLMResourceError):
    """Raised when the host machine has insufficient RAM for the configured model."""

    pass


class InferenceTimeoutError(SLMInferenceError):
    """Raised when inference exceeds the configured timeout."""

    pass


class OllamaNotAvailableError(SLMStartupError):
    """Raised when Ollama is not running or reachable."""

    pass


class ModelNotPulledError(SLMStartupError):
    """Raised when the configured model has not been pulled."""

    pass


class MalformedOutputError(SLMInferenceError):
    """Raised when the SLM returns unparseable output."""

    pass


class SLMEngine:
    """Manages the local SLM via Ollama for inference.

    Handles model loading, inference with retry logic, health checks,
    and graceful error handling for common failure modes.
    Falls back to OpenRouter API when Ollama is unavailable.
    """

    def __init__(self, config: Optional[SLMConfig] = None):
        """Initialize the SLM engine.

        Args:
            config: Optional SLM configuration. If not provided,
                    configuration is read from environment variables.
        """
        self._config = config or self._config_from_env()
        self._loaded = False
        self._use_openrouter = False
        self._use_azure_openai = False
        self._client = ollama.Client(host=self._get_ollama_host())
        self._memory_usage_mb: float = 0.0

    @staticmethod
    def _get_ollama_host() -> str:
        """Get the Ollama host URL from environment or default."""
        return os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    @staticmethod
    def _config_from_env() -> SLMConfig:
        """Build SLMConfig from environment variables."""
        model_name = os.environ.get("SLM_MODEL_NAME", DEFAULT_MODEL_NAME)
        context_window = int(
            os.environ.get("SLM_CONTEXT_WINDOW", str(DEFAULT_CONTEXT_WINDOW))
        )
        gpu_layers_str = os.environ.get("SLM_GPU_LAYERS")
        gpu_layers = int(gpu_layers_str) if gpu_layers_str else None

        return SLMConfig(
            modelPath=model_name,  # For Ollama, modelPath is the model tag
            modelName=model_name,
            contextWindow=context_window,
            gpuLayers=gpu_layers,
        )

    @property
    def config(self) -> SLMConfig:
        """Return the current SLM configuration."""
        return self._config

    @property
    def is_loaded(self) -> bool:
        """Return whether a model is currently loaded."""
        return self._loaded

    async def health_check(self) -> dict:
        """Verify Ollama is running and the configured model is available.

        Performs startup health check:
        1. Verifies Ollama server is reachable
        2. Verifies the configured model is pulled and available

        Returns:
            dict with keys: healthy (bool), message (str)

        Raises:
            OllamaNotAvailableError: If Ollama is not reachable.
            ModelNotPulledError: If the configured model is not available.
        """
        # Step 1: Check if Ollama is reachable
        try:
            models_response = await asyncio.to_thread(self._client.list)
        except Exception as e:
            error_msg = (
                f"Ollama is not running or not reachable at {self._get_ollama_host()}. "
                f"Please ensure Ollama is installed and running.\n"
                f"Install: https://ollama.com/download\n"
                f"Start: 'ollama serve'\n"
                f"Error: {e}"
            )
            logger.error(error_msg)
            raise OllamaNotAvailableError(error_msg)

        # Step 2: Check if the configured model is pulled
        available_models = [
            m.model for m in getattr(models_response, "models", [])
        ]
        # Also check without tag suffix for flexible matching
        model_name = self._config.modelName
        model_found = any(
            model_name in m or m.startswith(model_name.split(":")[0])
            for m in available_models
        )

        if not model_found:
            error_msg = (
                f"Model '{model_name}' is not available in Ollama. "
                f"Please pull it first:\n"
                f"  ollama pull {model_name}\n"
                f"Available models: {available_models}"
            )
            logger.error(error_msg)
            raise ModelNotPulledError(error_msg)

        logger.info(
            f"Health check passed: Ollama is running, model '{model_name}' is available."
        )
        return {"healthy": True, "message": f"Model '{model_name}' is ready."}

    async def load_model(self, config: Optional[SLMConfig] = None) -> None:
        """Load the SLM model into memory via Ollama, or fall back to OpenRouter.

        Args:
            config: Optional new configuration to apply before loading.

        Raises:
            SLMEngineError: If neither Azure OpenAI nor Ollama is available.
        """
        if config:
            self._config = config

        model_name = self._config.modelName

        # Try Azure OpenAI first (if configured)
        if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT:
            try:
                url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
                async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                    resp = await client.post(
                        url,
                        headers={"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"},
                        json={"messages": [{"role": "user", "content": "ping"}], "max_completion_tokens": 5},
                    )
                    if resp.status_code == 200:
                        self._loaded = True
                        self._use_openrouter = False
                        self._use_azure_openai = True
                        logger.info(f"Azure OpenAI active (primary). Deployment: {AZURE_OPENAI_DEPLOYMENT}")
                        return
                    else:
                        logger.warning(f"Azure OpenAI returned {resp.status_code}: {resp.text[:100]}. Trying Ollama fallback...")
            except Exception as e:
                logger.warning(f"Azure OpenAI not available: {e}. Trying Ollama fallback...")

        # Fallback: Ollama (local SLM)
        try:
            await self.health_check()

            await asyncio.to_thread(
                self._client.generate,
                model=model_name,
                prompt="",
                options={"num_ctx": self._config.contextWindow},
                keep_alive="10m",
            )
            self._loaded = True
            self._use_openrouter = False
            self._use_azure_openai = False

            try:
                ps_response = await asyncio.to_thread(self._client.ps)
                for model_info in getattr(ps_response, "models", []):
                    if model_name in getattr(model_info, "name", ""):
                        size_bytes = getattr(model_info, "size", 0)
                        self._memory_usage_mb = size_bytes / (1024 * 1024)
                        break
            except Exception:
                self._memory_usage_mb = 0.0

            logger.info(f"Model '{model_name}' loaded successfully via Ollama (fallback).")
            return

        except (OllamaNotAvailableError, ModelNotPulledError, SLMEngineError) as e:
            logger.warning(f"Ollama not available: {e}.")

        except Exception as e:
            logger.warning(f"Ollama load failed: {e}.")

        # Neither available
        raise SLMEngineError(
            "Neither Azure OpenAI nor Ollama is available. "
            "Configure AZURE_OPENAI_KEY + AZURE_OPENAI_ENDPOINT, or start Ollama."
        )

    async def inference(
        self, prompt: str, options: Optional[SLMOptions] = None
    ) -> SLMResponse:
        """Run inference on the loaded model with retry logic.

        Uses OpenRouter API if Ollama is unavailable. Retries up to
        MAX_RETRIES (2) additional times on timeout or malformed output.

        Args:
            prompt: The prompt to send to the model.
            options: Optional inference options (temperature, max_tokens, etc.)

        Returns:
            SLMResponse with content, model name, usage stats, and inference time.

        Raises:
            ModelNotLoadedError: If no model is loaded.
            InferenceTimeoutError: If all retries exceed the timeout.
            MalformedOutputError: If all retries produce unparseable output.
            SLMEngineError: For other inference errors.
        """
        if not self._loaded:
            raise ModelNotLoadedError(
                "No model is currently loaded. Call load_model() first."
            )

        # Route to OpenRouter if that's what we're using
        if self._use_azure_openai:
            return await self._inference_azure_openai(prompt, options)
        if self._use_openrouter:
            return await self._inference_openrouter(prompt, options)

        temperature = DEFAULT_TEMPERATURE
        max_tokens = 4096
        top_p = 0.9
        stop_sequences = None

        if options:
            if options.temperature is not None:
                temperature = options.temperature
            if options.maxTokens is not None:
                max_tokens = options.maxTokens
            if options.topP is not None:
                top_p = options.topP
            if options.stopSequences is not None:
                stop_sequences = options.stopSequences

        # Also allow environment override for temperature
        env_temp = os.environ.get("SLM_TEMPERATURE")
        if env_temp and options is None:
            temperature = float(env_temp)

        ollama_options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "top_p": top_p,
            "num_ctx": self._config.contextWindow,
        }
        if stop_sequences:
            ollama_options["stop"] = stop_sequences

        last_error: Optional[Exception] = None

        for attempt in range(1 + MAX_RETRIES):
            try:
                start_time = time.time()

                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._client.generate,
                        model=self._config.modelName,
                        prompt=prompt,
                        options=ollama_options,
                    ),
                    timeout=INFERENCE_TIMEOUT_SECONDS,
                )

                elapsed_ms = (time.time() - start_time) * 1000

                # Validate response structure
                content = getattr(response, "response", None)
                if content is None:
                    # Try dict access for compatibility
                    if isinstance(response, dict):
                        content = response.get("response")

                if content is None or not isinstance(content, str):
                    last_error = MalformedOutputError(
                        f"SLM returned malformed output on attempt {attempt + 1}. "
                        f"Response type: {type(response)}"
                    )
                    logger.warning(
                        f"Malformed output on attempt {attempt + 1}/{1 + MAX_RETRIES}: "
                        f"{last_error}"
                    )
                    continue

                # Extract token usage
                prompt_tokens = 0
                completion_tokens = 0
                if isinstance(response, dict):
                    prompt_tokens = response.get("prompt_eval_count", 0) or 0
                    completion_tokens = response.get("eval_count", 0) or 0
                else:
                    prompt_tokens = getattr(response, "prompt_eval_count", 0) or 0
                    completion_tokens = getattr(response, "eval_count", 0) or 0

                return SLMResponse(
                    content=content,
                    model=self._config.modelName,
                    usage={
                        "promptTokens": prompt_tokens,
                        "completionTokens": completion_tokens,
                    },
                    inferenceTimeMs=elapsed_ms,
                )

            except asyncio.TimeoutError:
                last_error = InferenceTimeoutError(
                    f"Inference timed out after {INFERENCE_TIMEOUT_SECONDS}s "
                    f"on attempt {attempt + 1}/{1 + MAX_RETRIES}."
                )
                logger.warning(str(last_error))
                continue

            except (ModelNotLoadedError, MalformedOutputError):
                raise

            except ResponseError as e:
                error_str = str(e).lower()
                if "not found" in error_str or "not loaded" in error_str:
                    self._loaded = False
                    raise ModelNotLoadedError(
                        f"Model '{self._config.modelName}' is no longer available. "
                        f"It may have been unloaded. Please reload the model."
                    )
                last_error = SLMEngineError(f"Ollama inference error: {e}")
                logger.warning(
                    f"Inference error on attempt {attempt + 1}: {last_error}"
                )
                continue

            except Exception as e:
                last_error = SLMEngineError(f"Unexpected inference error: {e}")
                logger.warning(
                    f"Unexpected error on attempt {attempt + 1}: {last_error}"
                )
                continue

        # All retries exhausted
        if isinstance(last_error, InferenceTimeoutError):
            raise InferenceTimeoutError(
                f"Inference timed out after {MAX_RETRIES + 1} attempts "
                f"(timeout: {INFERENCE_TIMEOUT_SECONDS}s each). "
                f"The estimation service is temporarily unavailable. Please retry."
            )
        elif isinstance(last_error, MalformedOutputError):
            raise MalformedOutputError(
                f"SLM returned unparseable output after {MAX_RETRIES + 1} attempts. "
                f"Could not complete estimation. Please retry or contact admin. "
                f"Consider adjusting model parameters (temperature, context window)."
            )
        else:
            raise last_error or SLMEngineError("Inference failed for unknown reasons.")

    def get_model_info(self) -> SLMModelInfo:
        """Get information about the currently configured model.

        Returns:
            SLMModelInfo with model details and status.
        """
        if self._use_azure_openai:
            return SLMModelInfo(
                modelName=f"azure/{AZURE_OPENAI_DEPLOYMENT}",
                modelPath="azure-openai-api",
                parameterCount="Cloud",
                contextWindow=self._config.contextWindow,
                loaded=self._loaded,
                memoryUsageMB=0.0,
            )

        if self._use_openrouter:
            return SLMModelInfo(
                modelName=OPENROUTER_MODEL,
                modelPath="openrouter-api",
                parameterCount="Cloud",
                contextWindow=self._config.contextWindow,
                loaded=self._loaded,
                memoryUsageMB=0.0,
            )

        param_count = self._extract_param_count(self._config.modelName)

        return SLMModelInfo(
            modelName=self._config.modelName,
            modelPath=self._config.modelPath,
            parameterCount=param_count,
            contextWindow=self._config.contextWindow,
            loaded=self._loaded,
            memoryUsageMB=self._memory_usage_mb,
        )

    async def unload_model(self) -> None:
        """Unload the model from memory.

        Sends a request to Ollama to free the model from memory.
        """
        if not self._loaded:
            logger.info("No model is loaded, nothing to unload.")
            return

        try:
            # Setting keep_alive to 0 tells Ollama to unload immediately
            await asyncio.to_thread(
                self._client.generate,
                model=self._config.modelName,
                prompt="",
                keep_alive=0,
            )
            self._loaded = False
            self._memory_usage_mb = 0.0
            logger.info(f"Model '{self._config.modelName}' unloaded successfully.")
        except Exception as e:
            logger.warning(f"Error unloading model: {e}")
            # Mark as unloaded regardless since we can't guarantee state
            self._loaded = False
            self._memory_usage_mb = 0.0

    @staticmethod
    def _extract_param_count(model_name: str) -> str:
        """Extract parameter count string from model name.

        Examples:
            'qwen3:4b' -> '4B'
            'gemma4:4b' -> '4B'
            'qwen3:1.7b' -> '1.7B'
            'custom-model' -> 'Unknown'
        """
        parts = model_name.lower().split(":")
        if len(parts) > 1:
            tag = parts[-1]
            # Look for patterns like '4b', '1.7b', '0.6b', '8b'
            for segment in tag.split("-"):
                if segment.endswith("b") and segment[:-1].replace(".", "").isdigit():
                    return segment.upper()
        return "Unknown"

    async def _inference_azure_openai(
        self, prompt: str, options: Optional[SLMOptions] = None
    ) -> SLMResponse:
        """Run inference via Azure OpenAI API (fallback mode)."""
        import time as _time

        temperature = DEFAULT_TEMPERATURE
        max_tokens = 4096
        if options:
            if options.temperature is not None:
                temperature = options.temperature
            if options.maxTokens is not None:
                max_tokens = options.maxTokens

        url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        headers = {
            "api-key": AZURE_OPENAI_KEY,
            "Content-Type": "application/json",
        }
        # GPT-5.6 family (gpt-5.6-luna): omit `temperature` (only default allowed)
        # and use `max_completion_tokens` instead of `max_tokens`.
        body = {
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": max_tokens,
        }

        start = _time.time()
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=INFERENCE_TIMEOUT_SECONDS, verify=False) as client:
                    resp = await client.post(url, headers=headers, json=body)

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    elapsed = _time.time() - start
                    return SLMResponse(
                        content=content,
                        model=f"azure/{AZURE_OPENAI_DEPLOYMENT}",
                        usage={
                            "promptTokens": usage.get("prompt_tokens", 0),
                            "completionTokens": usage.get("completion_tokens", 0),
                        },
                        inferenceTimeMs=int(elapsed * 1000),
                    )
                elif resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Azure OpenAI rate limited (attempt {attempt+1}). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                else:
                    raise SLMEngineError(f"Azure OpenAI API error ({resp.status_code}): {resp.text[:200]}")
            except httpx.TimeoutException:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Azure OpenAI timeout (attempt {attempt+1}). Retrying...")
                    continue
                raise InferenceTimeoutError("Azure OpenAI inference timed out after all retries")
            except SLMEngineError:
                raise
            except Exception as e:
                raise SLMEngineError(f"Azure OpenAI inference failed: {e}")

        raise SLMEngineError("Azure OpenAI inference failed after all retries")

    async def _inference_openrouter(
        self, prompt: str, options: Optional[SLMOptions] = None
    ) -> SLMResponse:
        """Run inference via OpenRouter API (fallback mode).

        Args:
            prompt: The prompt to send.
            options: Optional inference options.

        Returns:
            SLMResponse with content from OpenRouter.
        """
        temperature = DEFAULT_TEMPERATURE
        max_tokens = 4096

        if options:
            if options.temperature is not None:
                temperature = options.temperature
            if options.maxTokens is not None:
                max_tokens = options.maxTokens

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Project Estimation Tool",
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(1 + MAX_RETRIES):
            try:
                start_time = time.time()

                async with httpx.AsyncClient(timeout=INFERENCE_TIMEOUT_SECONDS, verify=False) as client:
                    resp = await client.post(
                        OPENROUTER_BASE_URL,
                        headers=headers,
                        json=payload,
                    )

                elapsed_ms = (time.time() - start_time) * 1000

                if resp.status_code != 200:
                    last_error = SLMEngineError(
                        f"OpenRouter API error ({resp.status_code}): {resp.text[:200]}"
                    )
                    logger.warning(f"OpenRouter attempt {attempt + 1} failed: {last_error}")
                    continue

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content:
                    last_error = MalformedOutputError("OpenRouter returned empty content")
                    continue

                usage = data.get("usage", {})

                return SLMResponse(
                    content=content,
                    model=OPENROUTER_MODEL,
                    usage={
                        "promptTokens": usage.get("prompt_tokens", 0),
                        "completionTokens": usage.get("completion_tokens", 0),
                    },
                    inferenceTimeMs=elapsed_ms,
                )

            except httpx.TimeoutException:
                last_error = InferenceTimeoutError(
                    f"OpenRouter timed out on attempt {attempt + 1}"
                )
                continue
            except Exception as e:
                last_error = SLMEngineError(f"OpenRouter inference error: {e}")
                continue

        raise last_error or SLMEngineError("OpenRouter inference failed after all retries.")
