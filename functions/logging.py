import random
import boto3
import json
from datetime import datetime

# Function to generate a random number between 1 and 10^12
def generate_random_number():
    return random.randint(1, 10**12)

# Function to upload logs to S3 bucket
def upload_to_s3(bucket_name, key, data, check_number = False):
    s3 = boto3.client('s3')
    if check_number:
        print(key[:-5] + "/")
        print(len(s3.list_objects_v2(Bucket=bucket_name, Prefix=key[:-5] + "/")))
        print(s3.list_objects_v2(Bucket=bucket_name, Prefix=key[:-5] + "/"))
    
    #s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data))

# Function to upload logs to S3 bucket
def upload_bug_to_s3(bucket_name, error):
    s3 = boto3.client('s3')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    key = f'logs/errors/{timestamp}.json'
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(error))

# Function to append a new question/answer to the logs and the informations on the selected bot
def append_to_logs(logs, user, chatbot, engine, ai_persona, ai_type_answer):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append({'timestamp': timestamp, 
                 'user': user, 
                 'chatbot': chatbot, 
                 'engine': engine,
                 'persona': ai_persona,
                 'type_answer':ai_type_answer})
