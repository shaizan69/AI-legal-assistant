# Contextual Reasoning Fine-tuning for Legal Document Assistant

This repository contains a comprehensive fine-tuning pipeline for improving the contextual reasoning capabilities of legal document assistants, specifically designed for Indian law, contracts, and financial agreements.

## 🎯 Objective

Fine-tune your selected base model to deeply understand and reason over legal and financial documents, enabling the model to:

1. **Understand context** even if the same keywords are not present
2. **Accurately extract** payment schedules, methods, and conditional clauses
3. **Infer implied information** (e.g., payment intervals, due dates) from context
4. **Avoid giving false or hallucinated answers** when information is missing

## 📊 Dataset Structure

### Training Data Format

Each training example follows this JSON structure:

```json
{
  "instruction": "<specific user query related to payments, clauses, or timelines>",
  "input": "<relevant section(s) from the document>",
  "output": {
    "answer": "<direct, factual answer>",
    "reasoning": "<short explanation of how answer was derived>",
    "clause_reference": "<section or clause number>",
    "confidence": "<High | Medium | Low>"
  }
}
```

### Dataset Files

1. **`contextual_reasoning_dataset.jsonl`** - Core training examples with complex legal language
2. **`synthetic_augmentation_dataset.jsonl`** - Paraphrased and augmented examples
3. **`edge_cases_dataset.jsonl`** - Edge cases, negative examples, and ambiguous scenarios

## 🧠 Training Strategy

### Key Features

- **Contextual Reasoning**: Focus on understanding meaning beyond surface keywords
- **Structured Output**: Consistent format with answer, reasoning, clause reference, and confidence
- **Negative Examples**: Include cases where information is missing or ambiguous
- **Synthetic Augmentation**: Paraphrased clauses to prevent memorization
- **Edge Case Handling**: Scenarios with incomplete or conditional information

### Training Parameters

- **Epochs**: 4-6
- **Learning Rate**: 1.5e-5
- **Batch Size**: 8-12
- **Context Length**: 4096 tokens minimum
- **Optimizer**: AdamW with warmup
- **Loss Function**: Weighted Cross-Entropy emphasizing reasoning tokens
- **Precision**: Mixed precision (bfloat16)

## 🚀 Usage

### 1. Prepare Datasets

Ensure all dataset files are in the `backend/` directory:

```bash
ls backend/*.jsonl
# contextual_reasoning_dataset.jsonl
# synthetic_augmentation_dataset.jsonl
# edge_cases_dataset.jsonl
```

### 2. Run Fine-tuning

```bash
cd backend
python contextual_fine_tuning_script.py \
    --model_name "law-ai/InLegalBERT" \
    --dataset_paths contextual_reasoning_dataset.jsonl synthetic_augmentation_dataset.jsonl edge_cases_dataset.jsonl \
    --epochs 5 \
    --learning_rate 1.5e-5 \
    --batch_size 8 \
    --max_length 4096 \
    --output_dir ./legal_assistant_finetuned
```

### 3. Evaluate Model

```bash
python evaluation_metrics.py
```

## 📈 Evaluation Metrics

The evaluation system measures:

1. **Contextual Accuracy** (30%) - Whether answer aligns with full clause meaning
2. **Monetary Parsing Precision** (25%) - Correct extraction of INR values, %, and timelines
3. **Reasoning Consistency** (15%) - Correctness of "reasoning" section
4. **Hallucination Rate** (15%) - Penalize unsupported or fabricated answers
5. **Clause Identification Accuracy** (10%) - Correct clause reference recognition
6. **Confidence Calibration** (5%) - Appropriate confidence levels

### Overall Score Calculation

```
Overall Score = Σ(Metric Score × Weight)
```

## 🎯 Expected Output Format

After fine-tuning, the model should output responses in this format:

```
**Answer:** <main factual answer>
**Reasoning:** <short explanation of how it found it>
**Clause Reference:** <number or section>
**Confidence:** <High | Medium | Low>
```

## 🔧 Implementation Details

### Model Architecture

- **Base Model**: configurable (e.g., law-ai/InLegalBERT for embeddings)
- **Fine-tuning**: LoRA (Low-Rank Adaptation) for efficient training
- **Context Window**: 4096 tokens
- **Precision**: bfloat16 for numerical stability

### Training Process

1. **Data Loading**: Combine all dataset files
2. **Tokenization**: Format prompts and tokenize with padding
3. **Training**: Use Trainer with specified parameters
4. **Evaluation**: Compute metrics on validation set
5. **Saving**: Save model and tokenizer

### Key Features

- **Contextual Understanding**: Model learns to reason beyond keywords
- **Structured Responses**: Consistent output format
- **Confidence Calibration**: Appropriate confidence levels
- **Hallucination Prevention**: Avoids fabricated information
- **Clause Reference**: Accurate source identification

## 📋 Dataset Examples

### Example 1: Payment Schedule
```json
{
  "instruction": "What is the payment schedule mentioned in this agreement?",
  "input": "Clause 10: The buyer shall pay 20% on signing, 40% on delivery, and the remaining 40% after final inspection within 30 days.",
  "output": {
    "answer": "20% on signing, 40% on delivery, and 40% within 30 days post inspection.",
    "reasoning": "Extracted from sequential payment terms under Clause 10.",
    "clause_reference": "Clause 10",
    "confidence": "High"
  }
}
```

### Example 2: Edge Case
```json
{
  "instruction": "What is the payment schedule?",
  "input": "The parties agree to mutually decide the payment terms based on project milestones and market conditions.",
  "output": {
    "answer": "Payment schedule not specified — to be mutually decided based on milestones and market conditions.",
    "reasoning": "Payment terms are conditional and not explicitly defined.",
    "clause_reference": "Clause 5",
    "confidence": "Low"
  }
}
```

## 🎯 Expected Behavior After Fine-tuning

After fine-tuning, the model should be able to:

- **Identify payment-related terms** even if worded differently
- **Understand conditional payment structures**
- **Handle implicit information** ("upon completion", "post inspection")
- **Reject queries** when no financial data is present instead of hallucinating
- **Provide structured responses** with reasoning and confidence levels
- **Reference specific clauses** accurately
- **Calibrate confidence** appropriately based on information availability

## 🔍 Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce batch size or use gradient accumulation
2. **Poor Performance**: Increase training epochs or adjust learning rate
3. **Hallucination**: Add more negative examples to the dataset
4. **Inconsistent Format**: Ensure all training examples follow the same structure

### Performance Optimization

- Use mixed precision training (bfloat16)
- Implement gradient checkpointing for large models
- Use data parallelism for multi-GPU training
- Monitor training metrics closely

## 📚 References

<!-- Removed GPT-OSS specific reference -->
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [Legal Document Processing](https://en.wikipedia.org/wiki/Legal_document_processing)
- [Indian Contract Law](https://en.wikipedia.org/wiki/Indian_Contract_Act,_1872)

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Add new training examples or improve evaluation metrics
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
