import requests
from datetime import datetime, timedelta
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_API_SECRET = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = 'https://data.alpaca.markets/v1beta1/news'


# Function to fetch news for a given ticker
def fetch_alpaca_news(ticker, limit=50, start_date=None, end_date=None):
    headers = {
        'APCA-API-KEY-ID': ALPACA_API_KEY,
        'APCA-API-SECRET-KEY': ALPACA_API_SECRET
    }
    
    params = {
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
