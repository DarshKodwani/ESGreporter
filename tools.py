import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

ARXIV_API_URL = "http://export.arxiv.org/api/query"

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = "esg-documents-index"

def brave_web_search(query: str, count: int = 10) -> List[Dict]:
    """
    Perform a web search using Brave Search API.
    
    Args:
        query (str): The search query
        count (int): Number of results to return (max 20)
        
    Returns:
        List[Dict]: List of search results with title, url, snippet
    """
    if not BRAVE_API_KEY:
        raise ValueError("BRAVE_SEARCH_API_KEY not found in environment variables")
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    
    params = {
        "q": query,
        "count": min(count, 20),  # Brave API max is 20
        "search_lang": "en",
        "country": "US",
        "safesearch": "moderate",
        "freshness": "pd",  # Past day for recent results
    }
    
    try:
        response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # Extract web results
        web_results = data.get("web", {}).get("results", [])
        
        for result in web_results:
            formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("description", ""),
                "published": result.get("age", ""),
            }
            results.append(formatted_result)
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error performing Brave search: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in Brave search: {e}")
        return []

def brave_news_search(query: str, count: int = 10) -> List[Dict]:
    """
    Perform a news search using Brave Search API.
    
    Args:
        query (str): The search query
        count (int): Number of results to return
        
    Returns:
        List[Dict]: List of news results with title, url, snippet, date
    """
    if not BRAVE_API_KEY:
        raise ValueError("BRAVE_SEARCH_API_KEY not found in environment variables")
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    
    params = {
        "q": query,
        "count": min(count, 20),
        "search_lang": "en",
        "country": "US",
        "safesearch": "moderate",
        "freshness": "pw",  # Past week for recent news
    }
    
    try:
        response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # Extract news results (often in web results but can filter by recent dates)
        web_results = data.get("web", {}).get("results", [])
        
        for result in web_results:
            # Filter for news-like sources
            url = result.get("url", "").lower()
            if any(news_domain in url for news_domain in ["news", "reuters", "bloomberg", "techcrunch", "wired", "bbc", "cnn"]):
                formatted_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("description", ""),
                    "published": result.get("age", ""),
                    "source": result.get("url", "").split("//")[1].split("/")[0] if "//" in result.get("url", "") else ""
                }
                results.append(formatted_result)
        
        return results[:count]
        
    except requests.exceptions.RequestException as e:
        print(f"Error performing Brave news search: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in Brave news search: {e}")
        return []

def arxiv_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search arXiv for academic papers.
    
    Args:
        query (str): Search query (can include field prefixes like 'ti:' for title, 'au:' for author)
        max_results (int): Maximum number of results to return
        
    Returns:
        List[Dict]: List of paper results with title, authors, abstract, url, published date
    """
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'relevance',
        'sortOrder': 'descending'
    }
    
    try:
        response = requests.get(ARXIV_API_URL, params=params)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Define namespaces
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        results = []
        entries = root.findall('atom:entry', namespaces)
        
        for entry in entries:
            # Extract paper information
            title = entry.find('atom:title', namespaces)
            title_text = title.text.strip().replace('\n', ' ') if title is not None else "No title"
            
            # Extract authors
            authors = []
            author_elements = entry.findall('atom:author', namespaces)
            for author in author_elements:
                name = author.find('atom:name', namespaces)
                if name is not None:
                    authors.append(name.text)
            
            # Extract abstract
            summary = entry.find('atom:summary', namespaces)
            abstract = summary.text.strip().replace('\n', ' ') if summary is not None else "No abstract"
            
            # Extract URL
            id_element = entry.find('atom:id', namespaces)
            paper_url = id_element.text if id_element is not None else ""
            
            # Extract published date
            published = entry.find('atom:published', namespaces)
            published_date = published.text[:10] if published is not None else ""  # Extract just the date part
            
            # Extract categories
            categories = []
            category_elements = entry.findall('atom:category', namespaces)
            for cat in category_elements:
                term = cat.get('term')
                if term:
                    categories.append(term)
            
            paper_info = {
                'title': title_text,
                'authors': authors,
                'abstract': abstract,
                'url': paper_url,
                'published': published_date,
                'categories': categories,
                'authors_string': ', '.join(authors) if authors else "Unknown authors"
            }
            
            results.append(paper_info)
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error performing arXiv search: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error parsing arXiv XML response: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in arXiv search: {e}")
        return []

def azure_vector_search(query: str, top_k: int = 5, use_hybrid: bool = True) -> List[Dict]:
    """
    Perform vector search against Azure AI Search index containing financial documents.
    
    Args:
        query (str): Search query
        top_k (int): Number of top results to return
        use_hybrid (bool): Whether to use hybrid search (vector + text)
        
    Returns:
        List[Dict]: List of search results with content, metadata, and scores
    """
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_KEY:
        print("⚠️ Azure Search credentials not configured")
        return []
    
    try:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY)
        )
        
        # Configure search parameters
        search_params = {
            "search_text": query if use_hybrid else None,
            "vector_queries": [
                {
                    "vector": None,  # This would need embedding generation
                    "k_nearest_neighbors": top_k,
                    "fields": "content_vector"
                }
            ] if not use_hybrid else [],
            "select": ["id", "title", "content", "institution", "year", "document_type", "file_path"],
            "top": top_k,
            "search_mode": "all" if use_hybrid else "any"
        }
        
        # For now, use text-only search since we'd need to generate embeddings for vector search
        # This can be enhanced later with proper embedding generation
        if use_hybrid:
            results = search_client.search(
                search_text=query,
                select=["id", "title", "content", "institution", "year", "document_type", "file_path"],
                top=top_k,
                search_mode="all"
            )
        else:
            # Simple text search fallback
            results = search_client.search(
                search_text=query,
                select=["id", "title", "content", "institution", "year", "document_type", "file_path"],
                top=top_k
            )
        
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get("id", ""),
                "title": result.get("title", "Unknown Document"),
                "content": result.get("content", "")[:1000],  # Truncate for readability
                "institution": result.get("institution", "Unknown"),
                "year": result.get("year", "Unknown"),
                "document_type": result.get("document_type", "Unknown"),
                "file_path": result.get("file_path", ""),
                "search_score": getattr(result, '@search.score', 0.0)
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
        
    except Exception as e:
        print(f"❌ Azure vector search error: {e}")
        return []

def format_search_results(results: List[Dict], result_type: str = "web") -> str:
    """
    Format search results into a readable string for LLM consumption.
    
    Args:
        results (List[Dict]): Search results from Brave API
        result_type (str): Type of results ("web" or "news")
        
    Returns:
        str: Formatted search results
    """
    if not results:
        return f"No {result_type} search results found."
    
    formatted = f"\n=== {result_type.upper()} SEARCH RESULTS ===\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. **{result.get('title', 'No title')}**\n"
        formatted += f"   URL: {result.get('url', 'No URL')}\n"
        formatted += f"   Summary: {result.get('snippet', 'No description')}\n"
        
        if result.get('published'):
            formatted += f"   Published: {result.get('published')}\n"
        if result.get('source'):
            formatted += f"   Source: {result.get('source')}\n"
            
        formatted += "\n"
    
    return formatted

def format_arxiv_results(results: List[Dict]) -> str:
    """
    Format arXiv search results into a readable string for LLM consumption.
    
    Args:
        results (List[Dict]): arXiv search results
        
    Returns:
        str: Formatted academic paper results
    """
    if not results:
        return "No academic papers found on arXiv."
    
    formatted = "\n=== ARXIV ACADEMIC PAPERS ===\n\n"
    
    for i, paper in enumerate(results, 1):
        formatted += f"{i}. **{paper.get('title', 'No title')}**\n"
        formatted += f"   Authors: {paper.get('authors_string', 'Unknown authors')}\n"
        formatted += f"   Published: {paper.get('published', 'Unknown date')}\n"
        formatted += f"   Categories: {', '.join(paper.get('categories', []))}\n"
        formatted += f"   URL: {paper.get('url', 'No URL')}\n"
        formatted += f"   Abstract: {paper.get('abstract', 'No abstract')[:500]}{'...' if len(paper.get('abstract', '')) > 500 else ''}\n"
        formatted += "\n"
    
    return formatted

def format_azure_search_results(results: List[Dict]) -> str:
    """
    Format Azure AI Search results into a readable string for LLM consumption.
    
    Args:
        results (List[Dict]): Azure Search results
        
    Returns:
        str: Formatted search results
    """
    if not results:
        return "No relevant documents found in the ESG documents index."
    
    formatted = "\n=== ESG DOCUMENT SEARCH RESULTS ===\n\n"
    formatted += f"Found {len(results)} relevant documents from the indexed ESG document collection:\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. **{result.get('title', 'Unknown Document')}**\n"
        formatted += f"   Institution: {result.get('institution', 'Unknown')}\n"
        formatted += f"   Year: {result.get('year', 'Unknown')}\n"
        formatted += f"   Document Type: {result.get('document_type', 'Unknown')}\n"
        formatted += f"   Relevance Score: {result.get('search_score', 0.0):.3f}\n"
        formatted += f"   Content Preview: {result.get('content', 'No content')[:500]}{'...' if len(result.get('content', '')) > 500 else ''}\n"
        formatted += f"   Source: {result.get('file_path', 'Unknown file')}\n"
        formatted += "\n"
    
    return formatted