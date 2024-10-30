import time
from kafka_events import consume, send_to_kafka
from summary import summarize

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