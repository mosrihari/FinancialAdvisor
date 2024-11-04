import pandas as pd
import chromadb
from chromadb.config import Settings
import time
from kakfa_events import consume, send_to_kafka
from fetch_news import fetch_alpaca_news
from preprocessing import clean_data, add_to_chromadb

if __name__ == '__main__':
    while True:
        try:
            db = chromadb.HttpClient(host="chroma", port = 8000, settings=Settings(allow_reset=True, anonymized_telemetry=False))
            input_data = consume()       
            ticker = ['*']
            news_data = fetch_alpaca_news(limit=50)
            if news_data:
                news_df = pd.DataFrame(news_data)
                news_df['clean_data'] = news_df['content'].apply(clean_data)
                is_done = news_df['clean_data'].apply(lambda x: add_to_chromadb(x, db))
                send_to_kafka(db, input_data) 
            else:
                print("No news data")
            time.sleep(60)
        except:
            print("Error occured")