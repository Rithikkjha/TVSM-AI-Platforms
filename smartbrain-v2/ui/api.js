/**
 * API Client for Engineering Memory Graph
 */
const ApiClient = (() => {
    function getApiKey() {
        return localStorage.getItem('emg_api_key') || '';
    }

    function getBaseUrl() {
        // Manual override wins if the user set one in Settings.
        const stored = localStorage.getItem('emg_base_url');
        if (stored && stored !== '/') {
            return stored;
        }
        // Otherwise auto-derive the prefix from where the UI is served:
        //   /brain/chatbot/... -> "/brain"   (behind nginx)
        //   /chatbot/...       -> ""          (served at root, e.g. :8000)
        return window.location.pathname.replace(/\/chatbot(\/.*)?$/, '');
    }

    function buildUrl(path) {
        const base = getBaseUrl();
        if (base && base !== '/') {
            return base.replace(/\/$/, '') + path;
        }
        return path;
    }

    function getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        const apiKey = getApiKey();
        if (apiKey) {
            headers['X-API-Key'] = apiKey;
        }
        return headers;
    }

    /**
     * Ask a question to the knowledge graph
     * POST /v1/ask { question: "...", history: [...] }
     */
    async function ask(question, history = []) {
        const url = buildUrl('/v1/ask');
        const response = await fetch(url, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ question, history })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error (${response.status}): ${errorText}`);
        }

        return response.json();
    }

    /**
     * Search for entities
     * GET /v1/search?q=...
     */
    async function search(query) {
        const url = buildUrl(`/v1/search?q=${encodeURIComponent(query)}`);
        const response = await fetch(url, {
            method: 'GET',
            headers: getHeaders()
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error (${response.status}): ${errorText}`);
        }

        return response.json();
    }

    /**
     * Get service details
     * GET /v1/services/{name}
     */
    async function getService(name) {
        const url = buildUrl(`/v1/services/${encodeURIComponent(name)}`);
        const response = await fetch(url, {
            method: 'GET',
            headers: getHeaders()
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error (${response.status}): ${errorText}`);
        }

        return response.json();
    }

    return { ask, search, getService, getApiKey, getBaseUrl };
})();
