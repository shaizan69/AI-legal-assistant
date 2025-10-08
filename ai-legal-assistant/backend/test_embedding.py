#!/usr/bin/env python3
"""Test script for InLegalBERT embedding service"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_embedding_service():
    """Test the embedding service"""
    try:
        print("Testing embedding service...")
        
        # Test sentence-transformers import
        try:
            from sentence_transformers import SentenceTransformer
            print("✓ sentence-transformers imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import sentence-transformers: {e}")
            return False
        
        # Test InLegalBERT model loading
        try:
            print("Loading InLegalBERT model...")
            model = SentenceTransformer('law-ai/InLegalBERT')
            print("✓ InLegalBERT model loaded successfully")
            print(f"✓ Model dimension: {model.get_sentence_embedding_dimension()}")
        except Exception as e:
            print(f"✗ Failed to load InLegalBERT: {e}")
            return False
        
        # Test embedding generation
        try:
            test_text = "This is a test legal document about payment schedules."
            embedding = model.encode(test_text)
            print(f"✓ Generated embedding with dimension: {len(embedding)}")
            print(f"✓ First 5 values: {embedding[:5]}")
        except Exception as e:
            print(f"✗ Failed to generate embedding: {e}")
            return False
        
        # Test our embedding service
        try:
            from app.core.supabase_embeddings import get_embedding_service
            service = get_embedding_service()
            print("✓ Embedding service initialized")
            print(f"✓ Service dimension: {service.dimension}")
            print(f"✓ Model available: {service.embedding_model is not None}")
            
            if service.embedding_model:
                test_embedding = service.generate_embedding(test_text)
                print(f"✓ Service generated embedding: {len(test_embedding)} dimensions")
            else:
                print("✗ Service model is None")
                return False
                
        except Exception as e:
            print(f"✗ Failed to initialize embedding service: {e}")
            return False
        
        print("\n🎉 All tests passed! InLegalBERT is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_embedding_service()
    sys.exit(0 if success else 1)
