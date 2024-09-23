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
from chromadb.utils import embedding_functions
from kafka import KafkaProducer,KafkaConsumer
import json
import ast
import os
from dotenv import load_dotenv
load_dotenv()
# Alpaca API credentials
API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = 'https://data.alpaca.markets/v1beta1/news'
#db = chromadb.PersistentClient(path=r"D:\Raghu Studies\FinancialAdvisor\chroma_dir")
db = chromadb.Client("http://chromadb:8000")
model_name = "all-MiniLM-L6-v2"
model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name)

# Function to fetch news for a given ticker
def fetch_alpaca_news(ticker, limit=50, start_date=None, end_date=None):
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': API_SECRET
    }
    
    params = {
    #    'symbols': ticker,
        'limit': limit,
        'start': start_date if start_date else (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'end': end_date if end_date else datetime.now().strftime('%Y-%m-%d'),
        "include_content": True
    }
    
    
    response = requests.get(BASE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data['news']
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def clean_data(contents):
    TAG_RE = re.compile(r'<[^>]+>')
    contents = TAG_RE.sub('', contents)
    contents = group_broken_paragraphs(contents)
    contents = clean_non_ascii_chars(contents)
    contents = clean_extra_whitespace(contents)
    return contents

def add_to_chromadb(contents):
    collection_name = "finance"
    document = contents
    # Check if collection exists, if not create it
    collection = db.get_or_create_collection(collection_name)

    results = collection.query(
        query_texts=[contents],
        n_results=2
    )
    # checking duplicates
    match_list = [d for d in results['distances'][0] if np.abs(d) < 0.0001]
    
    if(not match_list):
        embeddings_sent = model([document])
        pattern = re.compile(r'\d+')
        result_ids = collection.get()['ids']
        # Extract numbers from each string in results
        result_ids = sorted([int(pattern.search(item).group()) for item in result_ids])
        if(len(result_ids) == 0):
            # if this is the first entry
            final_id = 'ID1'
            collection.add(embeddings=embeddings_sent, documents=[document], ids=[final_id])
        else:
            final_id = "ID"+str(result_ids[-1] + 1)
            collection.add(embeddings=embeddings_sent, documents=[document], ids=[final_id])
    else:
        pass
    return True

def query_data(collection, question): #list of list
    results = collection.query(
                    query_texts=[question],
                    n_results=5
                    )
    return results['documents']

def send_to_kafka(data):
    collection_name = "finance"
    collection = db.get_or_create_collection(collection_name)
    results = query_data(collection, data['question'])
    data['context'] = results
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    producer.send('data_collection', data)
    producer.flush()

def consume():
    consumer = KafkaConsumer(
        'gradio_events',               # Topic name
        bootstrap_servers='kafka:9093',  # Kafka broker
        auto_offset_reset='earliest',        # Start at the earliest available message
        enable_auto_commit=True,             # Automatically commit offsets
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
            break
    except:
        print("Stopping consumer...")
    consumer.close()
    return data

if __name__ == '__main__': 
    input_data = consume()       
    ticker = ['*']
    news_data = fetch_alpaca_news(ticker, limit=10)
    if news_data:
        news_df = pd.DataFrame(news_data)
        news_df['clean_data'] = news_df['content'].apply(clean_data)
        is_done = news_df['clean_data'].apply(lambda x: add_to_chromadb(x))
        send_to_kafka(input_data) 
    else:
        print("No news data")