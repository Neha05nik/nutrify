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
def get_gpt_answer(prompt, chat_model, retriever, question, response_placeholder):
    
   # Search for context first
   inputs = RunnableMap({
       'context': lambda x: retriever.get_relevant_documents(x['question']),
       'question': lambda x: x['question']
   })
   chain = inputs | prompt | chat_model

   response = chain.invoke({'question': question}, config={'callbacks': [StreamHandler(response_placeholder)]})

   return response.content

# Generate the answer by calling OpenAI's Chat Model
def get_mistral_answer(prompt, chat_model, retriever, question):
   
   # Retrieve relevant documents from AstraDB as context
   context = retriever.get_relevant_documents(question)
   abstract = str([doc.page_content for doc in context])

    # Incorporate the prompt with context into the Mistral chat
   messages = [
        ChatMessage(role="system", content=prompt + abstract),
        ChatMessage(role="user", content=question)
    ]

    # Chat with Mistral-7B-v0.2
   chat_response = chat_model.chat(
        model="mistral-tiny",
        messages=messages,
        temperature=0.4,
    )
   # We return the content of the AI response
   return chat_response.choices[0].message.content

# Generate the answer depending of Chat Model
def get_answer(engine_AI, prompt, chat_model, retriever, question, response_placeholder):
    if engine_AI == "gpt-3.5-turbo":
        answer = get_gpt_answer(prompt, chat_model, retriever, question, response_placeholder)

    elif engine_AI == 'Mistral-7B-v0.2':
        answer = get_mistral_answer(prompt, chat_model, retriever, question)
    
    return answer