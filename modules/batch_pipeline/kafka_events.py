from kafka import KafkaProducer,KafkaConsumer
import json
import ast
from preprocessing import query_data
import settings

def send_to_kafka(db, data):
    collection_name = settings.CHROMA_DB_COLLECTION
    collection = db.get_or_create_collection(collection_name)
    results = query_data(collection, data['question'])
    data['context'] = results
    producer = KafkaProducer(
        bootstrap_servers=settings.KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Message published to data_collection:{data['context']}")
    producer.send(settings.KAFKA_PUBLISHER_TOPIC, data)
    producer.flush()

def consume():
    consumer = KafkaConsumer(
        settings.KAFKA_CONSUMER_TOPIC,               # Topic name
        bootstrap_servers=settings.KAFKA_SERVER,  # Kafka broker
        auto_offset_reset='earliest',        # Start at the earliest available message
        enable_auto_commit=False,             # Automatically commit offsets
        group_id=settings.KAFKA_GROUP_ID,      # Consumer group ID
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

