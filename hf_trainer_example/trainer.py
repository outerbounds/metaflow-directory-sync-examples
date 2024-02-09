import argparse

from datasets import load_dataset
from transformers import AutoModelForSequenceClassification
from transformers import TrainingArguments
from transformers import AutoTokenizer
from transformers import DataCollatorWithPadding
from transformers import Trainer

def main(
    checkpoint_dir: str = "training_output",
    ds_name: str = "rotten_tomatoes",
    sample_size: float = 0.05,
):

    dataset = load_dataset(ds_name)
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    def tokenize_dataset(dataset):
        return tokenizer(dataset["text"])

    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
    dataset = dataset.map(tokenize_dataset, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=checkpoint_dir,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=1,
        logging_steps=1,  
        save_steps=1,    
        eval_steps=2,     
        warmup_steps=1,   
        max_steps=4,  
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
        data_collator=data_collator
    )
    trainer.train()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-dir", type=str, default="training_output")
    parser.add_argument("--local_rank", type=int, default=0) # include if using argparse, deepspeed launcher automatically sets this.
    args = parser.parse_args()
    main(checkpoint_dir=args.checkpoint_dir)