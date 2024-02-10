import boto3
import streamlit_authenticator as stauth
import yaml
import json
import io
import streamlit as st
from yaml.loader import SafeLoader

try:
    S3_BUCKET = st.secrets["S3_BUCKET"]
except Exception as e:
    print(e)

# Function to load authenticator from S3 bucket
def loading_authenticator(key):
    s3 = boto3.client('s3')

    # Download config.yaml from S3 bucket
    response = s3.get_object(Bucket=S3_BUCKET, Key=key)
    contents = response['Body'].read().decode("utf-8")

    # Load the config from the file-like object
    config = yaml.load(contents, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    return authenticator, config

# Function to save authenticator to S3 bucket
def saving_configs(config, key):
    s3 = boto3.client('s3')

    # Dump the config to a YAML-formatted string
    yaml_string = yaml.dump(config, default_flow_style=False)

    # Upload config.yaml to S3 bucket
    s3.put_object(Body=yaml_string.encode('utf-8'), Bucket=S3_BUCKET, Key=key)