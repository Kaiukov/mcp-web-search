from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional
import asyncio
import logging
from duckduckgo_search import DDGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuckDuckGoServer:
    def __init__(self):
        self.mcp = FastMCP("DuckDuckGo Search Server")
        self.ddgs = DDGS()
        self.setup_tools()

    def setup_tools(self):
        """Register available search tools"""

        @self.mcp.tool()
        async def text_search(
            query: str,
            num_results: int = 5,
            region: str = "wt-wt",
            safesearch: str = "moderate",
            timelimit: Optional[str] = None
        ) -> List[Dict[str, str]]:
            """Perform a text search using DuckDuckGo"""
            try:
                results = self.ddgs.text(
                    keywords=query,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=num_results
                )
                return results
            except Exception as e:
                logger.error(f"Error during text search: {e}")
                raise ValueError(str(e))

        @self.mcp.tool()
        async def image_search(
            query: str,
            num_results: int = 5,
            region: str = "wt-wt",
            safesearch: str = "moderate",
            timelimit: Optional[str] = None,
            type_image: Optional[str] = None
        ) -> List[Dict[str, str]]:
            """Perform an image search using DuckDuckGo"""
            try:
                results = self.ddgs.images(
                    keywords=query,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    type_image=type_image,
                    max_results=num_results
                )
                return results
            except Exception as e:
                logger.error(f"Error during image search: {e}")
                raise ValueError(str(e))

        @self.mcp.tool()
        async def news_search(
            query: str,
            num_results: int = 5,
            region: str = "wt-wt",
            safesearch: str = "moderate",
            timelimit: Optional[str] = None
        ) -> List[Dict[str, str]]:
            """Perform a news search using DuckDuckGo"""
            try:
                results = self.ddgs.news(
                    keywords=query,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=num_results
                )
                return results
            except Exception as e:
                logger.error(f"Error during news search: {e}")
                raise ValueError(str(e))

    def run(self):
        """Run the server"""
        self.mcp.run()

if __name__ == "__main__":
    server = DuckDuckGoServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("Shutting down server...")
        print("Server shutdown gracefully")
    except Exception as e:
        print(f"Error running server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Server has been shut down")
