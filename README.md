# CerebroGPT

An intelligent AI-powered research assistant that combines web search capabilities with advanced language models to generate comprehensive, structured research notes with citations.

## 🚀 Features

- **Web Search Integration**: Uses SerpAPI to search the web for current information
- **AI-Powered Analysis**: Leverages GPT-4 or Google Gemini for intelligent content processing
- **Structured Output**: Generates organized research notes with:
  - Clear titles and summaries
  - Key points and insights
  - Properly cited sources with URLs
- **Modern Web Interface**: Clean, responsive Angular frontend
- **Research History**: Track and revisit previous research queries
- **Export Capabilities**: Download research results as text files
- **Real-time Statistics**: Monitor usage and success rates
- **Docker Deployment**: Easy containerized deployment



## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cerebrogpt
```

### 2. Set Up Environment Variables
```bash
cp env.example .env
```

Edit `.env` file and add your API keys:
```env
# Choose one: OpenAI GPT-4 (recommended) or Google Gemini
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Required for web search functionality
SERPAPI_API_KEY=your_serpapi_key_here
```

### 3. Build and Run with Docker

#### Option 1: Use the convenience script
```bash
./run-local.sh
```

#### Option 2: Manual Docker Compose
```bash
docker-compose up --build -d
```

### 4. Access the Application
- **Frontend**: http://localhost
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost/health

## 📖 Usage

### Making Research Queries

1. **Open CerebroGPT** in your browser at `http://localhost`
2. **Enter your research query** in the search bar (e.g., "latest AI breakthroughs 2024")
3. **Click "Launch Research"** or press Enter
4. **Wait for processing** - CerebroGPT will search the web and analyze results
5. **Review your research** - Get structured notes with:
   - Executive summary
   - Key insights and points
   - Properly cited sources

### Features

- **Research History**: View and reload previous research queries
- **Export Options**: Copy to clipboard or download as text file
- **Real-time Stats**: Monitor your research activity
- **Error Handling**: Clear error messages for troubleshooting

## 🔧 API Endpoints

### Research Endpoint
```http
GET /research?query=your_research_query
```

**Response:**
```json
{
  "title": "Research Title",
  "summary": "Executive summary...",
  "key_points": ["Point 1", "Point 2", "..."],
  "sources": [
    {
      "title": "Source Title",
      "url": "https://example.com"
    }
  ]
}
```

### Health Check
```http
GET /health
```

### Research History
```http
GET /history
```

### Statistics
```http
GET /stats
```



## 🚀 Deployment

### Production Deployment
1. **Set up environment variables** for production
2. **Configure domain and SSL** certificates
3. **Set up monitoring** and logging
4. **Deploy with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Variables
- `OPENAI_API_KEY` or `GOOGLE_API_KEY`: AI model access
- `SERPAPI_API_KEY`: Web search functionality
- `FLASK_ENV`: Set to `production` for production deployment

## 🔧 Configuration

### Backend Configuration
- **Database**: SQLite (can be changed to PostgreSQL/MySQL)
- **Caching**: In-memory caching for research results
- **Rate Limiting**: Configurable rate limits for API endpoints

### Frontend Configuration
- **API Endpoint**: Configurable backend URL
- **Theme**: Dark theme with futuristic design
- **Responsive**: Mobile-friendly interface







## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




**CerebroGPT** - Where AI meets research intelligence! 🧠🤖
