# ESG Reporter - Multi-Agent AI Research System

A sophisticated multi-agent AI system built with LangGraph that orchestrates specialized agents to conduct comprehensive ESG (Environmental, Social, and Governance) research. The system combines web search, academic research, data analysis, and document synthesis to generate detailed ESG reports.

## 🌟 Features

- **Multi-Agent Architecture**: 6 specialized AI agents working collaboratively
- **Comprehensive Research**: Web search, academic papers, and document analysis
- **Azure Integration**: Powered by Azure OpenAI and Azure AI Search
- **Interactive Interface**: Beautiful Streamlit web application
- **Document Processing**: Automated PDF indexing with vector search
- **Real-time Visualization**: Watch agents work in real-time

## 🤖 AI Agents

1. **Lead Agent** - Orchestrates research and coordinates other agents
2. **Academic Research Agent** - Searches arXiv and academic databases
3. **Web Search Agent** - Conducts comprehensive web research using Brave Search
4. **Data Search Agent** - Performs vector search on indexed ESG documents
5. **Verification Agent** - Fact-checks and validates research findings
6. **Synthesis Agent** - Combines findings into comprehensive reports

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure OpenAI API access
- Azure AI Search service
- Brave Search API key (free)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ESGreporter.git
   cd ESGreporter
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and endpoints
   ```

5. **Set up Azure AI Search index**
   ```bash
   # Create the search index using the provided schema
   # See setup instructions below
   ```

6. **Index your ESG documents** (optional)
   ```bash
   python add_documents_to_index.py
   ```

7. **Launch the application**
   ```bash
   streamlit run streamlit_app.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=your_search_endpoint
AZURE_SEARCH_KEY=your_search_key

# Brave Search API
BRAVE_SEARCH_API_KEY=your_brave_api_key

# Azure OpenAI Configuration - Embeddings
AZURE_OPENAI_EMBEDDINGS_ENDPOINT=your_embeddings_endpoint
AZURE_OPENAI_EMBEDDINGS_API_KEY=your_embeddings_api_key
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME=text-embedding-3-large
```

### Azure AI Search Setup

1. **Create the search index** using Azure Portal, CLI, or REST API:
   ```bash
   # Using Azure CLI
   az search index create --service-name your-search-service --index-definition azure-index-schema.json
   ```

2. **Or use the provided schema** in `azure-index-schema.json` to create the index manually

## 📁 Project Structure

```
ESGreporter/
├── agents.py                 # AI agent definitions and logic
├── tools.py                  # Search tools and utilities
├── workflow.py              # LangGraph workflow orchestration
├── streamlit_app.py         # Web interface
├── add_documents_to_index.py # Document indexing script
├── azure-index-schema.json  # Azure AI Search index schema
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── README.md               # This file
└── blog_post.md           # Technical deep-dive blog post
```

## 🎯 Usage

1. **Launch the web interface**: `streamlit run streamlit_app.py`
2. **Enter your research query** in the sidebar
3. **Watch the agents work** in real-time through the cinematic interface
4. **Download results** as PDF reports
5. **Explore cached results** from previous research sessions

## 🔧 Advanced Features

### Document Indexing

The system can index your own ESG documents for enhanced research:

```bash
# Place PDF documents in your chosen directory
# Update the path in add_documents_to_index.py
python add_documents_to_index.py
```

### Custom Agent Configuration

Modify agent behaviors in `agents.py`:
- Adjust system prompts
- Add new search capabilities
- Customize response formats

### Workflow Customization

Enhance the agent orchestration in `workflow.py`:
- Add new agent types
- Modify execution flow
- Implement parallel processing

## 📊 Technical Architecture

- **Framework**: LangGraph for agent orchestration
- **LLM**: Azure OpenAI GPT-4
- **Vector Search**: Azure AI Search with text-embedding-3-large
- **Web Search**: Brave Search API
- **Academic Search**: arXiv API
- **Frontend**: Streamlit with custom CSS
- **Document Processing**: PyPDF2 with intelligent chunking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Powered by [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Search capabilities via [Brave Search API](https://brave.com/search/api/)
- Academic research through [arXiv API](https://arxiv.org/help/api)

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check the [blog post](blog_post.md) for technical deep-dive
- Review the code documentation

---

**Made with ❤️ for ESG research and sustainable investing**
