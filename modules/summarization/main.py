from transformers import T5Tokenizer, T5ForConditionalGeneration
import chromadb
from kafka import KafkaConsumer, KafkaProducer
import ast
import json
model_name = "t5-base"

def summarize(results):
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    text = " ".join(results[0])
    inputs=tokenizer.encode("sumarize: " +text,return_tensors='pt', max_length=2048, truncation=True)
    output = model.generate(inputs, min_length=80, max_length=512)
    summary=tokenizer.decode(output[0], skip_special_tokens=True)
    return summary

def consume():
    consumer = KafkaConsumer(
        'data_collection',               # Topic name
        bootstrap_servers='kafka:9093',  # Kafka broker
        auto_offset_reset='earliest',        # Start at the earliest available message
        enable_auto_commit=True,             # Automatically commit offsets
        group_id='data-collection-group',      # Consumer group ID
        value_deserializer=lambda x: x.decode('utf-8')  # Decode message from bytes to string
        )
    try:
        for message in consumer:
            # Print consumed message
            print(f"Message consumed: {message.value} of type {type(message)} from partition {message.partition}, offset {message.offset}")
            data = message.value
            data = ast.literal_eval(data)
            print(data)
            break
    except:
        print("Stopping consumer...")
    consumer.close()
    return data # dictionary

def send_to_kafka(data):
    
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send('summary', data)
    producer.flush()

if __name__ == '__main__':
    results = consume()
    summary = summarize(results['context'])
    results['summary'] = summary
    send_to_kafka(results)
