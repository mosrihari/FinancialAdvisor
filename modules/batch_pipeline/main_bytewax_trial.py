from datetime import timedelta, datetime
from bytewax.dataflow import Dataflow
from bytewax.inputs import Input, DynamicInput, StatelessSource
from bytewax.outputs import Output, DynamicOutput
from bytewax.connectors.stdio import StdOutput
from typing import List
import requests
import json
from collections import defaultdict
from unstructured.cleaners.core import (
    clean_extra_whitespace, 
    clean_non_ascii_chars,
    group_broken_paragraphs
)
from unstructured.partition.html import partition_html
import re
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from datetime import datetime, timedelta


API_KEY = 'PKNA9BZKOZCJQCEFT1NR'
SECRET = 'IaJMEQzWTbUqLLpf20JfoomceBMJoQvkGiEKYQ8Q'
db = chromadb.PersistentClient(path=r"D:\Raghu Studies\FinancialAdvisor\chroma_dir")
model_name = "all-MiniLM-L6-v2"
model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name)

# python -m bytewax.run
def split_date_range(from_date, to_date, num_intervals):
    # Convert input strings to datetime objects
    from_date = datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.strptime(to_date, '%Y-%m-%d')
    
    # Calculate total number of days between from_date and to_date
    total_days = (to_date - from_date).days
    
    # Calculate the number of days per interval
    days_per_interval = total_days / num_intervals
    
    # Initialize list to store result tuples
    result = []
    
    # Generate intervals
    for i in range(num_intervals):
        # Calculate start and end dates for the current interval
        start_date = from_date + timedelta(days=int(i * days_per_interval))
        end_date = from_date + timedelta(days=int((i + 1) * days_per_interval))
        
        # Append tuple (start_date, end_date) to the result list
        result.append((start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    
    return result

class AlpacaBatch(DynamicInput):
    def __init__(self, from_date, to_date, ticker):
        self.from_date = from_date
        self.to_date = to_date
        self.ticker = ticker 
        self.api_key = API_KEY
        self.secret = SECRET
        self.url = "https://data.alpaca.markets/v1beta1/news"

    def build(self, worker_index, worker_count):
        worker_date_range = split_date_range(self.from_date, self.to_date, worker_count)
        current_from_date, current_to_date = worker_date_range[worker_index] # current wormer's value
        return AlpacaBatchInput(self.url, current_from_date, current_to_date, self.ticker)

class AlpacaBatchInput(StatelessSource):
    def __init__(self, url, current_from_date, current_to_date, ticker):
        self.url = url
        self.current_from_date = current_from_date
        self.current_to_date = current_to_date
        self.ticker = ticker
        self.alpaca_client = build_alpaca_client(self.url, self.current_from_date, 
                                                 self.current_to_date, self.ticker)
    
    def next(self):
        return self.alpaca_client.list()

def build_alpaca_client(url, current_from_date, current_to_date, ticker):  
    headers = {
                    "accept": "application/json",
                    "APCA-API-KEY-ID": API_KEY,
                    "APCA-API-SECRET-KEY": SECRET
                }
    params = {
        "start": current_from_date,
        "end"  : current_to_date,
        "symbols": ticker,
        "include_content": True,
        "limit": 50
    }
    return AlpacaClient(url, headers, params)

class AlpacaClient:
    def __init__(self, url, headers, params):
        self.url = url
        self.headers = headers
        self.params = params
        self._page_token = None

    def list(self):
        self.params['page_token'] = self._page_token
        response = requests.get(self.url, headers=self.headers, params=self.params)
        
        next_page_token = None
        if response.status_code == 200:  # Check if the request was successful
            # parse response into json
            news_json = response.json()

            # extract next page token (if any)
            next_page_token = news_json.get("next_page_token", None)

        else:
            print(f"Request failed with status code: {response.status_code}")

        self._page_token = next_page_token

        return news_json["news"]

def build_input(ticker) -> Input:
    get_current_date = datetime.today()
    get_past_date = get_current_date - timedelta(days=90)
    to_date = datetime.strftime(get_current_date, "%Y-%m-%d")
    from_date = datetime.strftime(get_past_date, "%Y-%m-%d")
    print(ticker)
    return AlpacaBatch(from_date, to_date, ticker)

def get_messages(messages):
    # Number of messages retrieved is 50
    message_content = []
    for message in messages:
        message_content.append(message['content'])
    return message_content

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
    return None

#def flow_builder(ticker):
ticker = ['MSFT']
flow = Dataflow()
flow.input("input", build_input(ticker))
flow.flat_map(lambda messages: get_messages(messages))
flow.map(lambda messages: clean_data(messages))
flow.map(lambda messages: add_to_chromadb(messages))
messages = flow.output("output",StdOutput())
#    return flow

# if __name__ == "__main__":
#     flow = flow_builder()
#     print("Success")
    

