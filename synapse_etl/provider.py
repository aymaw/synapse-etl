"""Opt-in JSON chat transport. No SDK, ambient credentials, redirects, or auto-retry."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class ProviderError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ChatPlanner:
    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 30):
        url = urlsplit(base_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError("Use an explicit HTTP(S) base URL without credentials or query")
        if url.scheme == "http" and url.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Remote model endpoints require HTTPS")
        if not model.strip() or not 0 < timeout <= 120:
            raise ValueError("Set a model name and timeout in (0,120]")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.api_key, self.timeout = model, api_key, timeout
        # Disable redirects (which could leak Authorization) and ambient proxies.
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    @classmethod
    def from_env(cls):
        if not os.getenv("MODEL_BASE_URL") or not os.getenv("MODEL_NAME"):
            raise ProviderError(
                "Set MODEL_BASE_URL and MODEL_NAME explicitly; offline demos need neither"
            )
        return cls(
            os.environ["MODEL_BASE_URL"], os.environ["MODEL_NAME"], os.getenv("MODEL_API_KEY", "")
        )

    def json(self, instruction: str, data: str) -> dict:
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "max_tokens": 2048,
                "messages": [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": data},
                ],
            }
        ).encode()
        if len(payload) > 64_000:
            raise ProviderError("Model request exceeds 64 KB")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = Request(self.url, data=payload, headers=headers, method="POST")
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read(1_048_577)
            if len(body) > 1_048_576:
                raise ProviderError("Model response exceeds 1 MB")
            envelope = json.loads(body)
            content = envelope["choices"][0]["message"]["content"]
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError("Expected object")
            return result
        except (HTTPError, URLError, TimeoutError, OSError):
            raise ProviderError("Model transport failed; inspect endpoint configuration") from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError("Model returned an invalid JSON object") from None
