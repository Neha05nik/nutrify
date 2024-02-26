import random
import boto3
import json
from datetime import datetime

# Function to generate a random number between 1 and 10^12
def generate_random_number():
    return random.randint(1, 10**12)

# Function to upload logs to S3 bucket
def upload_to_s3(bucket_name, key, data, check_number = False, new_conversation = False):
    s3 = boto3.client('s3')
    if check_number:
        # Get the list of the S3_folder
        list_s3 = s3.list_objects_v2(Bucket=bucket_name, Prefix=f'{key}/')
        # We get the number of files in the folder with the key KeyCount
        len_list_s3 = list_s3['KeyCount']

        # We increment the number if user started a new conversation
        if new_conversation:
            key = f'{key}/{len_list_s3 + 1}.json'
        else:
            key = f'{key}/{len_list_s3}.json'
    
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data))

# Function to upload bugs to S3 bucket
def upload_bug_to_s3(bucket_name, error):
    s3 = boto3.client('s3')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    key = f'logs/errors/{timestamp}.json'
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(error))

# Function to upload authorization for forgotten password to S3 bucket
def upload_reset_pwd_to_s3(bucket_name, email, token):
    s3 = boto3.client('s3')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {'email':email, 'token':token, 'timestamp':timestamp}
    key = f'authorized_changes/modification_pwd.json'
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data))

# Function to retrieve the content of the authorized email/token to reinitialize the pwd
def retrieve_authorized_pwd_change(bucket_name):
    try:
        s3 = boto3.client('s3')
        key = f'authorized_changes/modification_pwd.json'
        response = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        file_content = json.loads(file_content)
        authorized_emails = file_content['email']
        authorized_token = file_content['token']
        authorized_timestamp = file_content['timestamp']

        return authorized_emails, authorized_token, authorized_timestamp

    except Exception as e:
        print(e)
        return None, None, None

# Function to append a new question/answer to the logs and the informations on the selected bot
def append_to_logs(stock_messages, user, chatbot, engine, ai_persona):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stock_messages.append({'timestamp': timestamp, 
                 'user': user, 
                 'chatbot': chatbot, 
                 'engine': engine,
                 'persona': ai_persona})
    
def loading_s3_conversations(bucket_name, user_key):
    s3 = boto3.client('s3')
    # Get the list of the S3_folder
    list_s3 = s3.list_objects_v2(Bucket=bucket_name, Prefix=f'{user_key}/')
    # We get the number of files in the folder with the key KeyCount
    len_list_s3 = list_s3['KeyCount']
    # To store the conversations
    conversation_list = []
    if len_list_s3 > 0:
        for i in range(1, len_list_s3 + 1):
            response = s3.get_object(Bucket=bucket_name, Key=f'{user_key}/{i}.json')
            file_content = response['Body'].read().decode('utf-8')
            conversation_list.append(json.loads(file_content))
        
        return conversation_list
    else:
        return conversation_list
    

# Return the conversation
def return_conversation(conversations): 
    conversation = []
    for conv in conversations:
        conversation.append({"role": "human", "content": conv['user']})
        conversation.append({"role": "ai", "content": conv['chatbot']})
    return conversation

# Return the list of user's question in the current conversation
def return_questions(conversation):
    return [message['content'] for message in conversation if message['role']=='human']

# Return the timestamp
def return_dates(conversations): 
    dates = []
    for date in conversations:
        dates.append(date['timestamp'])
    return dates

def return_time_difference(timestamp_str, delta):
    # Convert the timestamp string to a datetime object
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

    # Get the current time
    current_time = datetime.now()

    # Calculate the time difference
    time_difference = current_time - timestamp

    # Return the delta based on the input
    if delta == 'days':
        delta_difference = time_difference.days
    elif delta == 'minutes':
        delta_difference = time_difference.total_seconds() / 60
    else:
        raise ValueError("Invalid delta parameter. Use 'days' or 'minutes'.")

    return delta_difference