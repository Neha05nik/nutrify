from langchain.schema.runnable import RunnableMap
from mistralai.models.chat_completion import ChatMessage
from langchain.callbacks.base import BaseCallbackHandler
from functions.retriever_abstracts import small_to_big, reranker_abstracts, return_abtracts_from_documents

# Streaming call back handler for responses
class StreamHandler(BaseCallbackHandler):
   def __init__(self, container, initial_text=""):
       self.container = container
       self.text = initial_text


   def on_llm_new_token(self, token: str, **kwargs):
       self.text += token
       self.container.markdown(self.text + "▌")


# Generate the answer by calling OpenAI's Chat Model
def get_gpt_answer(prompt, chat_model, vector_store, retriever, query, previous_queries, response_placeholder):
    
   # Search for context first
   #inputs = RunnableMap({
   #    'question': lambda x: x['question'],
   #    'context': lambda x: retriever.get_relevant_documents(x['question'])
   #})
   
   chain = prompt | chat_model
   
   # Retrieve relevant documents from AstraDB as context
   context = retriever.get_relevant_documents(query)

   try:
       # We search for full abtract
       full_documents = small_to_big(query, vector_store, context)
       # We rerank the documents
       reranked_documents = reranker_abstracts(query, full_documents)
       # We add metadatas
       abstracts = str(return_abtracts_from_documents(reranked_documents))
       
   except:
       abstracts = str([doc.page_content for doc in context])


   response = chain.invoke({'context':abstracts, 
                            'previous_queries': previous_queries, 
                            'query': query}, 
                            config={'callbacks': [StreamHandler(response_placeholder)]})

   return response.content

# Generate the answer by calling OpenAI's Chat Model
def get_mistral_answer(prompt, client_mistral, vector_store, retriever, query, previous_queries):
   
   # Retrieve relevant documents from AstraDB as context
   context = retriever.get_relevant_documents(query)

   try:
       # We search for full abtract
       full_documents = small_to_big(query, vector_store, context)
       # We rerank the documents
       reranked_documents = reranker_abstracts(query, full_documents)
       # We add metadatas
       abstracts = """CONTEXT: """ + str(return_abtracts_from_documents(reranked_documents))
       
   except:
       abstracts = """CONTEXT: """ + str([doc.page_content for doc in context])

   import streamlit as st
   content = f"""{prompt} \n CONTEXT: \n {abstracts} \n PREVIOUS QUESTIONS: {previous_queries}"""

    # Incorporate the prompt with context into the Mistral chat
   messages = [
        ChatMessage(role="system", content=content),
        ChatMessage(role="user", content=query)
    ]
   st.text(messages)
    # Chat with Mistral-7B-v0.2
    # Answer is streamed. 
   for chunk in client_mistral.chat_stream(
    model="mistral-tiny",
    messages=messages,
    temperature=0.4
        ):
        if chunk.choices[0].delta.content:
            # We send a generator
            yield chunk.choices[0].delta.content

# Generate the answer depending of Chat Model
def get_answer(engine_AI, prompt, chat_model, vector_store, retriever, query, previous_queries, response_placeholder):
    if engine_AI == "gpt-3.5-turbo":
        answer = get_gpt_answer(prompt, chat_model, vector_store, retriever, query, previous_queries, response_placeholder)
        return answer

    elif engine_AI == 'Mistral-7B-v0.2':
        # To contain the full answer
        response_content = ""
        for mistral_chunk in get_mistral_answer(prompt, chat_model, vector_store, retriever, query, previous_queries):
            response_content += mistral_chunk
            
            # Streaming through response_placeholder. Markdown for the text formating.
            response_placeholder.markdown(response_content + "▌")

        return response_content