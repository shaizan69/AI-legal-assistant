# Llama 3-8B Setup Guide for Legal Document Analysis

This guide will help you set up Llama 3-8B with Ollama for your legal document analysis system, including LoRA fine-tuning capabilities.

## Prerequisites

- Windows 10/11
- Python 3.8+
- At least 16GB RAM (32GB recommended for LoRA training)
- At least 50GB free disk space on D: drive
- Administrator privileges

## Quick Setup

### 1. Install Ollama and Llama 3-8B

Run the PowerShell script as Administrator:

```powershell
cd "D:\Legal assistant\ai-legal-assistant\backend\scripts"
.\install_ollama.ps1
```

This script will:
- Download and install Ollama
- Pull the Llama 3-8B model
- Create a specialized legal document analysis model
- Set up the necessary directory structure

### 2. Install Python Dependencies

```bash
cd "D:\Legal assistant\ai-legal-assistant\backend"
pip install -r requirements.txt
```

### 3. Test the Installation

```bash
python "D:\Ollama\test_ollama.py"
```

## Manual Setup (Alternative)

If the automated script doesn't work, follow these manual steps:

### 1. Install Ollama

1. Download Ollama from https://ollama.ai/download/windows
2. Install it with default settings
3. Add Ollama to your PATH environment variable

### 2. Pull Llama 3-8B Model

```bash
ollama pull llama3:8b
```

### 3. Create Legal Document Analysis Model

Create a file `D:\Ollama\Modelfile.legal`:

```
FROM llama3:8b

SYSTEM """You are a specialized legal document analysis assistant. You excel at:

1. Contract Analysis: Identifying key terms, parties, obligations, and risks
2. Legal Document Summarization: Creating clear, structured summaries
3. Risk Assessment: Identifying potential legal risks and issues
4. Document Comparison: Comparing legal documents and highlighting differences
5. Q&A: Answering questions about legal documents with precise, evidence-based responses

You provide accurate, professional, and detailed analysis of legal documents including contracts, agreements, policies, and other legal texts. Always cite specific clauses, sections, or provisions when possible."""
```

Create the model:

```bash
ollama create legal-llama3 -f D:\Ollama\Modelfile.legal
```

### 4. Start Ollama Service

```bash
ollama serve
```

## LoRA Fine-Tuning Setup

### 1. Install LoRA Training Dependencies

```bash
pip install -r D:\Ollama\requirements.txt
```

### 2. Run LoRA Setup Script

```bash
python "D:\Legal assistant\ai-legal-assistant\backend\scripts\setup_llama_lora.py"
```

### 3. Train LoRA Model

```bash
python "D:\Ollama\scripts\train_legal_lora.py"
```

## Configuration

### Environment Variables

Update your `.env` file:

```env
# Ollama Configuration (Primary LLM)
OLLAMA_URL=http://localhost:11434
LLAMA_MODEL=llama3:8b
LORA_MODEL=llama3-legal-lora
USE_LORA=true
OLLAMA_PATH=D:\Ollama
```

### Backend Configuration

The system is already configured to use Ollama as the primary LLM. The configuration is in:

- `backend/app/core/config.py` - Main configuration
- `backend/app/core/llama_llm.py` - Llama service implementation
- `backend/app/core/llm.py` - Main LLM service with fallback

## Usage

### Starting the Service

1. Start Ollama service:
   ```bash
   ollama serve
   ```

2. Start the backend:
   ```bash
   cd "D:\Legal assistant\ai-legal-assistant\backend"
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Testing the Integration

Run the test script:

```bash
python "D:\Ollama\test_ollama.py"
```

## Features

### 1. Document Analysis
- **Summarization**: Structured summaries with key sections
- **Risk Assessment**: Identifies potential legal risks
- **Document Comparison**: Compares two legal documents
- **Q&A**: Answers questions about document content

### 2. LoRA Fine-Tuning
- **Custom Training**: Fine-tune on your specific legal documents
- **Improved Accuracy**: Better performance on legal terminology
- **Domain Adaptation**: Specialized for legal document analysis

### 3. Fallback System
- **Primary**: Llama 3-8B via Ollama
- **Fallback**: None (deprecated)
- **Seamless**: Automatic fallback on errors

## Troubleshooting

### Common Issues

1. **Ollama not starting**
   - Check if port 11434 is available
   - Run as Administrator
   - Check Windows Firewall settings

2. **Model not found**
   - Ensure `llama3:8b` is pulled: `ollama pull llama3:8b`
   - Check model list: `ollama list`

3. **Memory issues**
   - Close other applications
   - Reduce batch size in LoRA training
   - Use CPU-only mode if needed

4. **Slow performance**
   - Ensure you have enough RAM (16GB+)
   - Use GPU acceleration if available
   - Consider using a smaller model for testing

### Logs

Check logs in:
- Backend: `backend/logs/app.log`
- Ollama: Check Ollama console output

## Performance Optimization

### 1. GPU Acceleration
If you have an NVIDIA GPU:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Memory Optimization
For systems with limited RAM:
- Use `llama3:8b-instruct-q4_K_M` (quantized model)
- Reduce context length
- Use smaller batch sizes

### 3. LoRA Training Optimization
- Use gradient checkpointing
- Reduce learning rate
- Use mixed precision training

## Advanced Configuration

### Custom Modelfile
Create custom models for specific legal domains:

```
FROM llama3:8b

SYSTEM """You are a contract law specialist focusing on:
- Employment contracts
- Service agreements
- Partnership agreements
- Commercial leases

Provide detailed analysis with specific legal precedents and recommendations."""
```

### API Configuration
Configure Ollama API settings in `backend/app/core/config.py`:

```python
OLLAMA_URL = "http://localhost:11434"
LLAMA_MODEL = "legal-llama3"
LORA_MODEL = "llama3-legal-lora"
USE_LORA = True
```

## Support

If you encounter issues:

1. Check the logs
2. Verify Ollama is running: `ollama list`
3. Test with the provided test script
4. Check system resources (RAM, disk space)
5. Ensure all dependencies are installed

## Next Steps

1. **Test the basic functionality** with the test script
2. **Upload a legal document** and test analysis features
3. **Fine-tune with your data** using the LoRA setup
4. **Monitor performance** and adjust settings as needed
5. **Scale up** with more training data for better accuracy

The system is now ready to provide accurate, AI-powered legal document analysis using Llama 3-8B!
