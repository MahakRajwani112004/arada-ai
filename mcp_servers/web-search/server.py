"""Web Search MCP Server.

Provides MCP tools for web search functionality:
- search_web: Search the web using DuckDuckGo (no API key required)
- fetch_page_content: Fetch and extract text content from a URL

This server uses DuckDuckGo's HTML interface which is:
- Free to use
- No API key required
- No rate limits (be respectful)
- Open and accessible

No credentials required - this server works without authentication.
"""
import os
import re
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool


class WebSearchServer(BaseMCPServer):
    """MCP Server for web search operations using DuckDuckGo."""

    # DuckDuckGo HTML search URL
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    # User agent to mimic a browser
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Request timeout in seconds
    TIMEOUT = 30

    def __init__(self):
        super().__init__(
            name="web-search",
            version="1.0.0",
            description="Web Search MCP Server using DuckDuckGo",
        )

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> httpx.Response:
        """Make an HTTP request with proper headers.

        Args:
            url: URL to request
            method: HTTP method (GET or POST)
            data: Form data for POST requests
            headers: Additional headers

        Returns:
            httpx.Response object
        """
        default_headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(
            timeout=self.TIMEOUT,
            follow_redirects=True,
        ) as client:
            if method == "POST":
                response = await client.post(url, data=data, headers=default_headers)
            else:
                response = await client.get(url, headers=default_headers)

            response.raise_for_status()
            return response

    def _parse_search_results(self, html: str) -> List[Dict[str, str]]:
        """Parse DuckDuckGo HTML search results.

        Args:
            html: Raw HTML from DuckDuckGo

        Returns:
            List of search results with title, url, and snippet
        """
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # DuckDuckGo HTML results are in divs with class "result"
        for result in soup.find_all("div", class_="result"):
            # Extract title and URL
            title_elem = result.find("a", class_="result__a")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            # Clean up DuckDuckGo redirect URL
            if url.startswith("//duckduckgo.com/l/"):
                # Extract actual URL from redirect
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                url = parsed.get("uddg", [url])[0]

            # Extract snippet
            snippet_elem = result.find("a", class_="result__snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })

        return results

    def _extract_text_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract readable text content from HTML.

        Args:
            html: Raw HTML content
            url: Source URL for context

        Returns:
            Dictionary with extracted content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Extract title
        title = ""
        title_elem = soup.find("title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract meta description
        meta_desc = ""
        meta_elem = soup.find("meta", attrs={"name": "description"})
        if meta_elem:
            meta_desc = meta_elem.get("content", "")

        # Extract main content - try common content containers
        main_content = None
        for selector in ["article", "main", '[role="main"]', ".content", "#content", ".post", ".article"]:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # Fall back to body if no main content found
        if not main_content:
            main_content = soup.find("body")

        # Extract text
        if main_content:
            # Get text with some structure preserved
            text = main_content.get_text(separator="\n", strip=True)
            # Clean up excessive whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r" {2,}", " ", text)
        else:
            text = ""

        # Extract headings for structure
        headings = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            heading_text = h.get_text(strip=True)
            if heading_text:
                headings.append({
                    "level": h.name,
                    "text": heading_text,
                })

        return {
            "title": title,
            "meta_description": meta_desc,
            "headings": headings[:10],  # Limit to first 10 headings
            "content": text[:10000],  # Limit content length
            "content_length": len(text),
            "url": url,
        }

    @tool(
        name="search_web",
        description=(
            "Search the web using DuckDuckGo. Returns a list of search results "
            "with titles, URLs, and snippets. Use this when you need current "
            "information or don't have knowledge about a topic."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10, max: 25)",
                    "default": 10,
                },
                "region": {
                    "type": "string",
                    "description": "Region for search results (e.g., 'us-en', 'uk-en', 'de-de')",
                    "default": "wt-wt",
                },
            },
            "required": ["query"],
        },
        credential_headers=[],  # No credentials needed
    )
    async def search_web(
        self,
        credentials: Dict[str, str],
        query: str,
        max_results: int = 10,
        region: str = "wt-wt",
    ) -> Dict[str, Any]:
        """Search the web using DuckDuckGo.

        Args:
            credentials: Not used (no auth required)
            query: Search query
            max_results: Maximum results to return
            region: Region code for localized results

        Returns:
            Search results with title, URL, and snippet
        """
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Search query cannot be empty",
            }

        # Limit max results
        max_results = min(max(1, max_results), 25)

        try:
            # Make search request to DuckDuckGo HTML
            response = await self._make_request(
                self.SEARCH_URL,
                method="POST",
                data={
                    "q": query,
                    "b": "",  # No offset for first page
                    "kl": region,
                },
            )

            # Parse results
            results = self._parse_search_results(response.text)

            # Limit results
            results = results[:max_results]

            return {
                "success": True,
                "query": query,
                "results": results,
                "result_count": len(results),
                "region": region,
            }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Search request timed out. Please try again.",
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Search request failed with status {e.response.status_code}",
            }
        except Exception as e:
            self.logger.exception("search_web_error", error=str(e))
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
            }

    @tool(
        name="fetch_page_content",
        description=(
            "Fetch and extract the main text content from a web page URL. "
            "Use this to read the full content of a page found in search results."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the web page to fetch",
                },
                "include_headings": {
                    "type": "boolean",
                    "description": "Include extracted headings in response",
                    "default": True,
                },
            },
            "required": ["url"],
        },
        credential_headers=[],  # No credentials needed
    )
    async def fetch_page_content(
        self,
        credentials: Dict[str, str],
        url: str,
        include_headings: bool = True,
    ) -> Dict[str, Any]:
        """Fetch and extract content from a web page.

        Args:
            credentials: Not used (no auth required)
            url: URL to fetch
            include_headings: Whether to include extracted headings

        Returns:
            Extracted page content
        """
        if not url or not url.strip():
            return {
                "success": False,
                "error": "URL cannot be empty",
            }

        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {
                "success": False,
                "error": "Invalid URL format. Please provide a complete URL with http:// or https://",
            }

        # Only allow HTTP/HTTPS
        if parsed.scheme not in ("http", "https"):
            return {
                "success": False,
                "error": "Only HTTP and HTTPS URLs are supported",
            }

        try:
            # Fetch the page
            response = await self._make_request(url)

            # Check content type
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return {
                    "success": False,
                    "error": f"URL does not return HTML content (got: {content_type})",
                }

            # Extract content
            content = self._extract_text_content(response.text, url)

            # Optionally remove headings
            if not include_headings:
                content.pop("headings", None)

            return {
                "success": True,
                **content,
            }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timed out. The page may be slow or unavailable.",
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Failed to fetch page: HTTP {e.response.status_code}",
            }
        except Exception as e:
            self.logger.exception("fetch_page_error", url=url, error=str(e))
            return {
                "success": False,
                "error": f"Failed to fetch page: {str(e)}",
            }


# Create server instance
server = WebSearchServer()
app = server.app


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
