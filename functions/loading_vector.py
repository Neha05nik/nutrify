import streamlit as st
from langchain_community.vectorstores import AstraDB
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

try:
    ASTRA_API_ENDPOINT = st.secrets["ASTRA_API_ENDPOINT"]
    ASTRA_TOKEN = st.secrets["ASTRA_TOKEN"]
    HF_API_KEY = st.secrets["HF_API_KEY"]
    ASTRA_COLLECTION  =  st.secrets["ASTRA_COLLECTION"]
except Exception as e:
    print(e)

# Cache the Astra DB Vector Store for future runs
@st.cache_resource(show_spinner='Loading of the database')
def load_vector_store():
    
    vector_store = AstraDB(
    #embedding=OpenAIEmbeddings(),
    # We use the embeddings
    embedding=HuggingFaceInferenceAPIEmbeddings(
            api_key=HF_API_KEY, 
            model_name="sentence-transformers/all-MiniLM-l6-v2"),
    collection_name=ASTRA_COLLECTION,
    api_endpoint=ASTRA_API_ENDPOINT,
    token=ASTRA_TOKEN)

    return vector_store

vector_store = load_vector_store()

# Cache the Retriever for future runs
@st.cache_resource(show_spinner='Getting retriever')
def load_retriever():
   # Get the retriever for the Chat Model
   retriever = vector_store.as_retriever(
       search_kwargs={"score_threshold": 0.5, "k": 10}
   )
   return retriever

retriever = load_retriever()