import gradio as gr
import nltk
from nltk.tokenize import word_tokenize
from kafka import KafkaProducer, KafkaConsumer
import json
import ollama
import ast
import time

question_words = [
    "what", "why", "when", "where", "name", "is", "how", 
    "do", "does", "which", "are", "could", "would", "should", 
    "has", "have", "whom", "whose", "don't"
]
chat_dict = {}

def check_question(question):
    question = question.lower()
    question = word_tokenize(question)
    return any(x in question for x in question_words)

def final_response():
    consumer = KafkaConsumer(
        'summary',
        bootstrap_servers='kafka:9093',
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        group_id='summary-group',
        value_deserializer=lambda x: x.decode('utf-8'),
        session_timeout_ms=30000,          # Set the session timeout to 30 seconds
        max_poll_interval_ms=300000 
    )
    for message in consumer:
        data = ast.literal_eval(message.value)
        print(f"Message consumed: {data}")
        consumer.commit()  # Commit after processing
        merged_prompt = "ABOUT_ME:{}QUESTION:{}CONTEXT:{}".format(
            data['about_me'], data['question'], data['summary']
        )
        response = ollama.chat(model='mosrihari/unsloth_finance_alpaca', messages=[
            {"role": "user", "content": merged_prompt}
        ])
        return response['message']['content']  # Return once message is processed

def send_to_kafka(data):
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send('gradio_events', data)
    producer.flush()

def respond_chat(message, history):
    if "about_me" not in chat_dict:
        chat_dict["about_me"] = message
    else:
        chat_dict["question"] = message

    if check_question(message):
        send_to_kafka(chat_dict)
        chat_dict.clear()
        suggestion = final_response()
        return suggestion
    else:
        return "Ask a question about where you want to invest."

iface = gr.ChatInterface(respond_chat)
iface.launch(server_name="0.0.0.0", server_port=7860)
