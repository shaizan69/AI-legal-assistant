# Mistral Legal Q4 Setup Guide for Legal Document Analysis

This guide will help you set up Mistral Legal Q4 with Ollama for your legal document analysis system. Mistral Legal Q4 is a specialized legal model optimized for document analysis.

## Why Mistral Legal Q4?

- **Specialized Legal Model**: Optimized for legal document analysis
- **Efficient Size**: ~4.4GB quantized model
- **Better Performance**: More efficient on laptops
- **Quantized**: 4-bit quantization reduces memory usage
- **VERY HIGH QUALITY**: Specialized legal prompts for superior analysis
- **Legal Focus**: Expert-level legal document analysis
- **D: Drive Storage**: All files stored on D: drive (no C: drive usage)

## Prerequisites

- Windows 10/11
- Python 3.8+
- At least 8GB RAM (16GB recommended)
- At least 10GB free disk space on D: drive
- Administrator privileges

## Quick Setup

### Option 1: Automated Setup (Recommended)
```cmd
cd "D:\Legal assistant\ai-legal-assistant\backend"
scripts\setup_mistral.bat
```

### Option 2: Manual Setup
```cmd
cd "D:\Legal assistant\ai-legal-assistant\backend"
python scripts\setup_mistral.py
```

## Manual Setup Steps

### 1. Install Ollama
1. Download Ollama from https://ollama.ai/download/windows
2. Install it with default settings
3. Add Ollama to your PATH environment variable

### 2. Configure Ollama for D: Drive
```cmd
# Set environment variable
set OLLAMA_MODELS=D:\Ollama

# Create directory
mkdir D:\Ollama
```

### 3. Start Ollama Service
```cmd
# Start Ollama with D: drive configuration
set OLLAMA_MODELS=D:\Ollama
ollama serve
```

### 4. Pull Mistral Legal Q4 Model
```cmd
ollama pull mistral-legal-q4:latest
```

### 5. Verify Model Installation
The Mistral Legal Q4 model is already optimized for legal analysis. No additional configuration needed.

## Configuration

### Environment Variables
Your `.env` file is already configured:
```env
# Ollama Configuration (Primary LLM)
OLLAMA_URL=http://localhost:11434
MISTRAL_MODEL=mistral-legal-q4:latest
USE_LORA=false
OLLAMA_PATH=D:\Ollama
```

### Backend Configuration
The system is configured to use **only** Mistral Legal Q4 as the LLM:
- `backend/app/core/config.py` - Main configuration
- `backend/app/core/mistral_llm.py` - Mistral service implementation
- `backend/app/core/llm.py` - Main LLM service

## Usage

### Starting the Service

1. **Start Ollama service**:
   ```cmd
   # Use the provided startup script
   D:\Ollama\start_ollama.bat
   
   # OR manually:
   set OLLAMA_MODELS=D:\Ollama
   ollama serve
   ```

2. **Start the backend**:
   ```cmd
   cd "D:\Legal assistant\ai-legal-assistant\backend"
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Testing the Integration

Run the setup script to test:
```cmd
python scripts\setup_mistral.py
```

## Features

### 1. Document Analysis
- **Summarization**: Structured summaries with key sections
- **Risk Assessment**: Identifies potential legal risks
- **Document Comparison**: Compares two legal documents
- **Q&A**: Answers questions about document content

### 2. Efficient Processing
- **4-bit Quantization**: Reduces memory usage by ~75%
- **Smaller Model**: 4.1GB vs 8GB for Llama 3-8B
- **Faster Inference**: Better performance on laptops
- **D: Drive Storage**: No C: drive usage

### 3. Fallback System
- **Primary**: Mistral 7B via Ollama
- **Fallback**: None (Mistral-legal-q4 is the sole LLM)
- **Seamless**: Automatic fallback on errors

## Performance Comparison

| Model | Size | RAM Usage | Speed | Quality |
|-------|------|-----------|-------|---------|
| Llama 3-8B | ~8GB | 12-16GB | Medium | High |
| Mistral 7B Q4 | ~4.1GB | 6-8GB | Fast | High |
| **Mistral 7B Q4 Legal** | **~4.1GB** | **6-8GB** | **Fast** | **VERY HIGH** |

## Troubleshooting

### Common Issues

1. **Ollama not starting**
   - Check if port 11434 is available
   - Run as Administrator
   - Check Windows Firewall settings

2. **Model not found**
   - Ensure `mistral-legal-q4:latest` is pulled: `ollama pull mistral-legal-q4:latest`
   - Check model list: `ollama list`

3. **Memory issues**
   - Mistral Legal Q4 uses optimized memory settings
   - Close other applications if needed
   - GPU acceleration is enabled for better performance

4. **Slow performance**
   - Mistral Legal Q4 is optimized for legal analysis
   - Ensure you have enough RAM (8GB+)
   - GPU acceleration is enabled by default

### Logs

Check logs in:
- Backend: `backend/logs/app.log`
- Ollama: Check Ollama console output

## Performance Optimization

### 1. GPU Acceleration
If you have an NVIDIA GPU:
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Memory Optimization
For systems with limited RAM:
- Mistral Legal Q4 already uses optimized memory settings
- GPU acceleration reduces CPU memory usage
- Low VRAM mode enabled for 4GB GPUs

### 3. Storage Optimization
- All models stored on D: drive
- No C: drive usage
- Easy to backup and transfer

## Advanced Configuration

### Custom Modelfile
The Mistral Legal Q4 model is already optimized for legal analysis. No additional configuration needed.

### API Configuration
Configure Ollama API settings in `backend/app/core/config.py`:

```python
OLLAMA_URL = "http://localhost:11434"
MISTRAL_MODEL = "mistral-legal-q4:latest"
LEGAL_MODEL = "mistral-legal-q4:latest"
USE_LORA = False
OLLAMA_PATH = "D:\\Ollama"
```

## Support

If you encounter issues:

1. Check the logs
2. Verify Ollama is running: `ollama list`
3. Test with the provided setup script
4. Check system resources (RAM, disk space)
5. Ensure all dependencies are installed

## Next Steps

1. **Run the setup script** to install and configure Mistral Legal Q4
2. **Test the basic functionality** with the setup script
3. **Upload a legal document** and test analysis features
4. **Monitor performance** - optimized for legal analysis
5. **Enjoy the efficiency** - specialized legal model with GPU acceleration

The system is now ready to provide accurate, AI-powered legal document analysis using Mistral Legal Q4 with GPU acceleration!
