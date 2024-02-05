import streamlit as st

from langchain.prompts import ChatPromptTemplate
from functions.loading_models import *
from functions.loading_promp import *
from functions.loading_vector import *
from functions.get_answer import *
from functions.logging import *

from functions.gdpr_compliance import run_compliance_modal
from functions.loading_examples_questions import random_questions

# Calling the function to execute the GDPR form
st.session_state.compliance_statut = run_compliance_modal()

try:
    QRCODE = st.secrets["QRCODE"]
    S3_BUCKET_NAME  = st.secrets["S3_BUCKET"]
except:
    print("Error loading qr_image")

# Generate a random user number and a variable to keep the conversation
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{generate_random_number()}"
    st.session_state.stock_messages = []
else:
    st.session_state.user_id = st.session_state.user_id
    st.session_state.stock_messages = st.session_state.stock_messages

# Generate the example question
if "random_example_questions" not in st.session_state:
    st.session_state.random_example_questions = random_questions()
else:
    st.session_state.random_example_questions = st.session_state.random_example_questions
    
engine_AI = st.sidebar.radio('**Powered by:**',["Mistral-7B-v0.2", "gpt-3.5-turbo"], help="Mistral-7B-v0.2 is a more powerful model than GPT-3.5")

answer_AI_persona = st.sidebar.radio('**Nutrional_AI persona:**',["Normal", "Scientific", "Nutritional coach"], 
                        help="""
                            All answers will be generated with scientific knowledge with the purpose 
                            to promote better food consumption.  

                            **Normal**: It wants you to eat better foods.  

                            **Scientific**: It wants you to eat better foods and with reasoning.  

                            **Nutritional coach**: It is your coach, nothing will satisfy him more than succeeding in having better food decisions.
                            """
)

answer_AI_type = st.sidebar.radio('**Nutrional_AI answers:**',["Short", "Summary", "Long and precise"], 
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
    nb_article = st.sidebar.slider('Number of articles to cite', min_value=2, max_value=5, value = 3)

if st.sidebar.button("Clear conversation"):
    # We empty the conversation and restore the questions
    st.session_state.messages = []
    st.session_state.random_example_questions = random_questions()
    st.session_state.first_question = False

if st.sidebar.button("Donation"):
    st.sidebar.image(QRCODE, width=200)
    st.sidebar.markdown("""**If you find value in our service, consider supporting us with a small donation. 
    Your contribution helps maintain the platform and fuels the development of new features. 
    We appreciate your generosity – thank you for helping us thrive!**""")

prompt = load_prompt(answer_AI_type, answer_AI_persona)

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
    for i in range(4):
        #To create an unique key for each button
        button_key = f"button_{i}" 
        if st.button(st.session_state.random_example_questions[i], key=button_key):
            example_question = st.session_state.random_example_questions[i]
            st.session_state.first_question = True

# Draw all messages, both user and bot so far (every time the app reruns)
for message in st.session_state.messages:
   st.chat_message(message['role']).markdown(message['content'])

# Draw the chat input box
if question := st.chat_input("How can I help you today?", max_chars=250) or example_question:
   try:
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
           # We extract the closest data from our database to the question
           sources = vector_store.similarity_search(question, k=10)

           # We extract the pmids from the metadata and eliminate duplicatas
           pmids = list(set([doc.metadata.get('PmID') for doc in sources]))

           answer += "  \n**You can find more informations in the following articles:**  \n"
       
           i = 0
           for article in pmids:
               if article and i < nb_article:
                   answer += f"https://pubmed.ncbi.nlm.nih.gov/{article}/  \n"
                   i += 1

       # Store the bot's answer in a session object for redrawing next time
       st.session_state.messages.append({"role": "ai", "content": answer})

       # Write the final answer without the cursor
       response_placeholder.markdown(answer)

       # If user consent to logging
       if st.session_state.compliance_statut:
            # S3 bucket details for logging folder
            s3_key = f'logs/conversations/{st.session_state.user_id}.json'

            append_to_logs(st.session_state.stock_messages, question, answer, 
                           engine_AI, answer_AI_persona, answer_AI_type)
        
            upload_to_s3(S3_BUCKET_NAME, s3_key, st.session_state.stock_messages)

       st.rerun()
   except Exception as e:
       # If an error occur
       st.session_state.messages.append({"role": "ai", "content": st.error("An error was detected, retry with another setup or question. Sorry for the inconvenience")})
       # Upload error to S3 bucket for further investigation
       upload_bug_to_s3(S3_BUCKET_NAME, str(e))

       s3_key = f'logs/{st.session_state.user_id}.json'

