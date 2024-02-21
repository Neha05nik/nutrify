# Importing libraries
from NCBI_retriever import perform_esearch_ids, perform_efetch_abstracts
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import VoyageEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
import time
import pandas as pd


try:
    from configs import *

except:

    #Prompt the user to enter API keys and other information
    OPENAI_API_KEY = input("Enter your OpenAI API key: ")
    ASTRA_API_ENDPOINT = input("Enter your Astra API endpoint: ")
    ASTRA_TOKEN = input("Enter your Astra token: ")
    ASTRA_COLLECTION = input("Enter your AstraDB collection: ")
    NCBI_API_KEY = input("Enter your NCBI API key: ")
    HF_API_KEY = input("Enter your Hugging Face API key: ")
    VOYAGE_API_KEY = input("Enter your voyageai  API key: ")

def load_vector_store(embedding_type = "all-MiniLM-l6-v2"):

    print("Connection to the AstraDB collection:", ASTRA_COLLECTION)

    # Selection of the embedding
    # Difference in the dimension's size
    if embedding_type == "OpenAi": #1536 dimensions
        embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")
    elif embedding_type == "all-MiniLM-l6-v2": #384 dimensions
        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=HF_API_KEY, 
            model_name="sentence-transformers/all-MiniLM-l6-v2")
    elif embedding_type == "voyageai": #1024 dimensions
        embeddings = VoyageEmbeddings(voyage_api_key=VOYAGE_API_KEY)

    print("Connecting to AstraDB...")
    
    from langchain_community.vectorstores import AstraDB

    # Connect to the Vector Store
    vector_store = AstraDB(
        embedding=embeddings,
        collection_name=ASTRA_COLLECTION,
        api_endpoint=ASTRA_API_ENDPOINT,
        token=ASTRA_TOKEN
    )

    print("Connecting to AstraDB...completed")
    return vector_store


def get_pmids_db():
    from astrapy.db import AstraDB, AstraDBCollection
    # Initialize the AstraDB client
    vector_store = AstraDB(
        api_endpoint=ASTRA_API_ENDPOINT,
        token=ASTRA_TOKEN
    )

    # Access an existing collection
    collection = AstraDBCollection(collection_name=ASTRA_COLLECTION, 
                                   astra_db=vector_store)
    
    # We retrieve all documents in the database
    generator = collection.paginated_find()

    # To time the retrieval
    time_it = time.time()

    print("Retrieving the files...")
    # We store the files
    file = [doc for doc in generator]
        
    time_it = time.time() - time_it

    print(f"It took {time_it:.1f} seconds to retrieve all the files")

    # Transform to dataframe
    df_file = pd.DataFrame(file, columns=['_id', 'content', '$vector', 'metadata'])

    # Create new columns for metadata column
    df_file['PmID'] = df_file['metadata'].apply(lambda x: x['PmID'])
    df_file['Title'] = df_file['metadata'].apply(lambda x: x['Title'])
    df_file['Publication_Date'] = df_file['metadata'].apply(lambda x: x['Publication_Date'])
    df_file['Authors'] = df_file['metadata'].apply(lambda x: x['Authors'])
    df_file['Journal'] = df_file['metadata'].apply(lambda x: x['Journal'])
    df_file['DOI'] = df_file['metadata'].apply(lambda x: x['DOI'])
    df_file['Query'] = df_file['metadata'].apply(lambda x: x['query'])

    # Drop the original column metadata
    df_file = df_file.drop('metadata', axis=1)

    pmids = list(df_file.PmID.unique())

    print(f"There are {len(pmids)} uniques articles in the database")

    # We return the list of pmIDs
    return pmids

def prepare_queries(query):
    """
        Function: Return list of prepared mesh queries
        args: list of words
        return: list of words
    """
    def is_list_2_queries(word_list):
        try:
            return word_list.split(';')
        except Exception as e:
            print('Error:', e)
            return None
        
    def is_list_words(word_test):
        try:
            return word_test.startswith('[') and word_test.endswith(']')
        except Exception as e:
            print('Error:', e)
            return False
    prepared_query = []

    if is_list_words(query):
        queries = is_list_2_queries(query)
        
        # if 1 mesh word
        if len(queries) == 1:
            list_word = queries[0][1:-1].split(',')
            for w in list_word:
                prepared_query.append(f'{w}[mesh]')
        # If 2 mesh words
        elif len(queries) == 2:
            list_word = queries[0][1:-1].split(',')
            list_word2 = queries[1][1:-1].split(',')
            for w in list_word:
                for w2 in list_word2:
                    prepared_query.append(f'{w}[mesh]+AND+{w2}[mesh]')
                
        return prepared_query
    
    else:
        print("\nRewrite query to be inside '[]' \n")
        return None

def get_articles(query, nb_article=10):
    # Perform ESearch to get publication IDs
    publication_ids, web_key = perform_esearch_ids(query, NCBI_API_KEY, sort_by="relevance", retmax=nb_article)

    print(f"\nNumber of publications found: {len(publication_ids)}\n")

    # Perform EFetch for abstracts
    articles_informations = perform_efetch_abstracts(publication_ids, web_key, NCBI_API_KEY)

    df = pd.concat([pd.DataFrame(publication_ids, columns=['PmID']), 
          pd.DataFrame(articles_informations, columns=['Abstract', 'Title', 'Publication_Date', 'Authors', 'Journal', 'DOI'])], axis = 1)
    
    # We add the query to the dataframe
    df['query'] = query
    
    return df

def preparation_corpus(df_corpus, pmids):

    # we clean the df_corpus of already added documents
    clean_df_corpus = df_corpus[~df_corpus["PmID"].isin(pmids)]

    # We prepare a splitter object, that will separate the abstract into smaller texts
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)

    # We prepare the columns for the metadatas
    metadatas_columns = [col for col in clean_df_corpus.columns if col != 'Abstract']

    # We prepare the documents abstracts into chunks and metadatas
    documents = splitter.create_documents(
        clean_df_corpus['Abstract'],
        metadatas=clean_df_corpus[metadatas_columns].to_dict('records'))

    #  We split  the document into chunks
    document_chunks = splitter.split_documents(documents)

    # We return the prepared document and the list of new articles added 
    return document_chunks, list(clean_df_corpus["PmID"].unique())

# We load the vector store
vector_store = load_vector_store("voyageai")

# We retrieve the list of pmids already in the database
pmids_list = get_pmids_db()

query = ""

print("\n_____WRITE 'quit' to stop______")
print("_____Single search e.g.'[catechin]'______")
print("_____Multiple searchs e.g.'[catechin,proteins]'______")
print("_____Multiple MeSH searchs e.g.'[catechin];[microbiota]'______\n")
print("_____Another e.g.'[catechin];[microbiota,proteins]'______\n")

while(query != "quit"):
       
    query = input("\nEnter a MeSH term to search in NCBI database: ")

    if query != 'quit':
        prepared_query = prepare_queries(query)
       
        for query in prepared_query:
            print("Searching articles with this query:", query)

            # We prepare the corpus before sending to AstraDatabase
            prepared_documents, new_pmids = preparation_corpus(get_articles(query, 100), pmids_list)

            #If no new articles, we pass
            if new_pmids==0:
                continue

            #We add the new pmids to the list
            pmids_list.extend(new_pmids)

            # We add the documents to the vector store
            print("Loading documents to AstraDB...")
            vector_store.add_documents(prepared_documents, batch_size = 20)
            
            print(f"{len(new_pmids)} new articles added to AstraDB")



