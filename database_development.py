# Importing libraries
#from importlib import metadata
from NCBI_retriever import perform_esearch_ids, perform_efetch_abstracts
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import AstraDB
from langchain.chains.summarize import load_summarize_chain
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.prompts import PromptTemplate
import pandas as pd

# Credit to https://github.com/gkamradt/langchain-tutorials/blob/main/data_generation/ for helping on summerization

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ASTRA_API_ENDPOINT = st.secrets["ASTRA_API_ENDPOINT"]
    ASTRA_TOKEN = st.secrets["ASTRA_TOKEN"]
    NCBI_API_KEY = st.secrets["NCBI_API_KEY"]
    HF_API_KEY = st.secrets["HF_API_KEY"]

except:
    # For local use
    from configs import *

# Initialize session state
if 'add_second_query' not in st.session_state:
    st.session_state.add_second_query = False

if 'df_articles_to_push' not in st.session_state:
    st.session_state.df_articles_to_push = pd.DataFrame()
elif 'df_articles_to_push' in st.session_state:
    st.session_state.df_articles_to_push = st.session_state.df_articles_to_push

if 'df_articles' not in st.session_state:
    st.session_state.df_articles = pd.DataFrame()
elif 'df_articles' in st.session_state:
    st.session_state.df_articles = st.session_state.df_articles
    
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

if 'embedding_type' not in st.session_state:
    st.session_state.embedding_type = False
else:
    st.session_state.embedding_type = st.session_state.embedding_type

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
if HF_API_KEY:
    st.session_state.key_5 = HF_API_KEY
else:
    if 'key_5' not in st.session_state:
        st.session_state.key_5 = None
    else:
        st.session_state.key_4 = st.session_state.key_4 

if 'key_2' not in st.session_state:
    st.session_state.key_2 = None
else:
    st.session_state.key_2 = st.session_state.key_2 

# Declare a function to retrieve articles and cache the result
@st.cache_data(show_spinner='Searching for the articles')
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
        embeddings = OpenAIEmbeddings()
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

# Cache prompt for future runs
@st.cache_resource()
def load_summarize_prompt():

    #if embedding_type == "OpenAI":
    llm = OpenAI(temperature=0.3, 
        openai_api_key=st.session_state.key_1)
    #elif embedding_type == "zephyr-7b-beta":
        #from langchain_community.llms import HuggingFaceHub
    #    llm = HuggingFaceHub(
     #       huggingfacehub_api_token=HF_API_KEY, 
      #      repo_id="HuggingFaceH4/zephyr-7b-beta", # Name of the repo
       #     task="text-generation",
        #    model_kwargs={
         #       "max_new_tokens": 512,
          #      "top_k": 5,
           #     "temperature": 0.3,
            #    "repetition_penalty": 1.03,
            #},
        #)

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
word = st.sidebar.text_input('Enter a query MeSH (e.g., "polyphenols")', 
                             help="For bulk search of several topic, write [polyphenols,catechin]")

# Checkbox for adding the second query
add_second_query = st.sidebar.checkbox('Add a second query', 
                             help="For bulk search of several topic, write [cancer,sport]")

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
    def is_list_words(word_test):
        return word_test.startswith('[') and word_test.endswith(']')
    def update_articles(query, nb_article):
        st.session_state.df_articles = get_articles(query, nb_article)

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


if st.session_state.clicked_searched:
    # Display retrieved abstracts
    st.header('Search Results')    

    # We invoke the llm model to do a summary of the abstracts
    if st.button('Generate a summary'):

        st.session_state.generated_summary_button = True
        
        st.session_state.generated_summary = generate_summary(list(st.session_state.df_articles["Abstract"]))

    # We display the generated summary
    if st.session_state.generated_summary_button:
         st.markdown(st.session_state.generated_summary)

    for i, abstract in enumerate(list(st.session_state.df_articles["Abstract"])):
        st.subheader(f"Abstract {i + 1}")
        st.text(abstract)

if st.session_state.df_articles_to_push.shape[0] > 0:

    # Button to push the abstracts to the database
    if st.sidebar.button('Push articles to Astradatabase') or st.session_state.clicked_added:
        st.session_state.clicked_added = True

        # Check if all keys have non-empty values
        if st.session_state.key_1 and st.session_state.key_2 and st.session_state.key_3 and st.session_state.key_4 and st.session_state.validated_credential and st.session_state.embedding_type:

            # We prepare the corpus before sending to AstraDatabase
            prepared_documents = preparation_corpus(st.session_state.df_articles_to_push)

            # We load the vector
            vector_store = load_vector_store(st.session_state.key_3, 
                                             st.session_state.key_4, 
                                             st.session_state.key_2, 
                                             st.session_state.embedding_type)

            vector_store.add_documents(prepared_documents)

            st.session_state.df_articles_to_push = pd.DataFrame()

            st.sidebar.text("Articles pushed to AstraDatabase")
            st.sidebar.write("With embedding:", st.session_state.embedding_type)

            
        else:
            st.session_state.validated_credential = False
            st.sidebar.text("Please enter values for all keys before pushing to AstraDatabase.")


        if st.session_state.validated_credential == False:
            with st.sidebar:
                # Update the session state with the new API key
                st.session_state.key_1 = st.text_input('Enter OPENAI_API_KEY', value=st.session_state.key_1)
                st.session_state.key_2 = st.text_input('Enter collection_name', value=st.session_state.key_2)
                st.session_state.key_3 = st.text_input('Enter ASTRA_API_ENDPOINT', value=st.session_state.key_3)
                st.session_state.key_4 = st.text_input('Enter ASTRA_TOKEN', value=st.session_state.key_4)
                #st.session_state.key_5 = st.sidebar.text_input('Enter HF_API_KEY', value=st.session_state.key_5)
                st.session_state.embedding_type = st.sidebar.selectbox('**Select an embedding strategy**', 
                                                                       ('all-MiniLM-l6-v2', 'OpenAi'))
            if st.sidebar.button('Validate credentials'):
                st.session_state.validated_credential = True
                st.session_state.clicked_added = False
                
    else:
        st.sidebar.write(f"Number of articles that will be push: {st.session_state.df_articles_to_push.shape[0]}")


