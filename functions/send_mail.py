# To send a link to reset the password
import streamlit as st
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functions.s3_files_functions import upload_reset_pwd_to_s3

try:
    SITE_EMAIL = st.secrets["SITE_EMAIL"]
    PASSWORD_EMAIL = st.secrets["PASSWORD_EMAIL"]
    S3_BUCKET_NAME  = st.secrets["S3_BUCKET"]
except Exception as e:
    print(e)

def send_email(to_email):
    # Set up the email server
    smtp_server = 'smtp.gmail.com:587'  
    sender_email = SITE_EMAIL
    sender_password = PASSWORD_EMAIL

    # Create the MIME object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = 'Reset your Password'

    # Generate a random token with 32 characters
    random_token = secrets.token_hex(16)

    upload_reset_pwd_to_s3(S3_BUCKET_NAME, to_email, random_token)

    body = f"""
        Click on the link to change your password.

        The link will expire in 5 minutes.

        http://localhost:8501/?email={to_email}&token={random_token}
    """

    msg.attach(MIMEText(body, 'plain'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
