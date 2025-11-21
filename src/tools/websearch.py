from functools import lru_cache
from langchain_tavily import TavilySearch


@lru_cache(maxsize=1)
def get_websearch_tool() -> TavilySearch:
    """Return a shared instance of TavilySearch, initialized lazily."""

    return TavilySearch(
        max_results=5,
        include_answer=True,
        include_raw_content=True,
        include_images=True,
    )
