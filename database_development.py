# Importing libraries
from NCBI_retriever import perform_esearch_ids, perform_efetch_abstracts
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import AstraDB
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate

# Credit to https://github.com/gkamradt/langchain-tutorials/blob/main/data_generation/ for helping on summerization

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ASTRA_API_ENDPOINT = st.secrets["ASTRA_API_ENDPOINT"]
    ASTRA_TOKEN = st.secrets["ASTRA_TOKEN"]
    NCBI_API_KEY = st.secrets["NCBI_API_KEY"]
except:
    # For local use
    from configs import *

# Initialize session state
if 'add_second_query' not in st.session_state:
    st.session_state.add_second_query = False

if 'abstract_to_push' not in st.session_state:
    st.session_state.abstract_to_push = []
elif 'abstract_to_push' in st.session_state:
    st.session_state.abstract_to_push = st.session_state.abstract_to_push

if 'publication_abstracts' not in st.session_state:
    st.session_state.publication_abstracts = []
elif 'publication_abstracts' in st.session_state:
    st.session_state.publication_abstracts = st.session_state.publication_abstracts
    
if 'clicked_added' not in st.session_state:
    st.session_state.clicked_added = False
    
if 'clicked_searched' not in st.session_state:
    st.session_state.clicked_searched = False
    
if 'generated_summary_button' not in st.session_state:
    st.session_state.generated_summary_button = False
    
if 'validated_credential' not in st.session_state:
    st.session_state.validated_credential = False
elif st.session_state.validated_credential:
    st.session_state.validated_credential = True

if OPENAI_API_KEY:
    st.session_state.key_1 = OPENAI_API_KEY
else:
    if 'key_1' not in st.session_state:
        st.session_state.key_1 = None
    else:
        st.session_state.key_1 = st.session_state.key_1 
if ASTRA_API_ENDPOINT :
    st.session_state.key_3 = ASTRA_API_ENDPOINT
else:
    if 'key_3' not in st.session_state:
        st.session_state.key_3 = None
    else:
        st.session_state.key_3 = st.session_state.key_3
if ASTRA_TOKEN:
    st.session_state.key_4 = ASTRA_TOKEN
else:
    if 'key_4' not in st.session_state:
        st.session_state.key_4 = None
    else:
        st.session_state.key_4 = st.session_state.key_4 

if 'key_2' not in st.session_state:
    st.session_state.key_2 = None
else:
    st.session_state.key_2 = st.session_state.key_2 

# Declare a function to retrieve abstracts and cache the result
@st.cache_data(show_spinner='Searching for the articles')
def get_abstracts(query, nb_article):
    # Perform ESearch to get publication IDs
    publication_ids, web_key = perform_esearch_ids(query, NCBI_API_KEY, sort_by="relevance", retmax=nb_article)

    st.sidebar.text(f"Number of publications found: {len(publication_ids)}")

    # Perform EFetch for abstracts
    return perform_efetch_abstracts(publication_ids, query, web_key, NCBI_API_KEY)

@st.cache_data(show_spinner='Preparing corpus into chunks')
def preparation_corpus(corpus):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

    # We prepare the document into chunks
    documents = splitter.create_documents(corpus)
    document_chunks = splitter.split_documents(documents)

    return document_chunks

# Cache the Astra DB Vector Store for future runs
@st.cache_resource(show_spinner='Connecting to AstraDB')
def load_vector_store(astra_key, astra_token, collection):
    # Connect to the Vector Store
    vector_store = AstraDB(
        embedding=OpenAIEmbeddings(),
        collection_name=collection,
        api_endpoint=astra_key,
        token=astra_token
    )
    return vector_store

# Cache prompt for future runs
@st.cache_resource()
def load_summarize_prompt():

    llm = OpenAI(temperature=0.3, 
                 openai_api_key=st.session_state.key_1)

    map_prompt = """
    Write a concise summary of the following:
    "{text}"
    CONCISE SUMMARY:
    """
    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])


    combine_prompt = """
    You will be given a series of abstracts of multiple scientific articles in the same field.
    The abstracts will be enclosed in triple backquotes.
    Your goal is to give a extensive summary of the subject.
    The summary should be comprehensible to someone outside of the field.
    Return your response in bullet points which covers the key points of the text.
    ```{text}```
    BULLET POINT SUMMARY:
    """
    combine_prompt_template = PromptTemplate(template=combine_prompt, input_variables=["text"])

    summary_chain = load_summarize_chain(llm=llm,
                                     chain_type='map_reduce',
                                     map_prompt=map_prompt_template,
                                     combine_prompt=combine_prompt_template
                                    )
    return summary_chain

summary_chain = load_summarize_prompt()

@st.cache_data(show_spinner='It is generating a summery...')
def generate_summary(texts_to_summarize):

    # We join the documents into a single one
    prepared_documents = ''.join(texts_to_summarize)

    # Create the text splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1500, chunk_overlap = 100)
    docs = text_splitter.create_documents([prepared_documents])
    
    # We call GPT3.5 customed to our prompt
    summery = summary_chain.invoke(docs)

    # We return the summery
    return summery['output_text']

# Sidebar for user input
st.sidebar.header('Retrieve articles from NCBI database')

# Sidebar for user input
st.sidebar.header('Article Search')
word = st.sidebar.text_input('Enter a query MeSH (e.g., "polyphenols")')

# Checkbox for adding the second query
add_second_query = st.sidebar.checkbox('Add a second query')

# Input for the second query, visible only when the checkbox is selected
if add_second_query:
    word2 = st.sidebar.text_input('Enter a second MeSH query (e.g., "microbiota")')

# Number of articles to retrieve
nb_article = st.sidebar.slider('Number of articles to extract', min_value=10, max_value=200, value = 50)

# Button to trigger the search
if st.sidebar.button('Search Articles'):
    
    st.session_state.clicked_searched = True
    st.session_state.generated_summary_button = False
    
    # Construct the query based on user input
    if add_second_query and 'word2' in locals():
        query = f'{word}[mesh]+AND+{word2}[mesh]'
    else:
        query = f'{word}[mesh]'

    st.session_state.publication_abstracts = get_abstracts(query, nb_article)

    st.session_state.abstract_to_push.extend(st.session_state.publication_abstracts)

    # To eliminate redundant abstracts
    st.session_state.abstract_to_push = list(set(st.session_state.abstract_to_push))

if st.session_state.clicked_searched:
    # Display retrieved abstracts
    st.header('Search Results')    

    # We invoke the llm model to do a summary of the abstracts
    if st.button('Generate a summary'):

        st.session_state.generated_summary_button = True
        
        st.session_state.generated_summary = generate_summary(st.session_state.publication_abstracts)

    # We display the generated summary
    if st.session_state.generated_summary_button:
         st.markdown(st.session_state.generated_summary)

    for i, abstract in enumerate(st.session_state.publication_abstracts):
        st.subheader(f"Abstract {i + 1}")
        st.text(abstract)

if len(st.session_state.abstract_to_push) > 0:

    # Button to push the abstracts to the database
    if st.sidebar.button('Push articles to Astradatabase') or st.session_state.clicked_added:
        st.session_state.clicked_added = True

        # Check if all keys have non-empty values
        if st.session_state.key_1 and st.session_state.key_2 and st.session_state.key_3 and st.session_state.key_4 and st.session_state.validated_credential:

            # We prepare the corpus before sending to AstraDatabase
            prepared_documents = preparation_corpus(st.session_state.abstract_to_push)

            # We load the vector
            vector_store = load_vector_store(st.session_state.key_3, st.session_state.key_4, st.session_state.key_2)

            vector_store.add_documents(prepared_documents)

            st.session_state.abstract_to_push = []

            st.sidebar.text("Articles pushed to AstraDatabase")

            st.session_state.clicked_added = False
        else:
            st.session_state.validated_credential = False
            st.sidebar.text("Please enter values for all keys before pushing to AstraDatabase.")

        if st.session_state.validated_credential == False:

            # Update the session state with the new API key
            st.session_state.key_1 = st.sidebar.text_input('Enter OPENAI_API_KEY', value=st.session_state.key_1)
            st.session_state.key_2 = st.sidebar.text_input('Enter collection_name', value=st.session_state.key_2)
            st.session_state.key_3 = st.sidebar.text_input('Enter ASTRA_API_ENDPOINT', value=st.session_state.key_3)
            st.session_state.key_4 = st.sidebar.text_input('Enter ASTRA_TOKEN', value=st.session_state.key_4)

            if st.sidebar.button('Validate credentials'):
                st.session_state.validated_credential = True
                st.session_state.clicked_added = False
                
    else:
        st.sidebar.write(f"Number of articles that will be push: {len(st.session_state.abstract_to_push)}")


