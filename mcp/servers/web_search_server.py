"""
web_search_server.py

MCP Server — web search + image search (100% free, no API key required).

Image search strategy (runs in order until a working URL is found):
  1. DuckDuckGo images — tries up to 5 candidates, HEAD-checks each URL
  2. Wikimedia Commons API — excellent for educational / science topics
  3. Wikipedia article thumbnail — almost always exists for well-known topics

Between these three sources, a relevant image is found for virtually every
educational topic.  The server only returns None if all three sources fail,
which is extremely rare.
"""

import sys
import time
import urllib.parse
import requests
from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS

mcp = FastMCP("search-server")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; auto-ppt-agent/1.0)"}
TIMEOUT = 8


# ─── helpers ────────────────────────────────────────────────────────────────

def _url_alive(url: str) -> bool:
    """Return True if the URL responds with HTTP 200."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


# ─── image source 1: DuckDuckGo ─────────────────────────────────────────────

def _ddg_image(query: str) -> str | None:
    try:
        with DDGS() as ddgs:
            # Fetch more candidates so we have fallbacks if some URLs are dead
            results = list(ddgs.images(query, max_results=5, region="wt-wt"))
        for r in results:
            url = r.get("image", "")
            if url and _url_alive(url):
                print(f"[IMG] DDG hit: {url}", file=sys.stderr)
                return url
    except Exception as e:
        print(f"[IMG] DDG error: {e}", file=sys.stderr)
    return None


# ─── image source 2: Wikimedia Commons ──────────────────────────────────────

def _wikimedia_image(query: str) -> str | None:
    """
    Search Wikimedia Commons for a relevant image.
    Uses the MediaWiki API generator — no key required.
    """
    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrnamespace": "6",         # File namespace only
            "gsrsearch": query,
            "gsrlimit": "5",
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": "800",
            "format": "json",
        }
        url = "https://commons.wikimedia.org/w/api.php"
        data = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT).json()
        pages = data.get("query", {}).get("pages", {}).values()
        for page in pages:
            info = page.get("imageinfo", [])
            for ii in info:
                mime = ii.get("mime", "")
                thumb = ii.get("thumburl") or ii.get("url", "")
                # Skip SVG and audio files — pptx can't embed them
                if thumb and "image" in mime and "svg" not in mime:
                    if _url_alive(thumb):
                        print(f"[IMG] Wikimedia hit: {thumb}", file=sys.stderr)
                        return thumb
    except Exception as e:
        print(f"[IMG] Wikimedia error: {e}", file=sys.stderr)
    return None


# ─── image source 3: Wikipedia article thumbnail ────────────────────────────

def _wikipedia_thumbnail(query: str) -> str | None:
    """
    Search Wikipedia and return the lead image thumbnail of the top article.
    Works well for any well-known topic.
    """
    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": "3",
            "prop": "pageimages",
            "piprop": "thumbnail",
            "pithumbsize": "800",
            "pilimit": "3",
            "format": "json",
        }
        data = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params=params, headers=HEADERS, timeout=TIMEOUT
        ).json()
        pages = data.get("query", {}).get("pages", {}).values()
        for page in pages:
            thumb = page.get("thumbnail", {}).get("source")
            if thumb and _url_alive(thumb):
                print(f"[IMG] Wikipedia thumb hit: {thumb}", file=sys.stderr)
                return thumb
    except Exception as e:
        print(f"[IMG] Wikipedia error: {e}", file=sys.stderr)
    return None


# ─── MCP tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def search_web(query: str) -> list[str]:
    """Search the web and return up to 3 result snippets."""
    print(f"[SEARCH] web: {query}", file=sys.stderr)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3, region="wt-wt"))
            snippets = [r["body"] for r in results if r.get("body")]
            if snippets:
                return snippets
    except Exception as e:
        print(f"[SEARCH] web error: {e}", file=sys.stderr)
    return ["No results found"]


@mcp.tool()
def search_image(query: str) -> str | None:
    """
    Find a relevant image URL for the given query.
    Tries DuckDuckGo → Wikimedia Commons → Wikipedia thumbnail.
    Returns a working image URL, or None only if all sources fail.
    """
    print(f"[SEARCH] image: {query}", file=sys.stderr)

    url = _ddg_image(query)
    if url:
        return url

    url = _wikimedia_image(query)
    if url:
        return url

    url = _wikipedia_thumbnail(query)
    if url:
        return url

    print(f"[IMG] all sources failed for: {query}", file=sys.stderr)
    return None


if __name__ == "__main__":
    print("[SEARCH SERVER] running...", file=sys.stderr)
    mcp.run()