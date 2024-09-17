import gradio as gr
import nltk
#nltk.download()
from nltk.tokenize import word_tokenize
from kafka import KafkaProducer
import json


question_words = ["what", "why", "when", "where", 
             "name", "is", "how", "do", "does", 
             "which", "are", "could", "would", 
             "should", "has", "have", "whom", "whose", "don't"]
chat_dict = {}
merged_prompt = "ABOUT_ME:{}QUESTION:{}CONTEXT:{}"

def check_question(question):
    question = question.lower()
    question = word_tokenize(question)
    if any(x in question for x in question_words):
        return 1
    else:
        return 0
    

def send_to_kafka(data):
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    producer.send('gradio_events', data)
    producer.flush()

def respond_chat(message, history):
    
    if "about_me" not in chat_dict.keys():
        chat_dict["about_me"] = message
    else:
        chat_dict["question"] = message
    is_question = check_question(message)
    if is_question:
        send_to_kafka(chat_dict)
        return "Check VSCODE"
    else:
        return "Ask question about where you want to invest"

iface = gr.ChatInterface(respond_chat)
iface.launch()