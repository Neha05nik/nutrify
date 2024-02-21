import streamlit as st
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain_openai import ChatOpenAI
from langchain_mistralai.chat_models import ChatMistralAI

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    HF_API_KEY = st.secrets["HF_API_KEY"]
    MISTRAL_API_KEY  =  st.secrets["MISTRAL_API_KEY"]

except Exception as e:
    print(e)
    

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
   return ChatMistralAI(model='mistral-tiny', 
                        temperature=0.4,
                        mistral_api_key=MISTRAL_API_KEY)

# Cache Mistral Chat Model small for future runs
@st.cache_resource()
def load_Mistral_SMALL():
   return ChatMistralAI(model='mistral-small', 
                        temperature=0.4,
                        mistral_api_key=MISTRAL_API_KEY)

