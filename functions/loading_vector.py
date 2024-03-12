import streamlit as st
from functions.others import get_env

ASTRA_API_ENDPOINT = get_env("ASTRA_API_ENDPOINT")
ASTRA_TOKEN = get_env("ASTRA_TOKEN")
HF_API_KEY  =  get_env("HF_API_KEY")
ASTRA_COLLECTION_384 = get_env("ASTRA_COLLECTION_384")
ASTRA_COLLECTION_1024 = get_env("ASTRA_COLLECTION_1024")
VOYAGE_API_KEY = get_env("VOYAGE_API_KEY")

# Cache the Astra DB Vector Store for future runs
@st.cache_resource(show_spinner='Loading of the database')
def load_vector_store():

    from langchain_community.vectorstores import AstraDB
    
    # We load at first the more complete model.
    try:
        from langchain_community.embeddings import VoyageEmbeddings

        vector_store = AstraDB(
        embedding=VoyageEmbeddings(voyage_api_key=VOYAGE_API_KEY,
                                      model = "voyage-02",
                                      voyage_api_base= 'https://api.voyageai.com/v1/embeddings'),
        collection_name=ASTRA_COLLECTION_1024,
        api_endpoint=ASTRA_API_ENDPOINT,
        token=ASTRA_TOKEN)

    except:
        
        from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

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
@st.cache_resource(show_spinner='Loading retriever')
def load_retriever():
   # Get the retriever for the Chat Model
   # The retriever search for the k=10 best match in the vector and keep only >0.5 threshold

   retriever = vector_store.as_retriever(
       search_kwargs={"score_threshold": 0.5, "k": 10}
   )
   return retriever    

# Cache the collection for future runs
@st.cache_resource(show_spinner='Loading collection')
def load_collection():
    from astrapy.db import AstraDB
    from astrapy.db import AstraDBCollection

    # Initialize the client.

    astra_db = AstraDB(
        token=ASTRA_TOKEN,
        api_endpoint=ASTRA_API_ENDPOINT,
    )
    try:
        collection = AstraDBCollection(collection_name=ASTRA_COLLECTION_1024, astra_db=astra_db)
    except:
        collection = AstraDBCollection(collection_name=ASTRA_COLLECTION_384, astra_db=astra_db)
    
    return collection

# We load the vector and retriever
vector_store = load_vector_store()
retriever = load_retriever()
collection = load_collection()