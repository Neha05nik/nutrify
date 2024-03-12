import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_mistralai.chat_models import ChatMistralAI
from functions.others import get_env

OPENAI_API_KEY = get_env("OPENAI_API_KEY")
HF_API_KEY = get_env("HF_API_KEY")
MISTRAL_API_KEY  =  get_env("MISTRAL_API_KEY")

# Cache OpenAI Chat Model 3.5 for future runs
@st.cache_resource()
def load_gpt3_model():
   return ChatOpenAI(
       openai_api_key=OPENAI_API_KEY,
       temperature=0.4,
       model='gpt-3.5-turbo',
       streaming=True,
       verbose=True
   )

# Cache OpenAI Chat Model 4 for future runs
@st.cache_resource()
def load_OpenAI_GPT4():
   return ChatOpenAI(
       openai_api_key=OPENAI_API_KEY,
       temperature=0.4,
       model='gpt-4'
   )

# Cache Mistral Chat Model tiny for future runs
@st.cache_resource()
def load_Mistral_TINY():
   return ChatMistralAI(model='mistral-tiny-2312', 
                        temperature=0.4,
                        mistral_api_key=MISTRAL_API_KEY)

# Cache Mistral Chat Model small for future runs
@st.cache_resource()
def load_Mistral_SMALL():
   return ChatMistralAI(model='mistral-small-2312', 
                        temperature=0.4,
                        mistral_api_key=MISTRAL_API_KEY)

