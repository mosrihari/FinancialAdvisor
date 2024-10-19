import gradio as gr
import nltk
#nltk.download()
from nltk.tokenize import word_tokenize
from kafka import KafkaProducer
import json
import ollama
from kafka import KafkaConsumer
import ast
import time
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
    
def final_response():
    max_retries = 10
    retry_count = 0
    flag = False
    while retry_count < max_retries:
        try:
            consumer = KafkaConsumer(
            'summary',               # Topic name
            bootstrap_servers='kafka:9093',  # Kafka broker
            auto_offset_reset='earliest',        # Start at the earliest available message
            enable_auto_commit=True,             # Automatically commit offsets
            group_id='summary-group',      # Consumer group ID
            value_deserializer=lambda x: x.decode('utf-8')  # Decode message from bytes to string
            )
            for message in consumer:
                # Print consumed message
                print(f"Message consumed: {message.value} of type {type(message)} from partition {message.partition}, offset {message.offset}")
                data = message.value
                data = ast.literal_eval(data)
                print(data)
                flag = True
                break
        except:
            retry_count += 1
            print("Stopping consumer...")
            flag = False
            time.sleep(10)
        if flag:
            break
    #consumer.close()

    merged_prompt = "ABOUT_ME:{}QUESTION:{}CONTEXT:{}"
    #ollama.pull(model='mosrihari/unsloth_finance_alpaca')
    response = ollama.chat(model='mosrihari/unsloth_finance_alpaca', messages=[
            {"role": "user", "content": merged_prompt.format(
                    data['about_me'],
                    data['question'],
                    data['summary']
                )},
            ])
    return response['message']['content']

def send_to_kafka(data):
    producer = KafkaProducer(
        bootstrap_servers='kafka:9093',
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
        chat_dict.clear()
        suggestion = final_response()
        return suggestion
    else:
        return "Ask question about where you want to invest"

iface = gr.ChatInterface(respond_chat)
iface.launch(server_name="0.0.0.0", server_port=7860)