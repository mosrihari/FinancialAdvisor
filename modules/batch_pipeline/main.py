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

# Alpaca API credentials
API_KEY = ''
API_SECRET = ''
BASE_URL = 'https://data.alpaca.markets/v1beta1/news'
db = chromadb.PersistentClient(path=r"D:\Raghu Studies\FinancialAdvisor\chroma_dir")
model_name = "all-MiniLM-L6-v2"
model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name)

# Function to fetch news for a given ticker
def fetch_alpaca_news(ticker, limit=50, start_date=None, end_date=None):
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': API_SECRET
    }
    
    params = {
        'symbols': ticker,
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
    results = collection.query(
                        query_texts=["I am planning to invest in Facebook"],
                        n_results=3
                    )
    print(results)
    return collection


if __name__ == '__main__':        
    ticker = 'AAPL'
    news_data = fetch_alpaca_news(ticker, limit=10)
    if news_data:
        news_df = pd.DataFrame(news_data)
        news_df['clean_data'] = news_df['content'].apply(clean_data)
        news_df['clean_data'].apply(lambda x: add_to_chromadb(x))
        
    else:
        print("No news data")