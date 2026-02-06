import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_agent import ResearchAgent


class TestResearchAgent:
    """Test cases for the ResearchAgent class."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_openai_key',
            'SERPAPI_API_KEY': 'test_serpapi_key'
        }):
            yield
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing."""
        mock_llm = Mock()
        mock_llm.run.return_value = "Mock LLM response"
        return mock_llm
    
    @pytest.fixture
    def mock_search(self):
        """Mock search tool for testing."""
        mock_search = Mock()
        mock_search.run.return_value = "Mock search results"
        return mock_search
    
    @pytest.fixture
    def research_agent(self, mock_env_vars):
        """Create a ResearchAgent instance for testing."""
        with patch('research_agent.ChatOpenAI') as mock_openai, \
             patch('research_agent.SerpAPIWrapper') as mock_serpapi:
            
            mock_openai.return_value = Mock()
            mock_serpapi.return_value = Mock()
            
            agent = ResearchAgent()
            return agent
    
    def test_initialization_success(self, mock_env_vars):
        """Test successful initialization of ResearchAgent."""
        with patch('research_agent.ChatOpenAI') as mock_openai, \
             patch('research_agent.SerpAPIWrapper') as mock_serpapi:
            
            mock_openai.return_value = Mock()
            mock_serpapi.return_value = Mock()
            
            agent = ResearchAgent()
            
            assert agent is not None
            assert hasattr(agent, 'llm')
            assert hasattr(agent, 'search')
            assert hasattr(agent, 'tools')
    
    def test_initialization_missing_api_keys(self):
        """Test initialization fails when API keys are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Either OPENAI_API_KEY or GOOGLE_API_KEY must be set"):
                ResearchAgent()
    
    def test_initialization_missing_serpapi_key(self):
        """Test initialization fails when SerpAPI key is missing."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}, clear=True):
            with pytest.raises(ValueError, match="SERPAPI_API_KEY not found"):
                ResearchAgent()
    
    def test_run_research_success(self, research_agent):
        """Test successful research execution."""
        # Mock the search and LLM chain
        research_agent.search.run.return_value = "Test search results"
        
        with patch('research_agent.LLMChain') as mock_chain:
            mock_chain_instance = Mock()
            mock_chain_instance.run.return_value = """
            TITLE: Test Research Title
            
            SUMMARY: This is a test summary of the research findings.
            
            KEY POINTS:
            - First key point about the research
            - Second key point with important information
            - Third key point summarizing findings
            
            SOURCES:
            [1] Test Source 1 (https://example1.com)
            [2] Test Source 2 (https://example2.com)
            """
            mock_chain.return_value = mock_chain_instance
            
            result = research_agent.run_research("test query")
            
            assert result is not None
            assert "title" in result
            assert "summary" in result
            assert "key_points" in result
            assert "sources" in result
            assert result["title"] == "Test Research Title"
            assert len(result["key_points"]) > 0
            assert len(result["sources"]) > 0
    
    def test_run_research_empty_query(self, research_agent):
        """Test research fails with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            research_agent.run_research("")
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            research_agent.run_research("   ")
    
    def test_run_research_no_search_results(self, research_agent):
        """Test research handles empty search results."""
        research_agent.search.run.return_value = ""
        
        result = research_agent.run_research("test query")
        
        assert result is not None
        assert "No search results found" in result["summary"]
        assert result["key_points"] == ["No key points available due to search failure"]
        assert result["sources"] == []
    
    def test_parse_research_note_valid_input(self, research_agent):
        """Test parsing of valid research note."""
        raw_text = """
        TITLE: Test Research Title
        
        SUMMARY: This is a comprehensive summary of the research findings.
        
        KEY POINTS:
        - First important point about the research
        - Second key finding with details
        - Third significant insight
        
        SOURCES:
        [1] Research Paper 1 (https://example1.com)
        [2] News Article 2 (https://example2.com)
        [3] Academic Source 3 (https://example3.com)
        """
        
        result = research_agent._parse_research_note(raw_text)
        
        assert result["title"] == "Test Research Title"
        assert "comprehensive summary" in result["summary"]
        assert len(result["key_points"]) == 3
        assert len(result["sources"]) == 3
        assert result["sources"][0]["title"] == "Research Paper 1"
        assert result["sources"][0]["url"] == "https://example1.com"
    
    def test_parse_research_note_malformed_input(self, research_agent):
        """Test parsing of malformed research note."""
        raw_text = "Invalid format without proper sections"
        
        result = research_agent._parse_research_note(raw_text)
        
        assert result["title"] == "Research Results"  # Default title
        assert result["summary"] == "No summary available"  # Default summary
        assert result["key_points"] == []
        assert result["sources"] == []
    
    def test_validate_research_output_valid(self, research_agent):
        """Test validation of valid research output."""
        valid_output = {
            "title": "Test Title",
            "summary": "Test Summary",
            "key_points": ["Point 1", "Point 2"],
            "sources": [{"title": "Source 1", "url": "http://example.com"}]
        }
        
        # Should not raise any exception
        research_agent._validate_research_output(valid_output)
    
    def test_validate_research_output_missing_fields(self, research_agent):
        """Test validation fails with missing fields."""
        invalid_output = {
            "title": "Test Title",
            "summary": "Test Summary"
            # Missing key_points and sources
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            research_agent._validate_research_output(invalid_output)
    
    def test_create_empty_result(self, research_agent):
        """Test creation of empty result."""
        query = "test query"
        message = "Test error message"
        
        result = research_agent._create_empty_result(query, message)
        
        assert result["title"] == f"Research Results: {query}"
        assert result["summary"] == message
        assert result["key_points"] == ["No key points available due to search failure"]
        assert result["sources"] == []
    
    def test_gemini_fallback(self, mock_env_vars):
        """Test fallback to Gemini when OpenAI fails."""
        with patch('research_agent.ChatOpenAI') as mock_openai, \
             patch('research_agent.ChatGoogleGenerativeAI') as mock_gemini, \
             patch('research_agent.SerpAPIWrapper') as mock_serpapi:
            
            # Mock OpenAI to fail
            mock_openai.side_effect = Exception("OpenAI API error")
            mock_gemini.return_value = Mock()
            mock_serpapi.return_value = Mock()
            
            agent = ResearchAgent()
            
            # Should have initialized Gemini instead
            mock_gemini.assert_called_once()
    
    @patch('research_agent.logging.getLogger')
    def test_logging_behavior(self, mock_logger, research_agent):
        """Test that appropriate logging occurs during research."""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        
        research_agent.search.run.return_value = "Test results"
        
        with patch('research_agent.LLMChain') as mock_chain:
            mock_chain_instance = Mock()
            mock_chain_instance.run.return_value = "Test LLM output"
            mock_chain.return_value = mock_chain_instance
            
            research_agent.run_research("test query")
            
            # Verify logging calls
            assert mock_logger_instance.info.called
            assert mock_logger_instance.error.called is False  # No errors in this test


class TestResearchAgentIntegration:
    """Integration tests for ResearchAgent."""
    
    @pytest.fixture
    def mock_environment(self):
        """Set up mock environment for integration tests."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_openai_key',
            'SERPAPI_API_KEY': 'test_serpapi_key'
        }):
            yield
    
    def test_full_research_pipeline(self, mock_environment):
        """Test the complete research pipeline."""
        with patch('research_agent.ChatOpenAI') as mock_openai, \
             patch('research_agent.SerpAPIWrapper') as mock_serpapi, \
             patch('research_agent.LLMChain') as mock_chain:
            
            # Mock all components
            mock_openai.return_value = Mock()
            mock_serpapi.return_value = Mock()
            mock_serpapi.return_value.run.return_value = "Comprehensive search results about AI"
            
            mock_chain_instance = Mock()
            mock_chain_instance.run.return_value = """
            TITLE: Artificial Intelligence Advancements
            
            SUMMARY: Recent developments in AI technology show significant progress in machine learning and neural networks.
            
            KEY POINTS:
            - AI models have achieved unprecedented accuracy in natural language processing
            - Neural network architectures continue to evolve rapidly
            - AI applications in healthcare are expanding significantly
            
            SOURCES:
            [1] AI Research Paper (https://ai-research.com)
            [2] Tech News Article (https://technews.com)
            """
            mock_chain.return_value = mock_chain_instance
            
            # Create agent and run research
            agent = ResearchAgent()
            result = agent.run_research("latest AI developments")
            
            # Verify the complete pipeline worked
            assert result is not None
            assert "Artificial Intelligence" in result["title"]
            assert "AI technology" in result["summary"]
            assert len(result["key_points"]) >= 3
            assert len(result["sources"]) >= 2
            
            # Verify all components were called
            mock_serpapi.return_value.run.assert_called_once_with("latest AI developments")
            mock_chain_instance.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
