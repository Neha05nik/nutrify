# To send the reset password
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    SITE_EMAIL = st.secrets["SITE_EMAIL"]
    PASSWORD_EMAIL = st.secrets["PASSWORD_EMAIL"]
except Exception as e:
    print(e)

def send_email(to_email, new_password):
    # Set up the email server
    smtp_server = 'smtp.gmail.com:587'  
    sender_email = SITE_EMAIL
    sender_password = PASSWORD_EMAIL

    # Create the MIME object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = 'Your New Password'

    # Attach the new password to the email body
    body = f'Your new password is: {new_password}'
    msg.attach(MIMEText(body, 'plain'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())