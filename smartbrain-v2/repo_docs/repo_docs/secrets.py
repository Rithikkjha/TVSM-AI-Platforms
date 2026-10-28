"""Token loading and redaction. The token VALUE must never be printed, logged or written.

The token reaches git only through environment-scoped config (GIT_CONFIG_COUNT/KEY/VALUE),
never through argv, remote URLs or .git/config. The same env also resets
``credential.helper`` to empty so ambient helpers (osxkeychain, GCM, store) from the user's
global/system config are never invoked and cannot supply or capture other credentials.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path


class TokenError(RuntimeError):
    """Raised when the token cannot be loaded. Message never contains the value."""


def load_token(env_file: Path | str, key: str) -> str:
    path = Path(env_file)
    if not path.is_file():
        raise TokenError(f"token file not found: {path} (key {key})")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, sep, value = line.partition("=")
        if not sep or name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            # strip trailing inline comment for unquoted values
            value = value.split(" #", 1)[0].strip()
        if not value:
            raise TokenError(f"key {key} is empty in {path}")
        return value
    raise TokenError(f"key {key} not found in {path}")


def basic_auth_b64(token: str) -> str:
    return base64.b64encode(f"x-access-token:{token}".encode()).decode()


def secret_forms(token: str) -> list[str]:
    """All representations of the token that could leak (raw + git basic-auth header form)."""
    if not token:
        return []
    return [token, basic_auth_b64(token)]


def redact(text: str, secrets: list[str] | tuple[str, ...]) -> str:
    if not text:
        return text
    for s in secrets:
        if s:
            text = text.replace(s, "***")
    return text


def git_auth_env(token: str, git_base: str) -> dict[str, str]:
    """Env vars that inject an Authorization header for ``git_base`` without touching config files."""
    base = git_base.rstrip("/") + "/"
    return {
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": f"http.{base}.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic_auth_b64(token)}",
        # an empty value resets the credential.helper list -> no ambient helpers run
        "GIT_CONFIG_KEY_1": "credential.helper",
        "GIT_CONFIG_VALUE_1": "",
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "never",
        "GIT_ASKPASS": "/usr/bin/false",
    }


class SecretFilter(logging.Filter):
    """Redacts registered secrets from every log record passing through a handler."""

    _secrets: list[str] = []

    @classmethod
    def register(cls, token: str) -> None:
        for s in secret_forms(token):
            if s not in cls._secrets:
                cls._secrets.append(s)

    @classmethod
    def secrets(cls) -> list[str]:
        return list(cls._secrets)

    def filter(self, record: logging.LogRecord) -> bool:
        if self._secrets:
            msg = record.getMessage()
            record.msg = redact(msg, self._secrets)
            record.args = ()
        return True
