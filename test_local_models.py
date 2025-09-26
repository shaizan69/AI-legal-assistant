#!/usr/bin/env python3
"""
Test script to verify that Hugging Face models are loaded from local paths
"""

import os
import sys

# Set environment variables
os.environ['HF_HOME'] = 'D:\\Hugging Face'
os.environ['TRANSFORMERS_CACHE'] = 'D:\\Hugging Face\\huggingface'
os.environ['HF_HUB_CACHE'] = 'D:\\Hugging Face\\huggingface'
os.environ['HF_DATASETS_CACHE'] = 'D:\\Hugging Face\\datasets'
os.environ['TORCH_HOME'] = 'D:\\Hugging Face\\torch'

def test_model_paths():
    """Test if model paths exist and are accessible"""
    print("=== Testing Hugging Face Model Paths ===\n")
    
    # Test e5-large-v2 model
    e5_path = os.path.join(os.environ['TORCH_HOME'], 'sentence_transformers', 'intfloat_e5-large-v2')
    print(f"E5 model path: {e5_path}")
    print(f"Exists: {os.path.exists(e5_path)}")
    if os.path.exists(e5_path):
        print(f"Contents: {os.listdir(e5_path)}")
    print()
    
    # Test CrossEncoder model
    cross_encoder_path = os.path.join(os.environ['HF_HOME'], 'huggingface', 'hub', 'models--cross-encoder--ms-marco-MiniLM-L-6-v2')
    print(f"CrossEncoder model path: {cross_encoder_path}")
    print(f"Exists: {os.path.exists(cross_encoder_path)}")
    if os.path.exists(cross_encoder_path):
        print(f"Contents: {os.listdir(cross_encoder_path)}")
    print()
    
    # Test all-MiniLM-L6-v2 model
    minilm_path = os.path.join(os.environ['HF_HOME'], 'huggingface', 'hub', 'models--sentence-transformers--all-MiniLM-L6-v2')
    print(f"MiniLM model path: {minilm_path}")
    print(f"Exists: {os.path.exists(minilm_path)}")
    if os.path.exists(minilm_path):
        print(f"Contents: {os.listdir(minilm_path)}")
    print()

def test_model_loading():
    """Test loading models using sentence-transformers"""
    try:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        print("=== Testing Model Loading ===\n")
        
        # Test e5-large-v2
        e5_path = os.path.join(os.environ['TORCH_HOME'], 'sentence_transformers', 'intfloat_e5-large-v2')
        if os.path.exists(e5_path):
            print("Loading e5-large-v2 from local path...")
            model = SentenceTransformer(e5_path)
            print(f"✓ E5 model loaded successfully! Dimension: {model.get_sentence_embedding_dimension()}")
            
            # Test encoding
            test_text = "This is a test sentence."
            embedding = model.encode(test_text)
            print(f"✓ Test embedding generated: shape {embedding.shape}")
        else:
            print("✗ E5 model path not found")
        
        print()
        
        # Test CrossEncoder
        cross_encoder_path = os.path.join(os.environ['HF_HOME'], 'huggingface', 'hub', 'models--cross-encoder--ms-marco-MiniLM-L-6-v2')
        if os.path.exists(cross_encoder_path):
            print("Loading CrossEncoder from local path...")
            reranker = CrossEncoder(cross_encoder_path)
            print("✓ CrossEncoder loaded successfully!")
            
            # Test reranking
            pairs = [("What is the capital of France?", "Paris is the capital of France.")]
            scores = reranker.predict(pairs)
            print(f"✓ Test reranking completed: score {scores[0]:.4f}")
        else:
            print("✗ CrossEncoder model path not found")
            
    except ImportError as e:
        print(f"✗ Failed to import sentence-transformers: {e}")
    except Exception as e:
        print(f"✗ Error loading models: {e}")

if __name__ == "__main__":
    test_model_paths()
    test_model_loading()
    print("\n=== Test Complete ===")
