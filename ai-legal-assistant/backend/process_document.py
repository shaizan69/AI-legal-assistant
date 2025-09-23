#!/usr/bin/env python3
"""
Background document processing script
This script handles heavy processing like embeddings and AI summaries
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_document_background(document_id: int):
    """Process document with heavy ML operations"""
    try:
        from app.core.database import get_db
        from app.models.document import Document, DocumentChunk, DocumentAnalysis
        from app.core.utils import chunk_text
        from app.core.supabase_embeddings import embedding_service
        from app.core.llm import llm_service
        
        # Get database session
        db = next(get_db())
        
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        logger.info(f"Starting background processing for document {document_id}")
        
        # Chunk text for vector search
        chunks = chunk_text(document.extracted_text, chunk_size=1000, overlap=200)
        
        # Create document chunks
        chunk_objects = []
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk_content,
                word_count=len(chunk_content.split()),
                character_count=len(chunk_content)
            )
            chunk_objects.append(chunk)
            db.add(chunk)
        
        db.commit()
        logger.info(f"Created {len(chunk_objects)} chunks for document {document_id}")
        
        # Generate embeddings for chunks
        try:
            chunk_texts = [chunk.content for chunk in chunk_objects]
            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
            
            # Add vectors to vector database
            chunk_ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunk_objects))]
            chunk_metadata = [
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "title": document.title,
                    "document_type": document.document_type or "contract"
                }
                for i in range(len(chunk_objects))
            ]
            
            embedding_service.add_vectors(embeddings, chunk_ids, chunk_metadata)
            
            # Update chunk objects with embedding info
            for chunk in chunk_objects:
                chunk.has_embedding = True
                chunk.embedding_id = f"doc_{document_id}_chunk_{chunk.chunk_index}"
            
            logger.info(f"Generated embeddings for document {document_id}")
            
        except Exception as e:
            logger.warning(f"Failed to generate embeddings for document {document_id}: {e}")
        
        # Generate summary using LLM
        try:
            summary_result = await llm_service.summarize_document(
                document.extracted_text, 
                document.document_type or "contract"
            )
            
            # Save summary analysis
            summary_analysis = DocumentAnalysis(
                document_id=document_id,
                analysis_type="summary",
                summary=summary_result["summary"],
                structured_data=summary_result["structured"],
                confidence_score=0.8,
                model_used="groq-llama3-8b-8192"
            )
            db.add(summary_analysis)
            db.commit()
            
            logger.info(f"Generated summary for document {document_id}")
            
        except Exception as e:
            logger.warning(f"Failed to generate summary for document {document_id}: {e}")
        
        logger.info(f"Background processing completed for document {document_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for document {document_id}: {e}")
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Main function to run background processing"""
    if len(sys.argv) != 2:
        print("Usage: python process_document.py <document_id>")
        sys.exit(1)
    
    try:
        document_id = int(sys.argv[1])
        asyncio.run(process_document_background(document_id))
    except ValueError:
        print("Error: document_id must be an integer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running background processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
