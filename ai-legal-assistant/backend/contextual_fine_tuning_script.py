#!/usr/bin/env python3
"""
Contextual Reasoning Fine-tuning Script for Legal Document Assistant
Fine-tunes a chosen base model for deep understanding of legal and financial documents
"""

import json
import torch
import logging
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling,
    AutoModel
)
from datasets import Dataset
from typing import Dict, List, Any
import argparse
from pathlib import Path
import random
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalDocumentDataset:
    """Dataset class for legal document fine-tuning"""
    
    def __init__(self, tokenizer, max_length: int = 4096):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def load_datasets(self, dataset_paths: List[str]) -> Dataset:
        """Load and combine multiple dataset files"""
        all_data = []
        
        for path in dataset_paths:
            logger.info(f"Loading dataset from {path}")
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        all_data.append(data)
        
        logger.info(f"Total examples loaded: {len(all_data)}")
        return Dataset.from_list(all_data)
    
    def format_prompt(self, example: Dict[str, Any]) -> str:
        """Format training example into prompt"""
        instruction = example["instruction"]
        input_text = example["input"]
        output = example["output"]
        
        # Format output as structured text
        if isinstance(output, dict):
            formatted_output = f"""**Answer:** {output['answer']}
**Reasoning:** {output['reasoning']}
**Clause Reference:** {output['clause_reference']}
**Confidence:** {output['confidence']}"""
        else:
            formatted_output = str(output)
        
        prompt = f"""You are an expert legal AI assistant specializing in Indian law, contracts, and financial agreements. Your task is to provide accurate, precise, and helpful answers based on the provided legal document context.

IMPORTANT INSTRUCTIONS:
1. Answer ONLY based on the provided context - do not add external legal knowledge
2. NEVER say "No monetary figure is present" or "The excerpt contains only..." - ALWAYS read the actual context provided
3. If the context doesn't contain enough information to answer fully, say so explicitly
4. Quote specific sections, clauses, or paragraphs when relevant
5. Use precise legal terminology from the document
6. If there are multiple relevant sections, organize your answer clearly
7. Be concise but comprehensive
8. If the question is unclear or ambiguous, ask for clarification
9. CRITICAL: Always analyze the actual context provided, not generic responses

CONTEXTUAL REASONING REQUIREMENTS:
- Understand context even if the same keywords are not present
- Accurately extract payment schedules, methods, and conditional clauses
- Infer implied information (e.g., payment intervals, due dates) from context
- Avoid giving false or hallucinated answers when information is missing
- Provide reasoning for how the answer was derived

LEGAL DOCUMENT CONTEXT:
{input_text}

USER QUESTION: {instruction}

RESPONSE FORMAT:
**Answer:** <direct, factual answer>
**Reasoning:** <short explanation of how answer was derived>
**Clause Reference:** <section or clause number>
**Confidence:** <High | Medium | Low>

RESPONSE:
{formatted_output}"""
        
        return prompt
    
    def tokenize_function(self, examples):
        """Tokenize examples for training"""
        prompts = [self.format_prompt(example) for example in examples]
        
        # Tokenize with padding and truncation
        tokenized = self.tokenizer(
            prompts,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        # For causal LM, labels are the same as input_ids
        tokenized["labels"] = tokenized["input_ids"].clone()
        
        return tokenized

def compute_metrics(eval_pred):
    """Compute evaluation metrics"""
    predictions, labels = eval_pred
    
    # For simplicity, we'll use perplexity as the main metric
    # In practice, you might want to implement more sophisticated metrics
    shift_logits = predictions[..., :-1, :].contiguous()
    shift_labels = labels[..., 1:].contiguous()
    
    loss_fct = torch.nn.CrossEntropyLoss()
    loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
    
    perplexity = torch.exp(loss)
    
    return {
        "perplexity": perplexity.item(),
        "loss": loss.item()
    }

def main():
    parser = argparse.ArgumentParser(description="Fine-tune legal document assistant")
    parser.add_argument("--model_name", default="law-ai/InLegalBERT", help="Model name")
    parser.add_argument("--output_dir", default="./legal_assistant_finetuned", help="Output directory")
    parser.add_argument("--dataset_paths", nargs="+", required=True, help="Paths to dataset files")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--learning_rate", type=float, default=1.5e-5, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--max_length", type=int, default=4096, help="Max sequence length")
    parser.add_argument("--warmup_steps", type=int, default=100, help="Warmup steps")
    parser.add_argument("--save_steps", type=int, default=500, help="Save steps")
    parser.add_argument("--eval_steps", type=int, default=500, help="Evaluation steps")
    parser.add_argument("--logging_steps", type=int, default=100, help="Logging steps")
    
    args = parser.parse_args()
    
    # Initialize tokenizer and model
    logger.info(f"Loading tokenizer and model: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # For InLegalBERT, we use AutoModel instead of AutoModelForCausalLM
    if "InLegalBERT" in args.model_name:
        model = AutoModel.from_pretrained(
            args.model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
    
    # Initialize dataset
    dataset_handler = LegalDocumentDataset(tokenizer, args.max_length)
    dataset = dataset_handler.load_datasets(args.dataset_paths)
    
    # Split dataset
    train_test_split = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = train_test_split["train"]
    eval_dataset = train_test_split["test"]
    
    # Tokenize datasets
    logger.info("Tokenizing datasets...")
    train_dataset = train_dataset.map(
        dataset_handler.tokenize_function,
        batched=True,
        remove_columns=train_dataset.column_names
    )
    eval_dataset = eval_dataset.map(
        dataset_handler.tokenize_function,
        batched=True,
        remove_columns=eval_dataset.column_names
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # We're doing causal LM, not masked LM
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        warmup_steps=args.warmup_steps,
        learning_rate=args.learning_rate,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        eval_steps=args.eval_steps,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="perplexity",
        greater_is_better=False,
        fp16=False,
        bf16=True,  # Use bfloat16 for better numerical stability
        dataloader_drop_last=True,
        report_to="none",  # Disable wandb/tensorboard for now
        remove_unused_columns=False,
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    # Start training
    logger.info("Starting training...")
    trainer.train()
    
    # Save the final model
    logger.info("Saving final model...")
    trainer.save_model()
    tokenizer.save_pretrained(args.output_dir)
    
    # Evaluate the model
    logger.info("Evaluating model...")
    eval_results = trainer.evaluate()
    logger.info(f"Evaluation results: {eval_results}")
    
    logger.info("Fine-tuning completed successfully!")

if __name__ == "__main__":
    main()
