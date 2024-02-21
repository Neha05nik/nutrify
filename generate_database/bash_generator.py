# Importing libraries
from NCBI_retriever import perform_esearch_ids, perform_efetch_abstracts
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import AstraDB
from langchain.chains.summarize import load_summarize_chain
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.prompts import PromptTemplate
import pandas as pd

"""
def get_articles(query, nb_article):
    # Perform ESearch to get publication IDs
    publication_ids, web_key = perform_esearch_ids(query, NCBI_API_KEY, sort_by="relevance", retmax=nb_article)

    st.sidebar.text(f"Number of publications found: {len(publication_ids)}")

    # Perform EFetch for abstracts
    articles_informations = perform_efetch_abstracts(publication_ids, web_key, NCBI_API_KEY)

    df = pd.concat([pd.DataFrame(publication_ids, columns=['PmID']), 
          pd.DataFrame(articles_informations, columns=['Abstract', 'Title', 'Publication_Date', 'Authors', 'Journal', 'DOI'])], axis = 1)

    return df

@st.cache_data(show_spinner='Preparing corpus into chunks')
def preparation_corpus(df_corpus):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

    metadatas_columns = [col for col in df_corpus.columns if col != 'Abstract']

    # We prepare the document into chunks
    documents = splitter.create_documents(
        df_corpus['Abstract'],
        metadatas=df_corpus[metadatas_columns].to_dict('records'))

    document_chunks = splitter.split_documents(documents)

    return document_chunks

# Cache the Astra DB Vector Store for future runs
@st.cache_resource(show_spinner='Connecting to AstraDB')
def load_vector_store(astra_key, astra_token, collection, embedding_type):

    # Selection of the embedding
    # Difference in the dimension's size
    if embedding_type == "OpenAi": #1536 dimensions
        embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")
    elif embedding_type == "all-MiniLM-l6-v2": #384 dimensions
        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=HF_API_KEY, 
            model_name="sentence-transformers/all-MiniLM-l6-v2")

    # Connect to the Vector Store
    vector_store = AstraDB(
        embedding=embeddings,
        collection_name=collection,
        api_endpoint=astra_key,
        token=astra_token
    )
    return vector_store

# Construct the query based on user input
def is_list_words(word_test):
    return word_test.startswith('[') and word_test.endswith(']')
def update_articles(query, nb_article):
    st.session_state.df_articles = get_articles(query, nb_article)

    st.session_state.df_articles['query'] = query
    
    st.session_state.df_articles_to_push = pd.concat([st.session_state.df_articles_to_push, 
                                                        st.session_state.df_articles]
                                                        ).drop_duplicates(['Abstract'], keep='first')


    # Construct the query based on user input
if add_second_query and 'word2' in locals():
    if is_list_words(word):
        list_word = word[1:-1].split(',')
    else:
        list_word = [word]

    if is_list_words(word2):
        list_word2 = word2[1:-1].split(',')
    else:
        list_word2 = [word2]

    for w in list_word:
        for w2 in list_word2:
            query = f'{w}[mesh]+AND+{w2}[mesh]'
            update_articles(query, nb_article)
    # Debugging purpose
    print(list_word, list_word2)

else:
    if is_list_words(word):
        list_word = word[1:-1].split(',')
    else:
        list_word = [word]

    for w in list_word:
        query = f'{w}[mesh]'
        update_articles(query, nb_article)

"""

try:
    from configs import *
except:

    #Prompt the user to enter API keys and other information
    OPENAI_API_KEY = input("Enter your OpenAI API key: ")
    ASTRA_API_ENDPOINT = input("Enter your Astra API endpoint: ")
    ASTRA_TOKEN = input("Enter your Astra token: ")
    NCBI_API_KEY = input("Enter your NCBI API key: ")
    HF_API_KEY = input("Enter your Hugging Face API key: ")

print("Connect to the database")
