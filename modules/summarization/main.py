from transformers import T5Tokenizer, T5ForConditionalGeneration
import chromadb

model_name = "t5-base"

def summarize(results):
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    text = " ".join(results['documents'][0])
    inputs=tokenizer.encode("sumarize: " +text,return_tensors='pt', max_length=2048, truncation=True)
    output = model.generate(inputs, min_length=80, max_length=512)
    summary=tokenizer.decode(output[0], skip_special_tokens=True)
    return summary

if __name__ == '__main__':
    db = chromadb.PersistentClient(path=r"D:\Raghu Studies\FinancialAdvisor\chroma_dir")
    collection_name = "finance"
    collection = db.get_or_create_collection(collection_name)

    results = collection.query(
        query_texts=["I wanted to invest in Facebook"],
        n_results=5
    )
    summary = summarize(results)