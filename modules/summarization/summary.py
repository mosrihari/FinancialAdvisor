from transformers import T5Tokenizer, T5ForConditionalGeneration
import settings
model_name = settings.SUMMARY_MODEL_NAME

def summarize(results):
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    text = " ".join(results[0])
    inputs=tokenizer.encode("sumarize: " +text,return_tensors='pt', max_length=2048, truncation=True)
    output = model.generate(inputs, min_length=settings.SUMMARY_MODEL_MIN_GEN_LENGTH, max_length=512)
    summary=tokenizer.decode(output[0], skip_special_tokens=True)
    return summary
