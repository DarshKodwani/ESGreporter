#!/usr/bin/env python3
"""
Simplified script to index ESG PDF documents in Azure AI Search.
Only handles PDF files from the ESG_docs folder.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import gc
from dotenv import load_dotenv
import tiktoken

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import PyPDF2

load_dotenv()

def extract_pdf_content(pdf_path: Path) -> str:
    """Extract text from all pages of a PDF file"""
    print(f"📄 Extracting PDF content from: {pdf_path.name}")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            if len(pdf_reader.pages) == 0:
                print("⚠️ PDF has no pages")
                return ""
            
            pages_to_process = len(pdf_reader.pages)
            print(f"📊 Processing {pages_to_process} pages...")
            
            text = ""
            for page_num in range(pages_to_process):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Progress indicator every 10 pages
                    if (page_num + 1) % 10 == 0:
                        print(f"   📄 Processed {page_num + 1}/{pages_to_process} pages")
                        gc.collect()  # Memory cleanup
                        
                except Exception as e:
                    print(f"⚠️ Warning: Could not extract page {page_num + 1}: {e}")
            
            print(f"✅ Extracted {len(text)} characters from {pages_to_process} pages")
            return text.strip()
            
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return ""

def chunk_text(text: str, max_tokens: int = 800, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks for better embedding performance"""
    print(f"🔧 Chunking text into {max_tokens}-token pieces with {overlap}-token overlap...")
    
    try:
        tokenizer = tiktoken.encoding_for_model("gpt-4")
        tokens = tokenizer.encode(text)
        
        print(f"📊 Total tokens to process: {len(tokens)}")
        
        if len(tokens) <= max_tokens:
            print(f"✅ Text fits in single chunk ({len(tokens)} tokens)")
            return [text]
        
        chunks = []
        start = 0
        chunk_num = 0
        max_chunks = 1000  # Reasonable limit for PDF documents
        
        while start < len(tokens) and chunk_num < max_chunks:
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            chunk_num += 1
            if chunk_num % 25 == 0:  # Progress every 25 chunks
                print(f"   🔧 Created {chunk_num} chunks... ({start}/{len(tokens)} tokens)")
                gc.collect()
            
            # Move start with overlap
            start = end - overlap
            if start >= len(tokens):
                break
        
        if chunk_num >= max_chunks:
            print(f"⚠️ WARNING: Hit chunk limit of {max_chunks}. Document truncated.")
        
        print(f"✅ Created {len(chunks)} chunks total")
        return chunks
        
    except Exception as e:
        print(f"❌ Error chunking text: {e}")
        return [text]  # Return original text as fallback

def get_embeddings(text: str, openai_client, model: str) -> List[float]:
    """Generate embeddings for text using Azure OpenAI"""
    try:
        print(f"🔄 Generating embeddings for {len(text)} characters...")
        response = openai_client.embeddings.create(
            input=text,
            model=model
        )
        print("✅ Embeddings generated successfully")
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        return []

def get_esg_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract ESG-specific metadata from filename patterns"""
    filename = file_path.name.lower()
    
    # Default metadata
    metadata = {
        'institution': 'Unknown',
        'document_type': 'ESG Document',
        'year': 2024,
        'tags': 'esg,sustainability'
    }
    
    # ESG Frameworks
    if 'gri' in filename:
        metadata['institution'] = 'Global Reporting Initiative'
        metadata['document_type'] = 'GRI Standards'
        metadata['tags'] = 'gri,standards,sustainability,reporting'
    elif 'sasb' in filename:
        metadata['institution'] = 'Sustainability Accounting Standards Board'
        metadata['document_type'] = 'SASB Standards'
        metadata['tags'] = 'sasb,standards,sustainability,accounting'
    elif 'tcfd' in filename:
        metadata['institution'] = 'Task Force on Climate-related Financial Disclosures'
        metadata['document_type'] = 'TCFD Framework'
        metadata['tags'] = 'tcfd,climate,risk,disclosure'
    
    # Corporate ESG Reports
    elif any(company in filename for company in ['microsoft', 'apple', 'google', 'amazon', 'tesla', 'nvidia', 'meta']):
        for company in ['microsoft', 'apple', 'google', 'amazon', 'tesla', 'nvidia', 'meta']:
            if company in filename:
                metadata['institution'] = company.title()
                break
        
        if 'sustainability' in filename or 'esg' in filename:
            metadata['document_type'] = 'Corporate ESG Report'
            metadata['tags'] = 'corporate,esg,sustainability,report'
        elif 'climate' in filename:
            metadata['document_type'] = 'Climate Report'
            metadata['tags'] = 'climate,corporate,environmental'
    
    # Topic-based categorization
    elif any(term in filename for term in ['climate', 'carbon', 'environment', 'green']):
        metadata['document_type'] = 'Environmental Report'
        metadata['tags'] = 'environmental,climate,carbon,green'
    elif any(term in filename for term in ['diversity', 'social', 'inclusion', 'community']):
        metadata['document_type'] = 'Social Impact Report'
        metadata['tags'] = 'social,diversity,inclusion,community'
    elif any(term in filename for term in ['governance', 'board', 'ethics', 'compliance']):
        metadata['document_type'] = 'Governance Report'
        metadata['tags'] = 'governance,ethics,compliance,board'
    
    # Extract year from filename
    import re
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        metadata['year'] = int(year_match.group())
    
    return metadata

def main():
    print("🚀 Indexing ESG PDF Documents in Azure AI Search")
    print("=" * 60)
    
    # Configuration
    ESG_DATA_DIR = Path("/Users/darshkodwani/Downloads/ESG_docs")
    INDEX_NAME = "esg-documents-index"
    
    # Check environment variables
    required_vars = [
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_KEY', 
        'AZURE_OPENAI_EMBEDDINGS_ENDPOINT',
        'AZURE_OPENAI_EMBEDDINGS_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Make sure these are set in your .env file")
        return
    
    print("🔧 Initializing Azure clients...")
    
    # Initialize clients
    search_client = SearchClient(
        endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_KEY'))
    )
    
    openai_client = AzureOpenAI(
        azure_endpoint=os.getenv('AZURE_OPENAI_EMBEDDINGS_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_EMBEDDINGS_API_KEY'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
    )
    
    embedding_model = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME', 'text-embedding-3-large')
    
    # Check if directory exists
    if not ESG_DATA_DIR.exists():
        print(f"❌ Directory not found: {ESG_DATA_DIR}")
        print(f"💡 Create the directory and add your PDF files: mkdir {ESG_DATA_DIR}")
        return
    
    # Find all PDF files
    pdf_files = list(ESG_DATA_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {ESG_DATA_DIR}")
        return
    
    print(f"📂 Found {len(pdf_files)} PDF files to process:")
    for i, file_path in enumerate(pdf_files, 1):
        print(f"   {i:2d}. {file_path.name}")
    
    print(f"\n🔄 Starting PDF processing...")
    
    all_documents = []
    processed_files = 0
    
    for file_index, file_path in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"📄 Processing {file_index}/{len(pdf_files)}: {file_path.name}")
        print(f"{'='*60}")
        
        try:
            # Extract text from PDF
            text = extract_pdf_content(file_path)
            if not text:
                print(f"⚠️ Skipping {file_path.name} - no text extracted")
                continue
            
            print(f"📝 Total text length: {len(text)} characters")
            
            # Get document metadata
            metadata = get_esg_metadata(file_path)
            print(f"🏷️ Classified as: {metadata['document_type']} from {metadata['institution']}")
            
            # Chunk the text
            chunks = chunk_text(text, max_tokens=800, overlap=150)
            print(f"📦 Created {len(chunks)} chunks for processing")
            
            # Process each chunk
            file_documents = []
            for i, chunk in enumerate(chunks):
                print(f"🔄 Processing chunk {i+1}/{len(chunks)}...")
                
                # Generate unique ID
                chunk_suffix = f"_chunk{i}" if len(chunks) > 1 else "_single"
                doc_id = hashlib.md5(f"{file_path.name}{chunk_suffix}".encode()).hexdigest()
                
                # Generate embeddings
                embeddings = get_embeddings(chunk, openai_client, embedding_model)
                if not embeddings:
                    print(f"⚠️ Skipping chunk {i+1} - no embeddings generated")
                    continue
                
                # Create document for index
                if len(chunks) > 1:
                    title_suffix = f" (Part {i+1}/{len(chunks)})"
                    summary = f"Part {i+1} of {len(chunks)} from {file_path.name}"
                else:
                    title_suffix = ""
                    summary = f"Complete content from {file_path.name}"
                
                document = {
                    'id': doc_id,
                    'title': f"{file_path.name}{title_suffix}",
                    'content': chunk,
                    'summary': summary,
                    'document_type': metadata['document_type'],
                    'institution': metadata['institution'], 
                    'year': metadata['year'],
                    'file_format': 'PDF',
                    'tags': metadata['tags'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'created_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'relevance_score': len(chunk.split()) / 1000.0,
                    'content_vector': embeddings
                }
                
                file_documents.append(document)
                print(f"✅ Created document for chunk {i+1}")
                
                # Memory cleanup every few chunks
                if (i + 1) % 5 == 0:
                    gc.collect()
            
            all_documents.extend(file_documents)
            processed_files += 1
            
            print(f"✅ Completed {file_path.name}: {len(file_documents)} chunks ready for upload")
            print(f"📊 Progress: {processed_files}/{len(pdf_files)} files processed")
            
            # Memory cleanup after each file
            gc.collect()
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            continue
    
    # Upload all documents in batches
    if all_documents:
        print(f"\n{'='*60}")
        print(f"📤 UPLOADING {len(all_documents)} DOCUMENT CHUNKS TO INDEX")
        print(f"{'='*60}")
        
        batch_size = 5  # Conservative batch size for PDFs
        total_uploaded = 0
        
        for i in range(0, len(all_documents), batch_size):
            batch = all_documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(all_documents) + batch_size - 1) // batch_size
            
            print(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            try:
                result = search_client.upload_documents(documents=batch)
                
                success_count = sum(1 for r in result if r.succeeded)
                error_count = len(batch) - success_count
                total_uploaded += success_count
                
                if error_count > 0:
                    print(f"⚠️ Batch {batch_num}: {success_count} succeeded, {error_count} failed")
                    for r in result:
                        if not r.succeeded:
                            print(f"   ❌ Error: {r.error_message}")
                else:
                    print(f"✅ Batch {batch_num}: All {success_count} chunks uploaded successfully")
                    
                gc.collect()  # Memory cleanup after each batch
                    
            except Exception as e:
                print(f"❌ Error uploading batch {batch_num}: {e}")
        
        print(f"\n🎉 UPLOAD COMPLETED!")
        print(f"📊 Final Summary:")
        print(f"   📄 PDF files processed: {processed_files}/{len(pdf_files)}")
        print(f"   📚 Total chunks uploaded: {total_uploaded}/{len(all_documents)}")
        print(f"   🏦 Index: {INDEX_NAME}")
        print(f"   🔍 Ready for ESG research queries!")
        
        if total_uploaded < len(all_documents):
            failed_count = len(all_documents) - total_uploaded
            print(f"   ⚠️ {failed_count} chunks failed to upload - check logs above")
    else:
        print("❌ No documents to upload - all PDFs failed processing")
    
    # Final cleanup
    gc.collect()
    print("\n🎉 ESG PDF indexing completed!")
    print("💡 You can now run your multi-agent research queries!")

if __name__ == "__main__":
    main()
