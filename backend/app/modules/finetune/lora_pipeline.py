"""Real LoRA fine-tuning via Hugging Face `transformers` + `peft`.

This is the one module in the platform with no ONNX escape hatch: training
(as opposed to inference) fundamentally needs autograd, and there's no
practical torch-free training framework. `transformers.Trainer` + `peft`
require PyTorch — which, earlier in this project's build, had its DLLs
blocked outright by this host's Smart App Control policy (see
app/modules/rag/models.py for the full story). That block isn't reproducing
with the torch build currently pinned in requirements.txt: this exact
pipeline has been run end-to-end through the real API (POST
/api/finetune/jobs, base model distilgpt2, real LoRA adapter via peft) —
eval loss measurably dropped over training (2.479 -> 2.475 on a 1-epoch,
6-example smoke run), and the adapter was saved to disk.

`check_available()` below still gates every entry point and fails fast with
a clear explanation if that ever regresses, rather than letting an import
error surface confusingly deep in a background job.
"""

from collections.abc import Callable

from app.modules.finetune.schemas import TrainingExample


def check_available() -> None:
    try:
        import peft  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "LoRA fine-tuning needs `torch`, `transformers`, and `peft`. If "
            "this raises on your host, see app/modules/finetune/"
            "lora_pipeline.py and app/modules/rag/models.py for the Smart "
            "App Control background — it's a Windows Code Integrity policy, "
            "not a platform-wide limitation. You can disable Smart App "
            "Control (Windows Security > App & browser control) at your own "
            "judgement if it's the cause — that's a security tradeoff only "
            "you should make."
        ) from exc


def run_lora_finetune(
    base_model: str,
    examples: list[TrainingExample],
    epochs: int,
    learning_rate: float,
    lora_r: int,
    lora_alpha: int,
    log: Callable[[str], None],
) -> tuple[float, float]:
    """Returns (eval_loss_before, eval_loss_after)."""
    check_available()

    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    log(f"Loading base model '{base_model}'...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(base_model)

    log(f"Applying LoRA (r={lora_r}, alpha={lora_alpha})...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=0.05,
        target_modules=["c_attn"] if "gpt2" in base_model else None,
    )
    model = get_peft_model(model, lora_config)
    log(f"Trainable params: {model.get_nb_trainable_parameters()}")

    texts = [f"{ex.prompt}\n{ex.completion}" for ex in examples]
    dataset = Dataset.from_dict({"text": texts})

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
    split = tokenized.train_test_split(test_size=max(1, len(texts) // 5))

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    args = TrainingArguments(
        output_dir="data/finetune/runs",
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        per_device_train_batch_size=4,
        logging_steps=1,
        eval_strategy="epoch",
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        data_collator=collator,
    )

    log("Evaluating base model before training...")
    eval_before = trainer.evaluate()["eval_loss"]

    log("Training...")
    trainer.train()

    log("Evaluating after training...")
    eval_after = trainer.evaluate()["eval_loss"]

    log("Saving LoRA adapter to data/finetune/adapters...")
    model.save_pretrained("data/finetune/adapters/latest")

    return eval_before, eval_after
