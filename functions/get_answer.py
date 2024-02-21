from langchain.schema.runnable import RunnableMap
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from functions.retriever_abstracts import small_to_big, reranker_abstracts, return_abtracts_from_documents
from functions.generate_question import get_mistral_requery, get_openAI_requery
from functions.language_dectection import detect_language
from functions.loading_models import load_Mistral_TINY

# Streaming call back handler for responses
class StreamHandler(BaseCallbackHandler):
   def __init__(self, container, initial_text=""):
       self.container = container
       self.text = initial_text


   def on_llm_new_token(self, token: str, **kwargs):
       self.text += token
       self.container.markdown(self.text + "▌")

# Generate the answer depending of Chat Model
def get_answer(engine_AI, prompt, chat_model, vector_store, retriever, query, previous_queries, response_placeholder, language_AI):

    # We detect the language of the query
    if language_AI == "AUTO-DETECT":
        # We detect the language of the user's question
        language_query = detect_language(query)
    else:
        language_query = language_AI
        
    if engine_AI == "gpt-3.5-turbo":
        # We get a new query, generate by GPT-4 model
        query = get_openAI_requery(query)

    elif engine_AI == 'Mistral-7B-v0.2':
       # We get a new query, generate by mistral small model
       query = get_mistral_requery(query)
        
        # In case it takes too long to have an answer.
        # It helps the user to know an answer is coming
    response_placeholder.markdown("Nutritional AI is thinking about your question...▌")

    chain = prompt | chat_model

   # Retrieve relevant documents from AstraDB as context
    context = retriever.get_relevant_documents(query)

    try:
        # We search for full abtract
        full_documents = small_to_big(query, vector_store, context)
        # We rerank the documents
        reranked_documents = reranker_abstracts(query, full_documents)
        # We add metadatas
        abstracts, PmIDS = str(return_abtracts_from_documents(reranked_documents))
        
    except:
        abstracts = str([doc.page_content for doc in context])
        PmIDS = [doc.metadata.get("PmID") for doc in context]

    response = chain.invoke({'context': abstracts, 
                        'previous_queries': previous_queries, 
                        'language_query': language_query,
                        'query': query}, 
                        config={'callbacks': [StreamHandler(response_placeholder)]})

    return response.content, PmIDS