import streamlit as st

from functions.loading_vector import *
from functions.get_answer import get_answer
from functions.s3_files_functions import *

from functions.loading_examples_questions import random_questions

from functions.loading_history import loading_conversation_history
from functions.authentification_menu import get_authentification_menu
from functions.logged_sidebar_menu import loading_sidebar_menu

S3_BUCKET_NAME  = st.secrets["S3_BUCKET"]

# We check the parameters in the st.session_state
authentification_buttons = ["login", "login_button", "register", "sign_up_button", "reset_pwd",
                            "forgot_pwd", "forgot_pwd_button", "continue_without_logging", "without_loggin_button"]

for auth_buttons in authentification_buttons:
    st.session_state[auth_buttons] = st.session_state.get(auth_buttons, False)

# Generation the authentification menu (Logging, registration, continue without logging)
authenticator = get_authentification_menu()

# When connected via login or without loggin
if st.session_state.login or st.session_state.without_loggin_button:

    # Variable to keep the conversation between user and bot
    st.session_state.stock_messages = st.session_state.get('stock_messages', [])

    st.session_state.history_messages = st.session_state.get('history_messages', [[]])

    # Generate the example question
    st.session_state.random_example_questions = st.session_state.get('random_example_questions', random_questions())

    # Keep the previous questions in memory
    st.session_state.memory_questions = st.session_state.get('memory_questions', '')

    # We load the sidebar buttons 
    engine_AI, answer_AI_persona, language_AI, citing_sources_AI, nb_article = loading_sidebar_menu(authenticator)

    # We load the conversation history 
    loading_conversation_history()
            
    # Start with empty messages, stored in session state
    if 'messages' not in st.session_state:
       st.session_state.messages = []
   
    if 'first_question' not in st.session_state:
       st.session_state.first_question = False

    example_question = False

    # Draw a title and some markdown
    st.warning("Occasionally, a bug may occur where Nutritional AI fails to process the question. If this happens, please try asking again.")
    st.title("Your personal nutritional AI")
    st.markdown("""Your generative AI will guide you in your nutritional choice!""")

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
    if question := st.chat_input("How can I help you today?", max_chars=150) or example_question:
       try:
           if example_question:
               question = example_question

           st.session_state.first_question = True
       
           # We store the new question in memory
           memory_questions = " ".join(return_questions(st.session_state.messages))
           
           # Store the user's question in a session object for redrawing next time
           st.session_state.messages.append({"role": "human", "content": question})

           # Draw the user's question
           with st.chat_message('human'):
               st.markdown(question)

           # UI placeholder to start filling with agent response
           with st.chat_message('assistant'):
               response_placeholder = st.empty()

               answer, PmIDS = get_answer(engine_AI, answer_AI_persona, collection, retriever, question, memory_questions, response_placeholder, language_AI)

            # We expose the sources used by Nutritional AI to formulate it's answer
           if citing_sources_AI:

               answer += "  \n**You can find more informations in the following articles:**  \n"
       
               i = 0
               for article in PmIDS:
                   if article and i < nb_article:
                       answer += f"https://pubmed.ncbi.nlm.nih.gov/{article}/  \n"
                       i += 1

           # Store the bot's answer in a session object for redrawing next time
           st.session_state.messages.append({"role": "ai", "content": answer})

           # Write the final answer without the cursor
           response_placeholder.markdown(answer)

           # We update and store the conversation
           st.session_state.history_messages[-1] = st.session_state.messages

           # If user consented to logging
           if st.session_state.compliance_statut:
                # S3 bucket details for logging folder
                if st.session_state.login:
                    s3_key = f'logs/conversations/users/{st.session_state.user_id}'
                    check_number = True

                elif st.session_state.without_loggin_button:
                    s3_key = f'logs/conversations/visitors/{st.session_state.user_id}.json'
                    check_number = False

                # We modify the stock_message with the new question/answer
                append_to_logs(st.session_state.stock_messages, question, answer, 
                               engine_AI, answer_AI_persona)
        
                upload_to_s3(S3_BUCKET_NAME, s3_key, st.session_state.stock_messages, check_number, st.session_state.new_conversation)
                
                st.session_state.new_conversation = False
                
           st.rerun()
       except Exception as e:
           # If an error occur
           st.session_state.messages.append({"role": "ai", 
                                             "content": st.error("An error was detected, retry with another setup or question. Sorry for the inconvenience")})
           # Upload error to S3 bucket for further investigation
           upload_bug_to_s3(S3_BUCKET_NAME, str(e))

           s3_key = f'logs/{st.session_state.user_id}.json'

           print(e)
