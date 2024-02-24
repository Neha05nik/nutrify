import cohere
import streamlit as st

COHERENCE_API_KEY = st.secrets["COHERENCE_API_KEY"]

def small_to_big(collection, documents):
    """
    Return full documents after first extraction
    args:
        collection: The collection we use
        documents: documents that were extracted with the first step
    """
    
    # We extract the PmID from the documents
    PmID_full_sources = [document.metadata.get("PmID") for document in documents]
    
    # We eliminate duplicatas
    PmID_full_sources = list(set(PmID_full_sources))
    
    # To store the new documents
    full_documents = []
    
    # We look through the PmIDs
    for article_PmID in PmID_full_sources:
        # We retrieve all documents linked to the PmID
        chunk = collection.find({"metadata.PmID": article_PmID})
        # We reduce to one document with the full abstract
        
        if len(chunk['data']['documents']) > 1:
            chunk = reduce_document(chunk)
        
        # We extend the full_documents
        full_documents.append(chunk)

    return full_documents
        
def return_abtracts_from_documents(documents):
    """
    We return the abstracts in a list
    """
    try:
        return [document.page_content for document in documents]
    except:
        try:
            return documents.page_content
        except:
            try:
                return [doc['content'] for document in documents for doc in document['data']['documents']]
            except:
                try:
                    return [document['content'] for document in documents['data']['documents']]
                except:
                    return []
                
def return_pmids_from_documents(documents):
    """
    We return the abstracts in a list
    """
    try:
        return [document.metadata.get("PmID") for document in documents]
    except:
        try:
            return documents.metadata.get("PmID")
        except:
            try:
                return [doc['metadata']['PmID'] for document in documents for doc in document['data']['documents']]
            except:
                try:
                    return [document['metadata']['PmID'] for document in documents['data']['documents']]
                except:
                    return []                

        
def return_abtracts_from_documents_with_metadata(documents):
    """
    We return the abstracts in a list with title and year of publication
    """
    try:
        return [f"""Title: {document.metadata.get('Title')}
            Publication date: {document.metadata.get('Publication_Date')}
            Abstract: {document.page_content}""" for document in documents]
    except:
        try:
            return [f"""Title: {documents.metadata.get('Title')}
            Publication date: {documents.metadata.get('Publication_Date')}
            Abstract: {documents.page_content}"""]
        except:
            return []
        
def in_case_duplicates(documents):
    """
    To eliminate duplicates, we use the abstract
    Not needed anymore, database shouldn't have any duplicates now
    """
    
    chunks_clean = []
    for chunk in documents:
        if return_abtracts_from_documents(chunk) not in return_abtracts_from_documents(chunks_clean):
            chunks_clean.append(chunk)
    
    return chunks_clean

def reduce_document(documents):
    """
    To combine abstracts from the same PmID
    """
    # We use the first chunks as the base line
    clean_chunk = {'data':{'documents':[documents['data']['documents'][0]]}}
    
    # We extract all the chunks abstracts
    abstracts = return_abtracts_from_documents(documents)
    
    # We modify the abstract with the concatenate version
    clean_chunk['data']['documents'][0]['content'] = ','.join(abstracts)
        
    # We return it
    return clean_chunk

def reranker_abstracts(query, documents, th=0.1, k=None):
    """
    We rerank the abstracts. 
    It can improve the selection of pertinent texts
    """
    
    # init client
    co = cohere.Client(COHERENCE_API_KEY)
    
    # We extract the abstracts
    abstracts = return_abtracts_from_documents(documents)

    k = k if k else len(abstracts)
    
    rerank_docs = co.rerank(
        query=query, 
        documents=abstracts, 
        top_n=k, 
        model="rerank-english-v2.0"
    )
    
    # To store the new re ranked document
    reranked_documents = []
    
    # We loop through the document
    for re_rank_files in rerank_docs:
        
        # If superior to the threshold we keep it
        if re_rank_files.relevance_score > th:
            reranked_documents.append(documents[re_rank_files.index])
    
    # We return the reranked documents
    return reranked_documents