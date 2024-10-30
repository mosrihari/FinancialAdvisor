from kafka import KafkaProducer,KafkaConsumer
import json
import ast
from preprocessing import query_data

def send_to_kafka(db, data):
    collection_name = "finance"
    collection = db.get_or_create_collection(collection_name)
    results = query_data(collection, data['question'])
    data['context'] = results
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Message published to data_collection:{data['context']}")
    producer.send('data_collection', data)
    producer.flush()

def consume():
    consumer = KafkaConsumer(
        'gradio_events',               # Topic name
        bootstrap_servers='kafka:9093',  # Kafka broker
        auto_offset_reset='earliest',        # Start at the earliest available message
        enable_auto_commit=False,             # Automatically commit offsets
        group_id='gradio-events-group',      # Consumer group ID
        value_deserializer=lambda x: x.decode('utf-8')  # Decode message from bytes to string
        )
    try:
        for message in consumer:
            # Print consumed message
            print(f"Message consumed: {message.value} of type {type(message)} from partition {message.partition}, offset {message.offset}")
            data = message.value
            data = ast.literal_eval(data)
            print(data)
            consumer.commit()
            return data
    except:
        print("Stopping consumer...")
    return None

