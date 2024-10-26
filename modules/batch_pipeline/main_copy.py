import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unstructured.cleaners.core import (
    clean_extra_whitespace, 
    clean_non_ascii_chars,
    group_broken_paragraphs
)
import re
from unstructured.partition.html import partition_html
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from kafka import KafkaProducer, KafkaConsumer
import json
import ast
import os
from dotenv import load_dotenv

load_dotenv()

# Alpaca API credentials
API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = 'https://data.alpaca.markets/v1beta1/news'
model_name = "all-MiniLM-L6-v2"
model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name)

def fetch_alpaca_news(ticker, limit=50, start_date=None, end_date=None):
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': API_SECRET
    }
    params = {
        'limit': limit,
        'start': start_date if start_date else (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'end': end_date if end_date else datetime.now().strftime('%Y-%m-%d'),
        "include_content": True
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    return response.json().get('news', []) if response.status_code == 200 else []

def clean_data(contents):
    TAG_RE = re.compile(r'<[^>]+>')
    contents = TAG_RE.sub('', contents)
    contents = group_broken_paragraphs(contents)
    contents = clean_non_ascii_chars(contents)
    contents = clean_extra_whitespace(contents)
    return contents

def add_to_chromadb(contents):
    collection_name = "finance"
    collection_status = False
    while not collection_status:
        try:
            collection = db.get_or_create_collection(name=collection_name)
            collection_status = True
        except Exception as e:
            pass
    results = collection.query(query_texts=[contents], n_results=2)
    match_list = [d for d in results['distances'][0] if np.abs(d) < 0.0001]
    
    if not match_list:
        embeddings_sent = model([contents])
        result_ids = sorted([int(re.search(r'\d+', item).group()) for item in collection.get()['ids']])
        final_id = 'ID1' if not result_ids else "ID" + str(result_ids[-1] + 1)
        collection.add(embeddings=embeddings_sent, documents=[contents], ids=[final_id])
    return True

def query_data(collection, question):
    return collection.query(query_texts=[question], n_results=5)['documents']

def send_to_kafka(data):
    collection_name = "finance"
    collection = db.get_or_create_collection(collection_name)
    data['context'] = query_data(collection, data['question'])
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send('data_collection', data)
    producer.flush()

def consume_and_process():
    print("batch pipeline is up")
    consumer = KafkaConsumer(
        'gradio_events',
        bootstrap_servers='kafka:9093',
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        group_id='gradio-events-group',
        value_deserializer=lambda x: x.decode('utf-8'),
        session_timeout_ms=30000,          # Set the session timeout to 30 seconds
        max_poll_interval_ms=300000 
    )
    
    for message in consumer:
        try:
            db = chromadb.HttpClient(host="chroma", port=8000, settings=Settings(allow_reset=True, anonymized_telemetry=False))
            data = ast.literal_eval(message.value)
            print(f"Message consumed: {data}")
            
            # Fetch and process news data
            ticker = ['*']
            news_data = fetch_alpaca_news(ticker, limit=10)
            if news_data:
                news_df = pd.DataFrame(news_data)
                news_df['clean_data'] = news_df['content'].apply(clean_data)
                news_df['clean_data'].apply(add_to_chromadb)
                
                # Send the processed input data to the next Kafka topic
                send_to_kafka(data)
            else:
                print("No news data available.")
            
            # Commit the offset after successful processing
            consumer.commit()

        except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == '__main__':
    consume_and_process()
