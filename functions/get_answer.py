from langchain.schema.runnable import RunnableMap
from mistralai.models.chat_completion import ChatMessage
from langchain.callbacks.base import BaseCallbackHandler

# Streaming call back handler for responses
class StreamHandler(BaseCallbackHandler):
   def __init__(self, container, initial_text=""):
       self.container = container
       self.text = initial_text


   def on_llm_new_token(self, token: str, **kwargs):
       self.text += token
       self.container.markdown(self.text + "▌")


# Generate the answer by calling OpenAI's Chat Model
def get_gpt_answer(prompt, chat_model, retriever, question, previous_questions, response_placeholder):
    
   # Search for context first
   #inputs = RunnableMap({
   #    'question': lambda x: x['question'],
   #    'context': lambda x: retriever.get_relevant_documents(x['question'])
   #})
   
   chain = prompt | chat_model
   
   # Retrieve relevant documents from AstraDB as context
   context = retriever.get_relevant_documents(question)
   abstract = str([doc.page_content for doc in context])

   response = chain.invoke({'context':abstract, 
                            'previous_questions': previous_questions, 
                            'question': question}, 
                            config={'callbacks': [StreamHandler(response_placeholder)]})

   return response.content

# Generate the answer by calling OpenAI's Chat Model
def get_mistral_answer(prompt, client_mistral, retriever, question, previous_questions):
   
   # Retrieve relevant documents from AstraDB as context
   context = retriever.get_relevant_documents(question)
   abstract = str([doc.page_content for doc in context])

    # Incorporate the prompt with context into the Mistral chat
   messages = [
        ChatMessage(role="system", content=prompt + abstract + previous_questions),
        ChatMessage(role="user", content=question)
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
            yield chunk.choices[0].delta.content

# Generate the answer depending of Chat Model
def get_answer(engine_AI, prompt, chat_model, retriever, question, previous_questions, response_placeholder):
    if engine_AI == "gpt-3.5-turbo":
        answer = get_gpt_answer(prompt, chat_model, retriever, question, previous_questions, response_placeholder)
        return answer

    elif engine_AI == 'Mistral-7B-v0.2':
        # To contain the full answer
        response_content = ""
        for mistral_chunk in get_mistral_answer(prompt, chat_model, retriever, question, previous_questions):
            response_content += mistral_chunk
            
            # Streaming through response_placeholder. Markdown for the text formating.
            response_placeholder.markdown(response_content + "▌")

        return response_content