import streamlit as st
import os
import tempfile


from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import AstraDB
from langchain.schema.runnable import RunnableMap
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
#from configs import *


# Streaming call back handler for responses
class StreamHandler(BaseCallbackHandler):
   def __init__(self, container, initial_text=""):
       self.container = container
       self.text = initial_text


   def on_llm_new_token(self, token: str, **kwargs):
       self.text += token
       self.container.markdown(self.text + "▌")


# Function for Vectorizing uploaded data into Astra DB
def vectorize_text(uploaded_file, vector_store):
   if uploaded_file is not None:
      
       # Write to temporary file
       temp_dir = tempfile.TemporaryDirectory()
       file = uploaded_file
       temp_filepath = os.path.join(temp_dir.name, file.name)
       with open(temp_filepath, 'wb') as f:
           f.write(file.getvalue())


       # Load the PDF
       docs = []
       loader = PyPDFLoader(temp_filepath)
       docs.extend(loader.load())


       # Create the text splitter
       text_splitter = RecursiveCharacterTextSplitter(
           chunk_size = 1500,
           chunk_overlap  = 100
       )


       # Vectorize the PDF and load it into the Astra DB Vector Store
       pages = text_splitter.split_documents(docs)
       vector_store.add_documents(pages) 
       st.info(f"{len(pages)} pages loaded.")

       
# Cache prompt for future runs
@st.cache_data()
def load_prompt(answer_AI):
    if answer_AI == "Long and precise":
        template = """
        You're a helpful AI assistant tasked to answer the user's questions.
        You're a friendly scientist and you answer extensively with multiples sentences. 
        You are a scientist that use it's scientific knowledge to answer.
        Your answers have to be related to nutrition and cite precise foods that can be eaten.
        You have to give nutritional advices when you answer. 
        If you don't know, do not answer.

        CONTEXT:
        {context}


        QUESTION:
        {question}


        YOUR ANSWER:"""
    elif answer_AI == "Summary":
        template = """
        You're a helpful AI assistant tasked to answer the user's questions.
        You're a friendly scientist and you answer with bullet points. 
        Your answers have to be related to nutrition and cite precise foods that can be eaten.
        You have to give nutritional advices when you answer. 
        If you don't know, do not answer.

        CONTEXT:
        {context}


        QUESTION:
        {question}


        YOUR ANSWER:"""

    elif answer_AI == "Short":
        template = """
        You're a helpful AI assistant tasked to answer the user's questions.
        You're a friendly scientist and you answer with short sentences. 
        Your answers have to be related to nutrition and cite precise foods that can be eaten.
        You have to give nutritional advices when you answer. 
        If you don't know, do not answer.

        CONTEXT:
        {context}


        QUESTION:
        {question}


        YOUR ANSWER:"""

    return ChatPromptTemplate.from_messages([("system", template)])

answer_AI = st.sidebar.radio('Nutrional_AI answers:',["Long and precise", "Summary", "Short"])

prompt = load_prompt(answer_AI)


# Cache OpenAI Chat Model for future runs
@st.cache_resource()
def load_chat_model():
   return ChatOpenAI(
       openai_api_key=OPENAI_API_KEY,
       temperature=0.3,
       model='gpt-3.5-turbo',
       streaming=True,
       verbose=True
   )
chat_model = load_chat_model()


# Cache the Astra DB Vector Store for future runs
@st.cache_resource(show_spinner='Connecting to Astra')
def load_vector_store():
   # Connect to the Vector Store
   #vector_store = AstraDB(
      # embedding=OpenAIEmbeddings(),
     #  collection_name="my_store",
    #   api_endpoint=st.secrets['ASTRA_API_ENDPOINT'],
   #    token=st.secrets['ASTRA_TOKEN']
  # )
    
    vector_store = AstraDB(embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
    collection_name="sc_article_nutrition",
    api_endpoint=ASTRA_API_ENDPOINT,
    token=ASTRA_TOKEN)

    return vector_store
vector_store = load_vector_store()


# Cache the Retriever for future runs
@st.cache_resource(show_spinner='Getting retriever')
def load_retriever():
   # Get the retriever for the Chat Model
   retriever = vector_store.as_retriever(
       search_kwargs={"k": 5}
   )
   return retriever


# Start with empty messages, stored in session state
if 'messages' not in st.session_state:
   st.session_state.messages = []


# Draw a title and some markdown
st.title("Your personal nutritional AI ")
st.markdown("""Your generative AI will guide you in your nutritional choice!""")


# Include the upload form for new data to be Vectorized
#with st.sidebar:
#   with st.form('upload'):
#       uploaded_file = st.file_uploader('Upload a document for additional context', type=['pdf'])
#       submitted = st.form_submit_button('Save to Astra DB')
#       if submitted:
#           vectorize_text(uploaded_file, vector_store)
           

retriever = load_retriever()

# Draw all messages, both user and bot so far (every time the app reruns)
for message in st.session_state.messages:
   st.chat_message(message['role']).markdown(message['content'])


# Draw the chat input box
if question := st.chat_input("How can I help you today?"):
  
   # Store the user's question in a session object for redrawing next time
   st.session_state.messages.append({"role": "human", "content": question})


   # Draw the user's question
   with st.chat_message('human'):
       st.markdown(question)


   # UI placeholder to start filling with agent response
   with st.chat_message('assistant'):
       response_placeholder = st.empty()


   # Generate the answer by calling OpenAI's Chat Model
   # Search for context first
   inputs = RunnableMap({
       'context': lambda x: retriever.get_relevant_documents(x['question']),
       'question': lambda x: x['question']
   })
   chain = inputs | prompt | chat_model
   response = chain.invoke({'question': question}, config={'callbacks': [StreamHandler(response_placeholder)]})
   answer = response.content


   # Store the bot's answer in a session object for redrawing next time
   st.session_state.messages.append({"role": "ai", "content": answer})


   # Write the final answer without the cursor
   response_placeholder.markdown(answer)
