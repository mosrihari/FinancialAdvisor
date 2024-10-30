from transformers import T5Tokenizer, T5ForConditionalGeneration
model_name = "t5-base"

def summarize(results):
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    text = " ".join(results[0])
    inputs=tokenizer.encode("sumarize: " +text,return_tensors='pt', max_length=2048, truncation=True)
    output = model.generate(inputs, min_length=80, max_length=512)
    summary=tokenizer.decode(output[0], skip_special_tokens=True)
    return summary
