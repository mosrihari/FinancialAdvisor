from kafka import KafkaConsumer, KafkaProducer
import ast
import json
import time

def consume():
    max_retries = 5
    retry_count = 0
    flag = False
    while retry_count < max_retries:
        try:
            consumer = KafkaConsumer(
                'data_collection',               # Topic name
                bootstrap_servers='kafka:9093',  # Kafka broker
                auto_offset_reset='earliest',        # Start at the earliest available message
                enable_auto_commit=False,             # Automatically commit offsets
                group_id='data-collection-group',      # Consumer group ID
                value_deserializer=lambda x: x.decode('utf-8')  # Decode message from bytes to string
                )
            for message in consumer:
                # Print consumed message
                print(f"Message consumed: {message.value} of type {type(message)} from partition {message.partition}, offset {message.offset}")
                data = message.value
                data = ast.literal_eval(data)
                print(data)
                flag = True
                consumer.commit()
                return data
                #break
        except:
            retry_count += 1
            print("Stopping consumer...")
            flag = False
            time.sleep(10)
        if flag:
            break
    #consumer.close()
    return None # dictionary

def send_to_kafka(data):
    
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Published message from Summary:{data}")
    producer.send('summary', data)
    producer.flush()

if __name__ == '__main__':
    while True:
        try:
            results = consume()
            summary = summarize(results['context'])
            results['summary'] = summary
            send_to_kafka(results)
            time.sleep(60)
        except:
            print("Error occured")