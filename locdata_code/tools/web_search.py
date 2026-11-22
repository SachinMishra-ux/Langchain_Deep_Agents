"""Web search tool for LocData Code."""

from __future__ import annotations

import warnings
from duckduckgo_search import DDGS
from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for up-to-date documentation, real-time facts, APIs, error solutions, and code references.

    Args:
        query: The search keywords or natural language query.
        max_results: Maximum number of search results to return (default 5).

    Returns:
        Formatted markdown containing titles, links, and snippets of results.
    """
    try:
        results = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    title = r.get("title", "")
                    link = r.get("href", "")
                    body = r.get("body", "")
                    results.append(f"### {title}\n**URL:** {link}\n{body}\n")

        if not results:
            return f"No results found for query: '{query}'"
        return "\n".join(results)
    except Exception as e:
        return f"Web search encountered an error: {e}"
