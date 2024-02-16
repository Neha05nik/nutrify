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


# Cache HuggingFace Chat Model for future runs
@st.cache_resource()
def load_chat_model_HF():
   return ChatHuggingFace(llm=HuggingFaceHub(
    huggingfacehub_api_token=HF_API_KEY, 
    repo_id="HuggingFaceH4/zephyr-7b-beta", # Name of the repo
    task="text-generation",
    model_kwargs={
        "max_new_tokens": 4096,
        "top_k": 50,
        "temperature": 0.4,
        "repetition_penalty": 1.03,
    },
    ), huggingfacehub_api_token=HF_API_KEY)
#chat_model = load_chat_model_HF()

# Cache Mistral Chat Model for future runs
@st.cache_resource()
def load_client_mistral():
   return MistralClient(api_key=MISTRAL_API_KEY)
