import gradio as gr
import nltk
#nltk.download()
from nltk.tokenize import word_tokenize
from kafka import KafkaProducer
import json
import ollama
from kafka import KafkaConsumer
import ast
from pydantic import BaseModel, ValidationError

# Define the Pydantic model
class UserInput(BaseModel):
    text: str

    class Config:
        arbitrary_types_allowed = True

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
    consumer = KafkaConsumer(
    'summary',               # Topic name
    bootstrap_servers='kafka:9093',  # Kafka broker
    auto_offset_reset='earliest',        # Start at the earliest available message
    enable_auto_commit=True,             # Automatically commit offsets
    group_id='summary-group',      # Consumer group ID
    value_deserializer=lambda x: x.decode('utf-8')  # Decode message from bytes to string
    )
    try:
        for message in consumer:
            # Print consumed message
            print(f"Message consumed: {message.value} of type {type(message)} from partition {message.partition}, offset {message.offset}")
            data = message.value
            data = ast.literal_eval(data)
            break
    except:
        print("Stopping consumer...")
    consumer.close()

    merged_prompt = "ABOUT_ME:{}QUESTION:{}CONTEXT:{}"

        
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
    validated_inputs = UserInput(message)
    if "about_me" not in chat_dict.keys():
        chat_dict["about_me"] = message
    else:
        chat_dict["question"] = message
    is_question = check_question(message)
    if is_question:
        send_to_kafka(chat_dict)
        suggestion = final_response()
        return suggestion
    else:
        return "Ask question about where you want to invest"

iface = gr.ChatInterface(respond_chat)
iface.launch(server_name="0.0.0.0", server_port=7860)