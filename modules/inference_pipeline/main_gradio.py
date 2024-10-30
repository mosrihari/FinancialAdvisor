import gradio as gr
from nltk.tokenize import word_tokenize
import ollama
from kafka import KafkaConsumer
import ast
import time
from kafka_events import send_to_kafka, receive_events

question_words = ["what", "why", "when", "where", 
             "name", "is", "how", "do", "does", 
             "which", "are", "could", "would", 
             "should", "has", "have", "whom", "whose", "don't"]
chat_dict = {}

def check_question(question):
    question = question.lower()
    question = word_tokenize(question)
    if any(x in question for x in question_words):
        return 1
    else:
        return 0

def pull_ollama(data):
    merged_prompt = "ABOUT_ME:{}QUESTION:{}CONTEXT:{}"
    response = ollama.chat(model='mosrihari/unsloth_finance_alpaca', messages=[
            {"role": "user", "content": merged_prompt.format(
                    data['about_me'],
                    data['question'],
                    data['summary']
                )},
            ])
    return response['message']['content']


def respond_chat(message, history):
    
    if "about_me" not in chat_dict.keys():
        chat_dict["about_me"] = message
    else:
        chat_dict["question"] = message
    is_question = check_question(message)
    if is_question:
        send_to_kafka(chat_dict)
        chat_dict.clear()
        data = receive_events()
        suggestion = pull_ollama(data)
        return suggestion
    else:
        return "Ask question about where you want to invest"

iface = gr.ChatInterface(respond_chat)
iface.launch(server_name="0.0.0.0", server_port=7860)