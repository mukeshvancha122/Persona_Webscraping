import os
import asyncio
from typing import Any, Dict, List, Optional

try:
    from perplexity import Perplexity
except Exception:  # pragma: no cover - import-time guard
    Perplexity = None


class PerplexitySDK:
    """Thin wrapper around the official `perplexity` SDK.

    Provides an async `search` method that runs the SDK call in a threadpool.
    """

    def __init__(self, api_key: Optional[str] = None):
        if Perplexity is None:
            raise RuntimeError("perplexity SDK is not installed. Install with `pip install perplexityai`.")

        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")

        # The SDK may read from env var; pass explicitly if supported
        try:
            self.client = Perplexity(api_key=self.api_key)
        except TypeError:
            # fallback if SDK expects no arg
            self.client = Perplexity()

    def _search_sync(self, query: str, max_results: int = 5, max_tokens_per_page: int = 1024) -> Any:
        # SDK demo: client.search.create(query=..., max_results=..., max_tokens_per_page=...)
        return self.client.search.create(
            query=query, max_results=max_results, max_tokens_per_page=max_tokens_per_page
        )

    async def search(self, query: str, max_results: int = 5, max_tokens_per_page: int = 1024) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._search_sync, query, max_results, max_tokens_per_page)

    @staticmethod
    def extract_structured(result_obj: Any) -> Dict[str, Optional[str]]:
        """Extract a small structured dict from an SDK result object.

        The SDK's result objects may include attributes like `title`, `url`, `snippet` or `text`.
        This helper is defensive and returns None for missing fields.
        """
        out: Dict[str, Optional[str]] = {"title": None, "url": None, "snippet": None}
        try:
            # many SDK result objects expose attributes
            out["title"] = getattr(result_obj, "title", None) or (result_obj.get("title") if isinstance(result_obj, dict) else None)
        except Exception:
            pass
        try:
            out["url"] = getattr(result_obj, "url", None) or (result_obj.get("url") if isinstance(result_obj, dict) else None)
        except Exception:
            pass
        try:
            # snippet/text may be nested
            out["snippet"] = (
                getattr(result_obj, "snippet", None)
                or getattr(result_obj, "text", None)
                or (result_obj.get("snippet") if isinstance(result_obj, dict) else None)
            )
        except Exception:
            pass
        return out
