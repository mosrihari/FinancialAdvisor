from kafka import KafkaProducer
import json
from kafka import KafkaConsumer
import ast
import time
    
def receive_events():
    max_retries = 10
    retry_count = 0
    flag = False
    while retry_count < max_retries:
        try:
            consumer = KafkaConsumer(
            'summary',               # Topic name
            bootstrap_servers='kafka:9093',  # Kafka broker
            auto_offset_reset='earliest',        # Start at the earliest available message
            enable_auto_commit=False,             # Automatically commit offsets
            group_id='summary-group',      # Consumer group ID
            value_deserializer=lambda x: x.decode('utf-8')  # Decode message from bytes to string
            )
            for message in consumer:
                # Print consumed message
                data = message.value
                data = ast.literal_eval(data)
                flag = True
                consumer.commit()
                break
        except:
            retry_count += 1
            print("Stopping consumer...")
            flag = False
            time.sleep(10)
        if flag:
            break

    return data

def send_to_kafka(data):
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    producer.send('gradio_events', data)
    producer.flush()
