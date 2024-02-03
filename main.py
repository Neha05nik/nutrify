import streamlit as st

from langchain.prompts import ChatPromptTemplate
from functions.loading_models import *
from functions.loading_promp import *
from functions.loading_vector import *
from functions.get_answer import *

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ASTRA_API_ENDPOINT = st.secrets["ASTRA_API_ENDPOINT"]
    ASTRA_TOKEN = st.secrets["ASTRA_TOKEN"]
    NCBI_API_KEY = st.secrets["NCBI_API_KEY"]
    HF_API_KEY = st.secrets["HF_API_KEY"]
    ASTRA_COLLECTION  =  st.secrets["ASTRA_COLLECTION"]
    MISTRAL_API_KEY  =  st.secrets["MISTRAL_API_KEY"]
except:
    # For local use
    from configs import *
     
engine_AI= st.sidebar.radio('**Powered by:**',["Mistral-7B-v0.2", "gpt-3.5-turbo"], help="Mistral-7B-v0.2 is a more powerful model than GPT-3.5")

answer_AI_type = st.sidebar.radio('**Nutrional_AI persona:**',["Normal", "Scientific", "Nutritional coach"], 
                        help="""
                            All answers will be generated with scientific knowledge with the purpose 
                            to promote better food consumption.  

                            **Normal**: It wants you to eat better.  

                            **Scientific**: It wants you to eat better and with reasoning.  

                            **Nutritional coach**: It is your coach, nothing will satisfy him more than succeeding in having better food decisions.
                            """
)

answer_AI = st.sidebar.radio('**Nutrional_AI answers:**',["Short", "Summary", "Long and precise"], 
                        help="""
                            All answers will be generated with scientific knowledge with the purpose 
                            to promote better food consumption.  

                            **Short**: The answers will be short and concise.  

                            **Summary**: The answers will be given by bullet points.  

                            **Long and precise**: The answers will be extensive.
                            """
)

citing_sources_AI = st.sidebar.checkbox('Cite sources')

if citing_sources_AI:
    nb_article = st.sidebar.slider('Number of articles to cite', min_value=2, max_value=5, value = 2)

if st.sidebar.button("Clear conversation"):
    # We empty the conversation and restore the questions
    st.session_state.messages = []
    st.session_state.first_question = False

prompt = load_prompt(answer_AI, answer_AI_type)

# Special prompting for gpt
if engine_AI == "gpt-3.5-turbo":
    prompt += """
        CONTEXT:
        {context}

        QUESTION:
        {question}

        YOUR ANSWER:"""
    prompt = ChatPromptTemplate.from_messages([("system", prompt)])
    
    # We load the chatmodel GPT
    chat_model = load_chat_model()

elif engine_AI == 'Mistral-7B-v0.2':
    # We load the chatmodel Mistral
    chat_model = load_chat_model_mistral()


# Start with empty messages, stored in session state
if 'messages' not in st.session_state:
   st.session_state.messages = []
   
if 'first_question' not in st.session_state:
   st.session_state.first_question = False

example_question = False

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

# We suggest some simple questions
if st.session_state.first_question == False:
    if st.button("What should I eat in the morning?"):
        example_question = "What should I eat in the morning?"
        st.session_state.first_question = True
    if st.button("In which food can I find the most fibers?"):
        example_question = "In which food can I find the most fibers?"
        st.session_state.first_question = True
    if st.button("What should I eat after right after practicing some sport?"):
        example_question = "What should I eat after right after practicing some sport?"
        st.session_state.first_question = True
    if st.button("How can I best prepare for a run tomorrow morning?"):
        example_question = "How can I best prepare for a run tomorrow morning?"
        st.session_state.first_question = True

# Draw all messages, both user and bot so far (every time the app reruns)
for message in st.session_state.messages:
   st.chat_message(message['role']).markdown(message['content'])

# Draw the chat input box
if question := st.chat_input("How can I help you today?", max_chars=250) or example_question:
   
   if example_question:
       question = example_question

   st.session_state.first_question = True
   
   # Store the user's question in a session object for redrawing next time
   st.session_state.messages.append({"role": "human", "content": question})

   # Draw the user's question
   with st.chat_message('human'):
       st.markdown(question)

   # UI placeholder to start filling with agent response
   with st.chat_message('assistant'):
       response_placeholder = st.empty()

       answer = get_answer(engine_AI, prompt, chat_model, retriever, question, response_placeholder)

   if citing_sources_AI:
       sources = vector_store.similarity_search(question, k=nb_article)
       # We extract the pmids from the metadata
       pmids = [doc.metadata.get('PmID') for doc in sources]
       answer += "  \n**You can find more informations in the following articles:**  \n"
       for article in pmids:
           if article:
               answer += f"https://pubmed.ncbi.nlm.nih.gov/{article}/  \n"

   # Store the bot's answer in a session object for redrawing next time
   st.session_state.messages.append({"role": "ai", "content": answer})

   # Write the final answer without the cursor
   response_placeholder.markdown(answer)

   
