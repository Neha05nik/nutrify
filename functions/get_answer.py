from langchain.schema.runnable import RunnableMap
from mistralai.models.chat_completion import ChatMessage
from langchain.callbacks.base import BaseCallbackHandler
from functions.retriever_abstracts import small_to_big, reranker_abstracts, return_abtracts_from_documents
from functions.generate_question import get_mistral_requery, get_openAI_requery
from functions.language_dectection import detect_language

# Streaming call back handler for responses
class StreamHandler(BaseCallbackHandler):
   def __init__(self, container, initial_text=""):
       self.container = container
       self.text = initial_text


   def on_llm_new_token(self, token: str, **kwargs):
       self.text += token
       self.container.markdown(self.text + "▌")


# Generate the answer by calling OpenAI's Chat Model
def get_gpt_answer(prompt, chat_model, vector_store, retriever, query, language_query, previous_queries, response_placeholder):
    
   # Search for context first
   #inputs = RunnableMap({
   #    'question': lambda x: x['question'],
   #    'context': lambda x: retriever.get_relevant_documents(x['question'])
   #})
   
   chain = prompt | chat_model

   # We get a new query, generate by GPT-4 model
   query = get_openAI_requery(query)

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

# Generate the answer by calling OpenAI's Chat Model
def get_mistral_answer(prompt, client_mistral, vector_store, retriever, query, language_query, previous_queries):
   
   try:
       # We get a new query, generate by mistral small model
       query = get_mistral_requery(client_mistral, query)

       # Retrieve relevant documents from AstraDB as context
       context = retriever.get_relevant_documents(query)
       
       try:
           # We search for full abtract
           full_documents = small_to_big(query, vector_store, context)
           # We rerank the documents
           reranked_documents = reranker_abstracts(query, full_documents)
           # We add the context
           abstracts, PmIDS = str(return_abtracts_from_documents(reranked_documents))
       
       except:
           # If failed to retrieve the full documents or reranking, we send the normal context
           abstracts = str([doc.page_content for doc in context])
           PmIDS = [doc.metadata.get("PmID") for doc in context]

       # We ground the answer in the same language as the question
       content = f"""{prompt} \n 
                    CONTEXT: \n {abstracts} \n 
                    PREVIOUS QUESTIONS: {previous_queries} \n 
                    YOU MUST ANSWER IN: '{language_query}' \n
                    QUERY:"""

        # Incorporate the prompt with context into the Mistral chat
       messages = [
            ChatMessage(role="system", content=content),
            ChatMessage(role="user", content=query)
        ]
       
        # Chat with Mistral-7B-v0.2
        # Answer is streamed. 
       for chunk in client_mistral.chat_stream(
        model="mistral-tiny",
        messages=messages,
        temperature=0.4
            ):
            if chunk.choices[0].delta.content:
                # We send a generator
                yield chunk.choices[0].delta.content, PmIDS
   
   except: 
       return "Error occured, retry"

# Generate the answer depending of Chat Model
def get_answer(engine_AI, prompt, chat_model, vector_store, retriever, query, previous_queries, response_placeholder, language_AI):

    # We detect the language of the query
    if language_AI == "AUTO-DETECT":
        # We detect the language of the user's question
        language_query = detect_language(query)
    else:
        language_query = language_AI
        
    if engine_AI == "gpt-3.5-turbo":
        answer = get_gpt_answer(prompt, chat_model, vector_store, retriever, query, language_query, previous_queries, response_placeholder)
        return answer

    elif engine_AI == 'Mistral-7B-v0.2':
        # To contain the full answer
        answer = ""
        
        # In case it takes too long to have an answer.
        # It helps the user to know an answer is coming
        response_placeholder.markdown("Nutritional AI is thinking about your question...▌")

        for mistral_chunk in get_mistral_answer(prompt, chat_model, vector_store, retriever, query, language_query, previous_queries):

            answer += mistral_chunk[0]
            
            # Streaming through response_placeholder. Markdown for the text formating.
            response_placeholder.markdown(answer + "▌")

        # After the loop, get the PmIDS value
        PmIDS = mistral_chunk[1]

        return answer, PmIDS