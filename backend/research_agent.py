import os
import logging
import json
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchAgent:
    """
    AI Research Assistant that combines web search with LLM processing
    to generate structured research notes with citations.
    """
    
    def __init__(self):
        """Initialize the research agent with LLM and search tools."""
        self._initialize_llm()
        self._initialize_search_tools()
        self._initialize_prompts()
        
    def _initialize_llm(self):
        """Initialize the Google Gemini language model."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        
        logger.info(f"Found Google API key: {google_api_key[:10]}...")
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash-latest",
                temperature=0.1,
                google_api_key=google_api_key
            )
            logger.info("Initialized Google Gemini model")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise ValueError(f"Failed to initialize Gemini model: {e}")
    
    def _initialize_search_tools(self):
        """Initialize search tools."""
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        if not serpapi_api_key:
            logger.error("SERPAPI_API_KEY not found in environment variables")
            raise ValueError("SERPAPI_API_KEY not found in environment variables.")

        logger.info(f"Found SerpAPI key: {serpapi_api_key[:10]}...")
        
        try:
            self.search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)
            logger.info("Initialized SerpAPI search tool")
        except Exception as e:
            logger.error(f"Failed to initialize SerpAPI: {e}")
            raise ValueError(f"Failed to initialize SerpAPI: {e}")
    
    def _initialize_prompts(self):
        """Initialize prompt templates."""
        self.research_prompt_template = PromptTemplate.from_template(
            """You are a research assistant. Based on the search results below, create a research note.

            QUERY: {query}

            SEARCH RESULTS: {search_results}

            Create a research note with exactly this format:

            TITLE: [Write a clear title here]

            SUMMARY: [Write 3-5 sentences summarizing the key findings]

            KEY POINTS:
            - [First key point]
            - [Second key point]
            - [Third key point]
            - [Fourth key point]
            - [Fifth key point]

            SOURCES:
            [1] [Source title] ([URL])
            [2] [Source title] ([URL])
            [3] [Source title] ([URL])

            CRITICAL SOURCE FORMATTING RULES:
            - Look for actual URLs in the search results and include them
            - Use EXACT format: [number] Title (URL)
            - Title should be the actual article/page title from the search results
            - URL must be a real web address from the search results (http:// or https://)
            - Copy URLs exactly as they appear in the search results
            - If you see URLs in the search results, you MUST include them
            - Do NOT use placeholder text like "Source title" or "no url"
            - Do NOT make up URLs - only use ones found in the search results
            - Make titles descriptive and specific to the content
            - Include at least 3 sources with real URLs if available in search results

            Be specific and use information from the search results."""
        )
    
    def run_research(self, query: str) -> Dict:
        """
        Perform comprehensive research on a given query.
        """
        try:
            logger.info(f"Starting research for query: {query}")
            
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
            
            logger.info("Performing web search...")
            search_results = self.search.run(query)
            
            # Convert list to string if needed
            if isinstance(search_results, list):
                search_results = " ".join(str(item) for item in search_results)
            
            logger.info(f"Search results length: {len(search_results) if search_results else 0}")
            
            if not search_results or str(search_results).strip() == "":
                logger.warning("No search results found")
                return self._create_empty_result(query, "No search results found for this query.")
            
            # Store search_results for later use in parsing
            self._current_search_results = search_results
            
            logger.info(f"Search completed. Processing results with LLM...")
            
            # Use LCEL (LangChain Expression Language) syntax
            chain = self.research_prompt_template | self.llm | StrOutputParser()
            raw_output = chain.invoke({"query": query, "search_results": search_results})
            
            logger.info("LLM processing completed. Parsing results...")
            
            parsed_output = self._parse_research_note(raw_output)
            self._validate_research_output(parsed_output)
            
            logger.info(f"Research completed successfully for query: {query}")
            return parsed_output

        except Exception as e:
            logger.error(f"Research failed for query '{query}': {e}")
            raise

    def _parse_research_note(self, raw_text: str) -> Dict:
        """Parse the raw LLM output into a structured format."""
        try:
            title = "Research Results"
            summary = "No summary available"
            key_points = []
            sources = []

            if not raw_text or len(raw_text.strip()) < 10:
                logger.warning(f"Raw text is too short: '{raw_text}'")
                return {
                    "title": title,
                    "summary": summary,
                    "key_points": key_points,
                    "sources": sources
                }

            lines = raw_text.split('\n')
            current_section = None
            summary_lines = []

            for line in lines:
                line = line.strip()
                
                if line.upper().startswith("TITLE:"):
                    title = line.replace("TITLE:", "").replace("title:", "").strip()
                    current_section = "title"
                elif line.upper().startswith("SUMMARY:"):
                    current_section = "summary"
                    summary_lines = []
                elif line.upper().startswith("KEY POINTS:"):
                    current_section = "key_points"
                    if summary_lines:
                        summary = " ".join(summary_lines).strip()
                elif line.upper().startswith("SOURCES:"):
                    current_section = "sources"
                    if summary_lines and summary == "No summary available":
                        summary = " ".join(summary_lines).strip()
                elif line.upper().startswith("IMPORTANT GUIDELINES:") or line.upper().startswith("CRITICAL"):
                    if summary_lines and summary == "No summary available":
                        summary = " ".join(summary_lines).strip()
                    break
                elif current_section == "summary" and line and not line.startswith(("-", "[")):
                    summary_lines.append(line)
                elif current_section == "key_points" and line.startswith("-"):
                    point = line.lstrip("-").strip()
                    if point and len(point) > 10:
                        key_points.append(point)
                elif current_section == "sources" and line.startswith("["):
                    source = self._parse_source_line(line)
                    if source:
                        sources.append(source)

            if summary_lines and summary == "No summary available":
                summary = " ".join(summary_lines).strip()

            if summary and summary != "No summary available":
                summary = summary.replace("SUMMARY:", "").strip()

            # Try to extract more sources from search results if needed
            if len(sources) < 3 and hasattr(self, '_current_search_results'):
                sources = self._extract_sources_from_search(sources)

            return {
                "title": title,
                "summary": summary,
                "key_points": key_points,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error in _parse_research_note: {e}")
            return {
                "title": "Research Results",
                "summary": "Error parsing research results",
                "key_points": [],
                "sources": []
            }

    def _parse_source_line(self, line: str) -> Optional[Dict]:
        """Parse a single source line."""
        try:
            source_title = ""
            source_url = ""
            
            if ']' in line:
                content = line.split(']', 1)[1].strip()
            else:
                content = line.strip()
            
            if '(' in content and ')' in content:
                url_start = content.rfind('(') + 1
                url_end = content.rfind(')')
                source_url = content[url_start:url_end].strip()
                source_title = content[:content.rfind('(')].strip()
            elif ' - ' in content:
                parts = content.split(' - ', 1)
                if len(parts) == 2:
                    source_title = parts[0].strip()
                    source_url = parts[1].strip()
            else:
                source_title = content.strip()
            
            if source_url:
                source_url = source_url.replace(' ', '')
                if not source_url.startswith(('http://', 'https://')):
                    if '.' in source_url:
                        source_url = 'https://' + source_url
                    else:
                        source_url = ""
            
            if source_title and len(source_title) > 3:
                return {"title": source_title, "url": source_url}
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not parse source line: '{line}'. Error: {e}")
            return None

    def _extract_sources_from_search(self, existing_sources: List[Dict]) -> List[Dict]:
        """Extract additional sources from search results."""
        try:
            search_results = self._current_search_results
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[^\s<>"{}|\\^`\[\]]*[a-zA-Z0-9])?'
            found_urls = re.findall(url_pattern, str(search_results))
            
            existing_urls = {s.get('url', '') for s in existing_sources}
            
            for url in found_urls:
                if url in existing_urls or len(url) < 15:
                    continue
                if not self._is_valid_url(url):
                    continue
                    
                domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                if domain_match:
                    title = f"Article from {domain_match.group(1)}"
                    existing_sources.append({"title": title, "url": url})
                    existing_urls.add(url)
                    
                if len(existing_sources) >= 5:
                    break
                    
            return existing_sources
            
        except Exception as e:
            logger.warning(f"Failed to extract sources from search results: {e}")
            return existing_sources
    
    def _validate_research_output(self, output: Dict) -> None:
        """Validate the research output structure."""
        required_fields = ["title", "summary", "key_points", "sources"]
        
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
    
    def _create_empty_result(self, query: str, message: str) -> Dict:
        """Create an empty result when research fails."""
        return {
            "title": f"Research Results: {query}",
            "summary": message,
            "key_points": ["No key points available due to search failure"],
            "sources": []
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if a URL is properly formatted."""
        try:
            url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+\.[a-zA-Z]{2,}'
            if not re.match(url_pattern, url):
                return False
            
            invalid_patterns = ['example.com', 'placeholder', 'no%20url']
            for pattern in invalid_patterns:
                if pattern in url.lower():
                    return False
            
            if len(url) < 15 or len(url) > 500:
                return False
            
            return True
            
        except Exception:
            return False


if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("Please set GOOGLE_API_KEY environment variable")
        exit(1)
    
    if not os.getenv("SERPAPI_API_KEY"):
        print("Please set SERPAPI_API_KEY environment variable")
        exit(1)

    try:
        agent = ResearchAgent()
        test_query = "latest advancements in artificial intelligence"
        result = agent.run_research(test_query)
        
        print("=== RESEARCH RESULTS ===")
        print(f"Title: {result['title']}")
        print(f"Summary: {result['summary']}")
        print("\nKey Points:")
        for i, point in enumerate(result['key_points'], 1):
            print(f"{i}. {point}")
        print("\nSources:")
        for i, source in enumerate(result['sources'], 1):
            print(f"{i}. {source['title']} ({source['url']})")
            
    except Exception as e:
        print(f"Error during testing: {e}")
