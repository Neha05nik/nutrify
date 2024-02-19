import streamlit as st
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain_community.llms import HuggingFaceHub
from mistralai.client import MistralClient
from langchain_openai import ChatOpenAI

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    HF_API_KEY = st.secrets["HF_API_KEY"]
    MISTRAL_API_KEY  =  st.secrets["MISTRAL_API_KEY"]

except Exception as e:
    print(e)
    

# Cache OpenAI Chat Model for future runs
@st.cache_resource()
def load_chat_model():
   return ChatOpenAI(
       openai_api_key=OPENAI_API_KEY,
       temperature=0.4,
       model='gpt-3.5-turbo',
       streaming=True,
       verbose=True
   )

# Cache OpenAI Chat Model for future runs
@st.cache_resource()
def load_OpenAI_GPT4():
   return ChatOpenAI(
       openai_api_key=OPENAI_API_KEY,
       temperature=0.4,
       model='gpt-4'
   )

# Cache Mistral Chat Model for future runs
@st.cache_resource()
def load_client_mistral():
   return MistralClient(api_key=MISTRAL_API_KEY)
