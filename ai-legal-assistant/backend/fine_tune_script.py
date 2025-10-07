#!/usr/bin/env python3
"""
Fine-tuning script for Indian Legal Document Assistant
Based on OpenAI GPT-OSS-120B model specifications
"""

import json
import torch
import transformers
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import logging
from typing import Dict, List, Any
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndianLegalFineTuner:
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", max_length: int = 4096):
        """
        Initialize the fine-tuner
        
        Args:
            model_name: Base model to fine-tune (replace with actual GPT-OSS-120B)
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        self.max_length = max_length
        self.tokenizer = None
        self.model = None
        
    def load_model_and_tokenizer(self):
        """Load the base model and tokenizer"""
        logger.info(f"Loading model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        logger.info("Model and tokenizer loaded successfully")
        
    def load_training_data(self, data_path: str) -> Dataset:
        """Load and preprocess training data"""
        logger.info(f"Loading training data from {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f]
            
        logger.info(f"Loaded {len(data)} training samples")
        
        # Convert to HuggingFace dataset format
        dataset = Dataset.from_list(data)
        
        return dataset
    
    def format_prompt(self, instruction: str, input_text: str, output: str) -> str:
        """Format the training prompt according to Indian legal assistant requirements"""
        prompt = f"""You are an AI-powered Legal Document Assistant specialized in Indian law, contracts, and financial agreements.

INSTRUCTION: {instruction}

DOCUMENT CONTEXT: {input_text}

RESPONSE FORMAT:
- Answer: <direct answer>
- Clause Reference: <clause number / section>
- Amount (if any): <INR value>
- Summary: <one-line explanation>

RESPONSE: {output}

Remember:
- Understand Indian legal phrasing
- Return INR amounts accurately
- Handle table data when you see "TABLE DATA:" in context
- Extract specific values from tables accurately
- Calculate totals and percentages from table data
- Reject queries unrelated to provided documents
- Produce deterministic, structured, and explainable answers"""
        
        return prompt
    
    def tokenize_function(self, examples):
        """Tokenize the training examples"""
        prompts = []
        for i in range(len(examples['instruction'])):
            prompt = self.format_prompt(
                examples['instruction'][i],
                examples['input'][i],
                examples['output'][i]
            )
            prompts.append(prompt)
        
        # Tokenize
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
    
    def prepare_dataset(self, dataset: Dataset) -> Dataset:
        """Prepare the dataset for training"""
        logger.info("Preparing dataset for training")
        
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        return tokenized_dataset
    
    def create_training_arguments(self, output_dir: str, num_epochs: int = 3) -> TrainingArguments:
        """Create training arguments"""
        return TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            gradient_accumulation_steps=2,
            learning_rate=2e-5,
            weight_decay=0.01,
            warmup_steps=100,
            logging_steps=10,
            save_steps=500,
            eval_steps=500,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=torch.cuda.is_available(),
            bf16=torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8,
            dataloader_num_workers=4,
            remove_unused_columns=False,
            report_to=None,  # Disable wandb/tensorboard
        )
    
    def create_trainer(self, train_dataset: Dataset, eval_dataset: Dataset, training_args: TrainingArguments) -> Trainer:
        """Create the trainer"""
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # We're doing causal LM, not masked LM
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        return trainer
    
    def fine_tune(self, data_path: str, output_dir: str, num_epochs: int = 3):
        """Main fine-tuning function"""
        logger.info("Starting fine-tuning process")
        
        # Load model and tokenizer
        self.load_model_and_tokenizer()
        
        # Load and prepare data
        dataset = self.load_training_data(data_path)
        
        # Split dataset (80% train, 20% eval)
        split_dataset = dataset.train_test_split(test_size=0.2, seed=42)
        train_dataset = split_dataset['train']
        eval_dataset = split_dataset['test']
        
        # Prepare datasets
        train_dataset = self.prepare_dataset(train_dataset)
        eval_dataset = self.prepare_dataset(eval_dataset)
        
        # Create training arguments
        training_args = self.create_training_arguments(output_dir, num_epochs)
        
        # Create trainer
        trainer = self.create_trainer(train_dataset, eval_dataset, training_args)
        
        # Start training
        logger.info("Starting training...")
        trainer.train()
        
        # Save the fine-tuned model
        logger.info(f"Saving fine-tuned model to {output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info("Fine-tuning completed successfully!")
        
        return trainer

def create_validation_data():
    """Create validation dataset for evaluation"""
    validation_data = [
        {
            "instruction": "What is the penalty for breach of contract?",
            "input": "Clause 15. Breach Penalty: In case of breach, the defaulting party shall pay Rs. 2,00,000/- as penalty.",
            "expected_output": "**Answer:** Breach penalty is INR 200,000\n**Clause Reference:** Clause 15\n**Amount:** INR 200,000\n**Summary:** Penalty for contract breach"
        },
        {
            "instruction": "What is the contract renewal period?",
            "input": "Section 8. Renewal: This contract may be renewed for additional 12-month periods upon mutual agreement.",
            "expected_output": "**Answer:** Contract renewal period is 12 months\n**Clause Reference:** Section 8\n**Amount:** None\n**Summary:** 12-month renewal periods upon mutual agreement"
        },
        {
            "instruction": "What are the payment terms for advance?",
            "input": "Article 6. Advance Payment: 30% advance payment of Rs. 3,00,000/- shall be made before commencement.",
            "expected_output": "**Answer:** Advance payment is 30% (INR 300,000)\n**Clause Reference:** Article 6\n**Amount:** INR 300,000\n**Summary:** 30% advance before commencement"
        }
    ]
    
    with open('validation_data.jsonl', 'w', encoding='utf-8') as f:
        for item in validation_data:
            f.write(json.dumps(item) + '\n')
    
    logger.info("Validation data created")

def evaluate_model(model_path: str, validation_data_path: str):
    """Evaluate the fine-tuned model"""
    logger.info("Evaluating fine-tuned model")
    
    # Load the fine-tuned model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    
    # Load validation data
    with open(validation_data_path, 'r', encoding='utf-8') as f:
        validation_data = [json.loads(line) for line in f]
    
    # Evaluation metrics
    total_samples = len(validation_data)
    correct_answers = 0
    correct_clause_refs = 0
    correct_amounts = 0
    
    for item in validation_data:
        # Generate response
        prompt = f"""You are an AI-powered Legal Document Assistant specialized in Indian law, contracts, and financial agreements.

INSTRUCTION: {item['instruction']}

DOCUMENT CONTEXT: {item['input']}

RESPONSE FORMAT:
- Answer: <direct answer>
- Clause Reference: <clause number / section>
- Amount (if any): <INR value>
- Summary: <one-line explanation>

RESPONSE:"""
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_text = response[len(prompt):].strip()
        
        # Simple evaluation (in practice, you'd use more sophisticated metrics)
        expected = item['expected_output']
        
        # Check if key elements are present
        if "Answer:" in generated_text and "Clause Reference:" in generated_text:
            correct_answers += 1
        
        if "Clause Reference:" in generated_text:
            correct_clause_refs += 1
            
        if "Amount:" in generated_text:
            correct_amounts += 1
    
    # Calculate metrics
    answer_accuracy = correct_answers / total_samples
    clause_accuracy = correct_clause_refs / total_samples
    amount_accuracy = correct_amounts / total_samples
    
    logger.info(f"Evaluation Results:")
    logger.info(f"Answer Accuracy: {answer_accuracy:.2%}")
    logger.info(f"Clause Reference Accuracy: {clause_accuracy:.2%}")
    logger.info(f"Amount Extraction Accuracy: {amount_accuracy:.2%}")
    
    return {
        "answer_accuracy": answer_accuracy,
        "clause_accuracy": clause_accuracy,
        "amount_accuracy": amount_accuracy
    }

if __name__ == "__main__":
    # Configuration
    MODEL_NAME = "microsoft/DialoGPT-medium"  # Replace with actual GPT-OSS-120B
    DATA_PATH = "training_data.jsonl"
    OUTPUT_DIR = f"fine_tuned_legal_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    NUM_EPOCHS = 3
    
    # Create validation data
    create_validation_data()
    
    # Initialize fine-tuner
    fine_tuner = IndianLegalFineTuner(MODEL_NAME)
    
    # Fine-tune the model
    trainer = fine_tuner.fine_tune(
        data_path=DATA_PATH,
        output_dir=OUTPUT_DIR,
        num_epochs=NUM_EPOCHS
    )
    
    # Evaluate the model
    evaluation_results = evaluate_model(OUTPUT_DIR, "validation_data.jsonl")
    
    print("\n" + "="*50)
    print("FINE-TUNING COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"Model saved to: {OUTPUT_DIR}")
    print(f"Training samples: {len(fine_tuner.load_training_data(DATA_PATH))}")
    print(f"Epochs: {NUM_EPOCHS}")
    print(f"Answer Accuracy: {evaluation_results['answer_accuracy']:.2%}")
    print(f"Clause Accuracy: {evaluation_results['clause_accuracy']:.2%}")
    print(f"Amount Accuracy: {evaluation_results['amount_accuracy']:.2%}")
    print("="*50)
