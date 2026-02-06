import os
import logging
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from research_agent import ResearchAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    """Initialize SQLite database for storing research queries and results."""
    conn = sqlite3.connect('research_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'success',
            error_message TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_research_query(query, result=None, status='success', error_message=None):
    """Save research query and result to database."""
    try:
        conn = sqlite3.connect('research_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO research_queries (query, result, status, error_message)
            VALUES (?, ?, ?, ?)
        ''', (query, json.dumps(result) if result else None, status, error_message))
        conn.commit()
        conn.close()
        logger.info(f"Research query saved to database: {query}")
    except Exception as e:
        logger.error(f"Failed to save research query to database: {e}")

# Initialize ResearchAgent
try:
    research_agent = ResearchAgent()
    logger.info("ResearchAgent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ResearchAgent: {e}")
    research_agent = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    agent_status = "not_initialized"
    if research_agent is not None:
        agent_status = "initialized"
        try:
            # Test if we can access the LLM
            if hasattr(research_agent, 'llm') and research_agent.llm is not None:
                agent_status = "llm_ready"
            # Test if we can access the search
            if hasattr(research_agent, 'search') and research_agent.search is not None:
                agent_status = "search_ready"
        except Exception as e:
            agent_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": research_agent is not None,
        "agent_status": agent_status,
        "environment_vars": {
            "google_api_key_set": bool(os.getenv("GOOGLE_API_KEY")),
            "serpapi_key_set": bool(os.getenv("SERPAPI_API_KEY"))
        }
    }), 200

@app.route('/test-agent', methods=['GET'])
def test_agent():
    """Test endpoint to verify research agent components."""
    if not research_agent:
        return jsonify({
            "error": "Research agent not initialized",
            "details": "Check backend logs for initialization errors"
        }), 500
    
    try:
        # Test LLM initialization
        llm_status = "ok" if hasattr(research_agent, 'llm') and research_agent.llm else "missing"
        
        # Test search initialization  
        search_status = "ok" if hasattr(research_agent, 'search') and research_agent.search else "missing"
        
        # Test prompt template
        prompt_status = "ok" if hasattr(research_agent, 'research_prompt_template') and research_agent.research_prompt_template else "missing"
        
        return jsonify({
            "status": "agent_components_checked",
            "llm_status": llm_status,
            "search_status": search_status,
            "prompt_status": prompt_status,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": "Failed to test agent components",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/test-serpapi', methods=['GET'])
def test_serpapi():
    """Test SerpAPI connection without making a full search."""
    if not research_agent:
        return jsonify({
            "error": "Research agent not initialized"
        }), 500
    
    try:
        # Test with a simple search
        test_query = "test"
        logger.info(f"Testing SerpAPI with query: {test_query}")
        result = research_agent.search.run(test_query)
        
        return jsonify({
            "status": "serpapi_working",
            "test_query": test_query,
            "result_length": len(str(result)) if result else 0,
            "result_preview": str(result)[:200] if result else "No result"
        }), 200
        
    except Exception as e:
        import traceback
        logger.error(f"SerpAPI test failed: {e}")
        return jsonify({
            "error": "SerpAPI test failed",
            "details": str(e),
            "traceback": traceback.format_exc(),
            "suggestion": "Check your SERPAPI_API_KEY in Render environment variables"
        }), 500

@app.route('/debug-research', methods=['GET'])
def debug_research():
    """Debug endpoint to see raw LLM output for source parsing issues."""
    query = request.args.get('query', 'test query')
    
    if not research_agent:
        return jsonify({"error": "Research agent not initialized"}), 500
    
    try:
        # Perform search only
        logger.info(f"Debug: Performing search for: {query}")
        search_results = research_agent.search.run(query)
        
        # Process with LLM
        logger.info("Debug: Processing with LLM...")
        chain = LLMChain(llm=research_agent.llm, prompt=research_agent.research_prompt_template)
        raw_output = chain.run(query=query, search_results=search_results)
        
        # Extract text content
        if hasattr(raw_output, 'content'):
            raw_output = raw_output.content
        elif isinstance(raw_output, dict) and 'text' in raw_output:
            raw_output = raw_output['text']
        else:
            raw_output = str(raw_output)
        
        return jsonify({
            "query": query,
            "search_results_length": len(str(search_results)),
            "search_results_preview": str(search_results)[:500],
            "raw_llm_output": raw_output,
            "llm_output_length": len(raw_output)
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": "Debug research failed",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/debug-urls', methods=['GET'])
def debug_urls():
    """Debug endpoint to see what URLs are found in search results."""
    query = request.args.get('query', 'test query')
    
    if not research_agent:
        return jsonify({"error": "Research agent not initialized"}), 500
    
    try:
        # Perform search only
        logger.info(f"Debug URLs: Performing search for: {query}")
        search_results = research_agent.search.run(query)
        
        # Extract URLs from search results
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[^\s<>"{}|\\^`\[\]]*[a-zA-Z0-9])?'
        found_urls = re.findall(url_pattern, str(search_results))
        
        # Remove duplicates
        unique_urls = []
        seen = set()
        for url in found_urls:
            if url not in seen and len(url) > 10:
                unique_urls.append(url)
                seen.add(url)
        
        # Validate URLs
        valid_urls = []
        for url in unique_urls:
            if research_agent._is_valid_url(url):
                valid_urls.append(url)
        
        return jsonify({
            "query": query,
            "search_results_length": len(str(search_results)),
            "search_results_preview": str(search_results)[:1000],
            "all_urls_found": found_urls,
            "unique_urls": unique_urls,
            "valid_urls": valid_urls,
            "total_urls_found": len(found_urls),
            "unique_count": len(unique_urls),
            "valid_count": len(valid_urls)
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": "Debug URLs failed",
            "details": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/research', methods=['GET'])
def research():
    """
    Research endpoint that takes a query parameter and returns structured research notes.
    
    Query Parameters:
    - query (required): The research query string
    
    Returns:
    - JSON object with structured research note containing title, summary, key_points, and sources
    """
    query = request.args.get('query')
    
    if not query:
        logger.warning("Research endpoint called without a query parameter")
        return jsonify({
            "error": "Query parameter is required.",
            "usage": "GET /research?query=your_research_query"
        }), 400

    if not query.strip():
        logger.warning("Research endpoint called with empty query")
        return jsonify({
            "error": "Query cannot be empty."
        }), 400

    logger.info(f"Received research query: {query}")

    try:
        if not research_agent:
            error_msg = "Research agent not initialized. Check backend logs for details."
            logger.error(error_msg)
            save_research_query(query, status='error', error_message=error_msg)
            return jsonify({"error": error_msg}), 500

        # Perform research
        result = research_agent.run_research(query)
        
        # Save successful result to database
        save_research_query(query, result)
        
        logger.info(f"Successfully processed query: {query}")
        return jsonify({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }), 200

    except Exception as e:
        import traceback
        error_msg = f"Failed to perform research: {str(e)}"
        full_traceback = traceback.format_exc()
        logger.error(f"Error processing research query '{query}': {e}")
        logger.error(f"Full traceback: {full_traceback}")
        save_research_query(query, status='error', error_message=error_msg)
        return jsonify({
            "error": "Failed to perform research.",
            "details": str(e),
            "traceback": full_traceback,
            "query": query
        }), 500

@app.route('/history', methods=['GET'])
def get_research_history():
    """
    Get research history from database.
    
    Query Parameters:
    - limit (optional): Number of recent queries to return (default: 10)
    - offset (optional): Number of queries to skip (default: 0)
    
    Returns:
    - JSON array of recent research queries and results
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = sqlite3.connect('research_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, query, result, created_at, status, error_message
            FROM research_queries
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "query": row[1],
                "result": json.loads(row[2]) if row[2] else None,
                "created_at": row[3],
                "status": row[4],
                "error_message": row[5]
            })
        
        return jsonify({
            "history": history,
            "count": len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve research history: {e}")
        return jsonify({
            "error": "Failed to retrieve research history.",
            "details": str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get research statistics."""
    try:
        conn = sqlite3.connect('research_history.db')
        cursor = conn.cursor()
        
        # Total queries
        cursor.execute('SELECT COUNT(*) FROM research_queries')
        total_queries = cursor.fetchone()[0]
        
        # Successful queries
        cursor.execute('SELECT COUNT(*) FROM research_queries WHERE status = "success"')
        successful_queries = cursor.fetchone()[0]
        
        # Failed queries
        cursor.execute('SELECT COUNT(*) FROM research_queries WHERE status = "error"')
        failed_queries = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM research_queries 
            WHERE created_at >= datetime('now', '-1 day')
        ''')
        recent_queries = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
            "recent_queries_24h": recent_queries
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {e}")
        return jsonify({
            "error": "Failed to retrieve statistics.",
            "details": str(e)
        }), 500

@app.route('/')
def root():
    """Root endpoint - should not be reached when nginx is working properly."""
    return jsonify({
        "message": "Backend API is running. Frontend should be served by nginx.",
        "available_endpoints": [
            "GET /health",
            "GET /research?query=<your_query>",
            "GET /history?limit=<number>&offset=<number>",
            "GET /stats"
        ]
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found.",
        "available_endpoints": [
            "GET /health",
            "GET /research?query=<your_query>",
            "GET /history?limit=<number>&offset=<number>",
            "GET /stats"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error.",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start Flask app - bind to all interfaces for local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
