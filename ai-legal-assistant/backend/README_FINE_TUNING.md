# Indian Legal Document Assistant - Fine-tuning Guide

This guide provides comprehensive instructions for fine-tuning a large language model to act as an AI-powered Legal Document Assistant specialized in Indian law, contracts, and financial agreements.

## Overview

The fine-tuning process transforms a base language model (GPT-OSS-120B) into a specialized legal assistant that can:
1. Read and interpret long Indian legal and financial documents
2. Accurately answer clause-specific questions
3. Extract and reason over monetary values, dates, and legal references
4. Provide concise, verifiable answers with supporting clause citations

## Files Structure

```
backend/
├── training_data.jsonl              # Training dataset
├── fine_tune_script.py             # Main fine-tuning script
├── evaluation_metrics.py            # Evaluation metrics and validation
├── integrate_finetuned_model.py    # Integration with existing system
├── requirements_training.txt        # Python dependencies
└── README_FINE_TUNING.md          # This guide
```

## Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA GPU with at least 24GB VRAM (recommended: A100, V100, or RTX 4090)
- **RAM**: 64GB+ system RAM
- **Storage**: 500GB+ SSD storage for model and data

### Software Requirements
- Python 3.8+
- CUDA 11.8+ (for GPU acceleration)
- PyTorch 2.0+
- Transformers 4.30+

## Installation

### Option 1: Automatic Dependency Fix (Recommended)

1. **Run the dependency fix script:**
```bash
python fix_dependencies.py
```

This script will:
- Remove conflicting torch/torchvision versions
- Install compatible versions (torch==2.1.1, torchvision==0.16.1)
- Install all required fine-tuning dependencies
- Verify installation and check system requirements

### Option 2: Manual Installation

1. **Fix torch/torchvision conflicts:**
```bash
pip uninstall torch torchvision -y
pip install torch==2.1.1 torchvision==0.16.1
```

2. **Install Python dependencies:**
```bash
pip install -r requirements_training.txt
```

3. **Verify GPU availability:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

4. **Check CUDA version:**
```bash
nvidia-smi
```

## Training Data Format

The training data follows the supervised fine-tuning format with instruction-response pairs:

```json
{
  "instruction": "What is the penalty amount for delayed payment?",
  "input": "Section 12. Penalty for delayed payment shall be Rs. 50,000 per month for any delay beyond the due date.",
  "output": "**Answer:** Delayed payment penalty is INR 50,000 per month\n**Clause Reference:** Section 12\n**Amount:** INR 50,000\n**Summary:** Monthly penalty for payments beyond due date"
}
```

### Key Features of Training Data:
- **Diverse document types**: Contracts, MoUs, loan agreements, property deeds
- **Monetary reasoning**: INR amounts, percentages, fees, penalties
- **Date reasoning**: Contract periods, notice periods, deadlines
- **Legal references**: Section numbers, clause references, article citations
- **Table data extraction**: Pricing tables, payment schedules, fee structures
- **Structured output**: Consistent format with Answer, Clause Reference, Amount, Summary

## Fine-tuning Process

### Step 1: Prepare Training Data

The training data is already prepared in `training_data.jsonl` with 50+ examples covering:
- Financial terms and amounts
- Legal clause references
- Contract durations and deadlines
- Penalties and fees
- Compliance requirements
- Table data extraction (pricing tables, payment schedules, fee structures)

### Step 2: Run Fine-tuning

```bash
python fine_tune_script.py
```

**Training Parameters:**
- **Epochs**: 3-5
- **Batch Size**: 8-16 (depending on GPU memory)
- **Learning Rate**: 2e-5 (with decay after 2 epochs)
- **Max Sequence Length**: 4096 tokens
- **Mixed Precision**: bfloat16 (if supported)

### Step 3: Monitor Training

The script provides detailed logging:
- Training loss per epoch
- Validation metrics
- GPU memory usage
- Training progress

### Step 4: Evaluate Model

```bash
python evaluation_metrics.py
```

**Evaluation Metrics:**
- **Legal reasoning accuracy**: Correctness of legal interpretations
- **Monetary extraction precision**: Accuracy of amount identification
- **Hallucination rate**: Frequency of fabricated information
- **Response structure adherence**: Compliance with required format

## Model Integration

### Step 1: Load Fine-tuned Model

```python
from integrate_finetuned_model import FineTunedLegalAssistant

# Initialize the fine-tuned assistant
assistant = FineTunedLegalAssistant("path/to/fine_tuned_model")
```

### Step 2: Replace Existing LLM Service

```python
# Replace the existing answer_question function
def fine_tuned_answer_question(question: str, context: str) -> Dict[str, Any]:
    result = assistant.analyze_document(question, context)
    return {
        "answer": result["answer"],
        "confidence": 0.9,
        "model_used": "fine_tuned_legal_assistant",
        "timestamp": result["timestamp"]
    }
```

### Step 3: Update API Endpoints

Modify the existing API endpoints to use the fine-tuned model:

```python
# In backend/app/api/free.py
result = await fine_tuned_answer_question(question, context)
```

## Expected Output Format

After fine-tuning, the model responds in this structured pattern:

```
**Answer:** Delayed payment penalty is INR 50,000 per month
**Clause Reference:** Section 12
**Amount:** INR 50,000
**Summary:** Monthly penalty for payments beyond due date
```

## Performance Benchmarks

### Target Metrics:
- **Answer Accuracy**: >85%
- **Clause Reference Accuracy**: >90%
- **Amount Extraction Accuracy**: >80%
- **Structure Compliance**: >95%
- **Hallucination Rate**: <5%

### Evaluation Criteria:
1. **Legal Reasoning**: Correct interpretation of legal clauses
2. **Monetary Precision**: Accurate extraction of INR amounts
3. **Reference Accuracy**: Correct section/clause citations
4. **Format Compliance**: Adherence to structured output
5. **Hallucination Detection**: No fabricated information

## Troubleshooting

### Common Issues:

1. **Dependency Conflicts (torch/torchvision)**:
   ```bash
   # Run the automatic fix
   python fix_dependencies.py
   
   # Or manually fix
   pip uninstall torch torchvision -y
   pip install torch==2.1.1 torchvision==0.16.1
   ```

2. **CUDA Out of Memory**:
   - Reduce batch size
   - Use gradient accumulation
   - Enable mixed precision training

3. **Training Loss Not Decreasing**:
   - Check learning rate
   - Verify data quality
   - Increase training epochs

4. **Poor Performance on Validation**:
   - Add more diverse training data
   - Adjust hyperparameters
   - Check for data leakage

5. **Import Errors**:
   ```bash
   # Reinstall all dependencies
   pip install -r requirements_training.txt --force-reinstall
   ```

6. **GPU Not Detected**:
   ```bash
   # Check CUDA installation
   nvidia-smi
   
   # Verify PyTorch CUDA support
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### Performance Optimization:

1. **GPU Memory Optimization**:
   ```python
   # Use gradient checkpointing
   model.gradient_checkpointing_enable()
   
   # Use mixed precision
   training_args.fp16 = True
   training_args.bf16 = True
   ```

2. **Data Loading Optimization**:
   ```python
   # Increase dataloader workers
   training_args.dataloader_num_workers = 4
   
   # Use prefetching
   training_args.dataloader_pin_memory = True
   ```

## Deployment Considerations

### Production Readiness:
1. **Model Validation**: Thorough testing on unseen legal documents
2. **Performance Monitoring**: Track accuracy metrics in production
3. **Fallback Mechanism**: Maintain backup to original model
4. **A/B Testing**: Compare fine-tuned vs. original model performance

### Security Considerations:
1. **Model Security**: Protect fine-tuned model weights
2. **Data Privacy**: Ensure training data compliance
3. **Access Control**: Restrict model access to authorized users

## Future Improvements

### Potential Enhancements:
1. **Domain-Specific Training**: Specialize for specific legal domains
2. **Multi-language Support**: Extend to regional languages
3. **Real-time Learning**: Continuous model updates
4. **Advanced Evaluation**: More sophisticated metrics

### Research Directions:
1. **Legal Reasoning**: Improve complex legal interpretation
2. **Document Understanding**: Better handling of complex documents
3. **Citation Accuracy**: Enhanced legal reference extraction
4. **Hallucination Reduction**: Advanced techniques to prevent fabrication

## Support and Maintenance

### Regular Maintenance:
1. **Model Updates**: Periodic retraining with new data
2. **Performance Monitoring**: Continuous evaluation
3. **Bug Fixes**: Address issues as they arise
4. **Documentation Updates**: Keep guides current

### Contact Information:
- **Technical Issues**: Check logs and error messages
- **Performance Questions**: Review evaluation metrics
- **Integration Help**: Refer to integration guide

## Conclusion

This fine-tuning guide provides a comprehensive approach to creating a specialized Indian Legal Document Assistant. The process involves careful data preparation, systematic training, thorough evaluation, and seamless integration with existing systems.

The fine-tuned model should demonstrate significant improvements in:
- Legal document understanding
- Monetary value extraction
- Clause reference accuracy
- Structured response generation
- Reduced hallucination rates

Follow this guide step-by-step to achieve optimal results for your legal document assistant.
