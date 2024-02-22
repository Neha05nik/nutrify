import streamlit as st
from langchain_community.vectorstores import AstraDB
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.embeddings import VoyageEmbeddings

try:
    ASTRA_API_ENDPOINT = st.secrets["ASTRA_API_ENDPOINT"]
    ASTRA_TOKEN = st.secrets["ASTRA_TOKEN"]
    HF_API_KEY = st.secrets["HF_API_KEY"]
    ASTRA_COLLECTION_384  =  st.secrets["ASTRA_COLLECTION_384"]
    ASTRA_COLLECTION_1024  =  st.secrets["ASTRA_COLLECTION_1024"]
    VOYAGE_API_KEY = st.secrets["VOYAGE_API_KEY"]

except Exception as e:
    print(e)

# Cache the Astra DB Vector Store for future runs
@st.cache_resource(show_spinner='Loading of the database')
def load_vector_store():
    
    # We load at first the more complete model.
    try:
        vector_store = AstraDB(
        embedding=VoyageEmbeddings(voyage_api_key=VOYAGE_API_KEY),
        collection_name=ASTRA_COLLECTION_1024,
        api_endpoint=ASTRA_API_ENDPOINT,
        token=ASTRA_TOKEN)

    except:
        vector_store = AstraDB(
        # We use the embeddings, it is free of charge
        embedding=HuggingFaceInferenceAPIEmbeddings(
                api_key=HF_API_KEY, 
                model_name="sentence-transformers/all-MiniLM-l6-v2"),
        collection_name=ASTRA_COLLECTION_384,
        api_endpoint=ASTRA_API_ENDPOINT,
        token=ASTRA_TOKEN)

    return vector_store

# Cache the Retriever for future runs
@st.cache_resource(show_spinner='Getting retriever')
def load_retriever():
   # Get the retriever for the Chat Model
   # The retriever search for the k=10 best match in the vector and keep only >0.5 threshold

   retriever = vector_store.as_retriever(
       search_kwargs={"score_threshold": 0.5, "k": 10}
   )
   return retriever

# We load the vector and retriever
vector_store = load_vector_store()
retriever = load_retriever()