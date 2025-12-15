import os
import json
import httpx
from typing import List, Optional
from src.types.orchestrator_plan import SearchResult


class SearchService:
    """Service for performing web searches using different providers"""
    
    MAX_RESULTS_SERPAPI = 10
    MAX_RESULTS_BRAVE = 5
    
    @staticmethod
    async def search(query: str, provider_override: Optional[str] = None) -> List[SearchResult]:
        """
        Search using the specified provider or default
        
        Args:
            query: The search query
            provider_override: Override the default search provider
            
        Returns:
            List of search results
        """
        provider = provider_override or os.getenv("SEARCH_PROVIDER", "brave")
        
        if provider == "brave":
            return await SearchService.search_brave(query)
        elif provider == "serpapi":
            return await SearchService.search_serpapi(query)
        else:
            return []
    
    @staticmethod
    async def search_serpapi(query: str) -> List[SearchResult]:
        """Search using ZenSERP API (historically called 'serpapi' in this project)."""
        api_key = os.getenv("ZENSERP_API_KEY") or os.getenv("SERPAPI_API_KEY")
        
        if not api_key:
            print("[search] ZENSERP_API_KEY (or SERPAPI_API_KEY) not set; returning empty results")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://app.zenserp.com/api/v2/search",
                    params={"apikey": api_key, "q": query}
                )
                data = response.json()
                
            organic = data.get("organic", [])
            results = [
                SearchResult(
                    position=r.get("position") or r.get("rank"),
                    title=r.get("title", ""),
                    link=r.get("url", ""),
                    snippet=r.get("description", "")
                )
                for r in organic[:SearchService.MAX_RESULTS_SERPAPI]
            ]
            return results
        except Exception as e:
            print(f"[search] ZenSERP search failed: {e}")
            return []
    
    @staticmethod
    async def search_brave(query: str) -> List[SearchResult]:
        """Search using Brave Search API"""
        api_key = os.getenv("BRAVE_SEARCH_API_KEY") or os.getenv("BRAVE_API_KEY")
        
        if not api_key:
            print("[search] BRAVE_SEARCH_API_KEY (or BRAVE_API_KEY) not set; returning empty results")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={"Accept": "application/json", "X-Subscription-Token": api_key},
                    params={
                        "q": query,
                        "count": SearchService.MAX_RESULTS_BRAVE,
                        "country": "us"
                    }
                )
                data = response.json()
                
            # Brave response shape is typically:
            # { "web": { "results": [ { "title": "...", "url": "...", "description": "..." }, ... ] } }
            web = data.get("web") or {}
            web_results = web.get("results") if isinstance(web, dict) else []

            results: List[SearchResult] = []
            for i, result in enumerate((web_results or [])[:SearchService.MAX_RESULTS_BRAVE]):
                results.append(
                    SearchResult(
                        position=i + 1,
                        title=result.get("title", ""),
                        link=result.get("url", ""),
                        snippet=result.get("description", "")
                    )
                )
            return results
        except Exception as e:
            print(f"[search] Brave search failed: {e}")
            return []
    
    @staticmethod
    async def get_web_page(url: str) -> str:
        """
        Fetch and parse the content of a webpage
        
        Args:
            url: The URL to fetch
            
        Returns:
            The text content of the webpage
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                
            # Basic HTML to text conversion
            text = response.text
            
            # Remove script and style elements
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '\n', text)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            return text[:5000]  # Limit to first 5000 chars
        except Exception as e:
            print(f"[search] Failed to get web page {url}: {e}")
            return f"Error fetching page: {str(e)}"
