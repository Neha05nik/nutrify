import random
import boto3
import json
from datetime import datetime

# Function to generate a random number between 1 and 10^12
def generate_random_number():
    return random.randint(1, 10**12)

# Function to upload logs to S3 bucket
def upload_to_s3(bucket_name, key, data):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data))

# Function to append a new question/answer to the logs and the informations on the selected bot
def append_to_logs(logs, user, chatbot, engine, ai_persona, ai_type_answer):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append({'timestamp': timestamp, 
                 'user': user, 
                 'chatbot': chatbot, 
                 'engine': engine,
                 'persona': ai_persona,
                 'type_answer':ai_type_answer})
