import streamlit as st

from langchain.prompts import ChatPromptTemplate
from functions.loading_models import *
from functions.loading_promp import *
from functions.loading_vector import *
from functions.get_answer import *
from functions.s3_files_functions import *

from functions.gdpr_compliance import run_compliance_modal
from functions.loading_examples_questions import random_questions

from functions.send_mail import send_email
from streamlit_modal import Modal

from functions.gdpr_compliance import run_compliance_modal, get_compliance_message
from functions.s3_authenticator import loading_authenticator, saving_configs

try:
    QRCODE = st.secrets["QRCODE"]
    QRCODE_LINK = st.secrets["QRCODE_LINK"]
    S3_BUCKET_NAME  = st.secrets["S3_BUCKET"]
except:
    print("Error loading qr_image")

authenticator, config = loading_authenticator("nutritional_ai/config.yaml")

# We check the parameters in the st.session_state
authentification_buttons = ["login", "login_button", "register", "sign_up_button", "reset_pwd",
                            "forgot_pwd", "forgot_pwd_button", "continue_without_logging", "without_loggin_button"]

for auth_buttons in authentification_buttons:
    if auth_buttons not in st.session_state:
        st.session_state[auth_buttons] = False
    else:
        st.session_state[auth_buttons] = st.session_state[auth_buttons]    
    
if "successful_registration" not in st.session_state:
    st.session_state.successful_registration = False

if "successful_forgotten_pwd" not in st.session_state:
    st.session_state.successful_forgotten_pwd = False

if "successful_reset_pwd" not in st.session_state:
    st.session_state.successful_reset_pwd = False

if "compliance_message_bool" not in st.session_state:
    st.session_state.compliance_message_bool = False

if "option_menu" not in st.session_state:
    st.session_state.option_menu = False

if "new_conversation" not in st.session_state:
    st.session_state.new_conversation = False

if "previous_conversation" not in st.session_state:
    st.session_state.previous_conversation = False

# Just to show that the registration worked
if st.session_state.successful_registration:
    st.success('User registered successfully')
    st.session_state.successful_registration = False

if st.session_state.successful_forgotten_pwd:
    st.success('New password sent to your email')
    st.session_state.successful_forgotten_pwd = False

if st.session_state.successful_reset_pwd:
    st.success('Password modified successfully')
    st.session_state.successful_reset_pwd = False

# Show buttons before being logging or before "continue without logging" 
bool_logging = not st.session_state.login and not st.session_state.without_loggin_button

# When user wants to log in
if bool_logging:
    st.sidebar.title("Your personal nutritional AI")
    st.sidebar.markdown("---")

    if st.sidebar.button("**Log in**"):
        st.session_state.login_button = True
        st.session_state.sign_up_button = False
        st.session_state.forgot_pwd_button = False
        st.session_state.without_loggin_button = False
        st.rerun()

# When user wants to register
if not st.session_state.register and bool_logging:
    if st.sidebar.button("**Sign up**"):
        st.session_state.login_button = False
        st.session_state.sign_up_button = True
        st.session_state.forgot_pwd_button = False
        st.session_state.without_loggin_button = False
        st.rerun()

# When user forgot its password
if not st.session_state.forgot_pwd and bool_logging:
    if st.sidebar.button("**Forgot password**"):
        st.session_state.login_button = False
        st.session_state.sign_up_button = False
        st.session_state.forgot_pwd_button = True
        st.session_state.without_loggin_button = False
        st.rerun()

# When user forgot its password
if bool_logging:
    if st.sidebar.button("**Continue without logging**"):
        st.session_state.login_button = False
        st.session_state.sign_up_button = False
        st.session_state.forgot_pwd_button = False
        st.session_state.without_loggin_button = True
        st.session_state.user_id = f"user_{generate_random_number()}"
        st.rerun()

    st.sidebar.markdown("---")

# We launch the authenticator process
if st.session_state.login_button:
    authenticator.login()

# When the credentials are correct, the authentification is done
if st.session_state["authentication_status"] and st.session_state.login == False:
    st.session_state.login = True
    st.session_state.login_button = False
    st.rerun()

# If authentification failed
elif st.session_state["authentication_status"] is False:
    st.error('Email/password is incorrect')

# When user is log in with or without credentials
if st.session_state.login or st.session_state.without_loggin_button:

    if "user_id" not in st.session_state:
        if st.session_state.without_loggin_button:
            # Generate a random user number
            st.session_state.user_id = f"user_{generate_random_number()}"
        else:
            st.session_state.user_id = st.session_state["email"]
            st.session_state.new_conversation = True

            # We read the previous conversations
            s3_key = f'logs/conversations/users/{st.session_state.user_id}'
            st.session_state.previous_conversation = loading_s3_conversations(S3_BUCKET_NAME, s3_key)
#    else: 
#        st.session_state.user_id = st.session_state.user_id
        
    # We track the first part of the email if login else random user id
    username = st.session_state["email"].split('@')[0] if st.session_state.login else st.session_state.user_id

    st.sidebar.title(f'Welcome *{username}*')
    
    if st.session_state.option_menu:    
        modal = Modal(
        "Settings",
        key="settings",
        padding=20,
        max_width=744
        )
        
        with modal.container():
            if st.session_state.login:
                # Button to reset password
                rst_pwd = st.button("**Reset password**")

                if rst_pwd:
                    st.session_state.option_menu = False
                    # To launch the modification password form
                    st.session_state.reset_pwd = True
                    st.rerun()
                    
            change_consent = st.button("**Modify consent form**")
            quitting_option = st.button("Continue")

            # Solution for not working quitting with cross
            if quitting_option:
                st.session_state.option_menu = False
                st.rerun()

            if change_consent:
                st.session_state.option_menu = False
                # To relaunch the compliance message
                if st.session_state.login:
                    authenticator.set_credential_information(st.session_state["email"], 'compliance_message', False)
                    st.session_state.compliance_button = False
                    # We write the new user informations
                    saving_configs(config, "nutritional_ai/config.yaml")
                else:
                    st.session_state.compliance_message = False
                    st.session_state.compliance_button = False
                st.rerun()

    if st.session_state.login:

        if st.session_state.reset_pwd:
            try:
                # Return true when password is correctly change
                password_of_registered_user = authenticator.reset_password(st.session_state["email"])
                if password_of_registered_user:
                    st.session_state.reset_pwd = False
                    # We write the new user informations
                    saving_configs(config, "nutritional_ai/config.yaml")

                    st.session_state.successful_reset_pwd = True

                    st.rerun()
            except Exception as e:
                st.error(e)

        # We check if the compliance_message was asked to the user, mandatory in the first connexion
        try:
            compliance_message = authenticator.get_credential_information(st.session_state["email"], 'compliance_message')
            st.session_state.compliance_statut = authenticator.get_credential_information(st.session_state["email"], 'compliance_statut')
        except:
            # If error, and a compliance_message was not created or answered by the user, we relaunch the 
            compliance_message = False

        if not compliance_message:
            authenticator.set_credential_information(st.session_state["email"], 
                                                        'compliance_message', 
                                                        True)
            # Calling the function to execute the GDPR form
            st.session_state.compliance_statut = run_compliance_modal()
            if st.session_state.compliance_button:
                authenticator.set_credential_information(st.session_state["email"], 
                                                        'compliance_statut', 
                                                    st.session_state.compliance_statut)
        
                st.session_state.compliance_message_bool = True

                # We write the new user informations
                saving_configs(config, "nutritional_ai/config.yaml")

                st.rerun()


    else: 
        
        # Calling the function to execute the GDPR form
        st.session_state.compliance_statut = run_compliance_modal()

        if st.session_state.compliance_button and not st.session_state.compliance_message:
        
            st.session_state.compliance_message_bool = True

# When the user at hit the sign up button
elif st.session_state.sign_up_button:
    try:
        email_of_registered_user = authenticator.register_user(preauthorization=False)
        # The registration worked
        if email_of_registered_user:

            # By default, the compliance message is set to False
            authenticator.set_credential_information(email_of_registered_user, 
                                                    'compliance_message', 
                                                    False)
            # We write the new user informations
            saving_configs(config, "nutritional_ai/config.yaml")

            # Just to show that the registration was successful
            st.session_state.successful_registration = True
        
            # Quitting the register mode and launching the login
            st.session_state.sign_up_button = False
            st.session_state.login_button = True

            st.rerun()
    except Exception as e:
        st.error(e)

# When the user hit the forgotten button
elif st.session_state.forgot_pwd_button:
    try:
        # We ask for the email used in the registration
        email_of_forgotten_password, new_random_password = authenticator.forgot_password()
        # If we have a successful email
        if email_of_forgotten_password:
            send_email(email_of_forgotten_password, new_random_password)
            st.session_state.password = new_random_password
            saving_configs(config, "nutritional_ai/config.yaml")

            # Just to show that the new password was sent
            st.session_state.successful_forgotten_pwd = True

        elif email_of_forgotten_password == False:
            st.error('Email not found')

    except Exception as e:
        st.error(e)


# To display the compliance message True: accepted/ False: Refused
if st.session_state.compliance_message_bool:

    st.session_state.compliance_message = True
    st.session_state.compliance_message_bool = False

    if st.session_state.login:
        compliance_statut = authenticator.get_credential_information(st.session_state["email"], 'compliance_statut')
    else:
        compliance_statut = st.session_state.compliance_statut

    get_compliance_message(compliance_statut)


# When connected
if st.session_state.login or st.session_state.without_loggin_button:

    # Variable to keep the conversation
    if "stock_messages" not in st.session_state:
        st.session_state.stock_messages = []
    else:
        st.session_state.stock_messages = st.session_state.stock_messages

    # Generate the example question
    if "random_example_questions" not in st.session_state:
        st.session_state.random_example_questions = random_questions()
    else:
        st.session_state.random_example_questions = st.session_state.random_example_questions

    # Keep the previous question in memory
    if "memory_questions" not in st.session_state:
        st.session_state.memory_questions = ""
    else:
        st.session_state.memory_questions = st.session_state.memory_questions

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
    memory_AI = st.sidebar.checkbox('Use memory',
                                    help="""
                                    Nutritional AI is keeping your previous questions in memory.
                                    """)

    citing_sources_AI = st.sidebar.checkbox('Cite sources',
                                            help="""
                                            Nutritional AI cites the articles on which the model based its answers
                                            """)

    if citing_sources_AI:
        nb_article = st.sidebar.slider('Number of articles to cite', min_value=2, max_value=5, value = 3)

    if st.sidebar.button("New conversation"):
        # We empty the conversation and restore the questions
        st.session_state.messages = []
        st.session_state.random_example_questions = random_questions()
        st.session_state.first_question = False
        st.session_state.new_conversation = True

    if st.sidebar.button("Donation"):
        st.sidebar.image(QRCODE, width=200)
        st.sidebar.link_button('Paypal link', url = QRCODE_LINK)
        st.sidebar.markdown("""**If you find value in our service, consider supporting us with a small donation. 
        Your contribution helps maintain the platform and fuels the development of new features. 
        We appreciate your generosity – thank you for helping us thrive!**""")

    # We open the Option menu if clicked on
    if st.sidebar.button("Settings"):
        st.session_state.option_menu = True
        st.session_state.reset_pwd = False
        st.rerun()

    # Logout from account
    if st.sidebar.button("**Log out**"):
        # Restart the parameters for loging in or Signing in 
        st.session_state.login = False
        st.session_state.register = False
        st.session_state["authentication_status"] = None
        st.session_state.reset_pwd = False
        st.session_state.messages = []
        st.session_state.first_question = False
        if st.session_state.without_loggin_button:
            st.session_state.without_loggin_button = False
            st.session_state.user_id = f"user_{generate_random_number()}"
            st.session_state.compliance_button = False
            st.session_state.compliance_message = False

        st.rerun()

    # Archived conversations only available if login
    if st.session_state.login:
        st.sidebar.markdown("---")
        st.sidebar.title("Previous conversations")
        st.sidebar.markdown("---")

        if st.session_state.previous_conversation != None:
            bool_timeline = [True, True, True, True]
            try:
                # We read from the most recent to oldest
                for i, conversation in enumerate(st.session_state.previous_conversation[::-1]):
                    # Each text is visible as a button
                    title = return_conversation(conversation)[0]['content']
                    time_conversation = return_dates(conversation)[0]

                    if return_time_difference(time_conversation) == 0 and bool_timeline[0]:
                        st.sidebar.subheader("Today's conversations")  
                        bool_timeline[0] = False

                    elif return_time_difference(time_conversation) == 1 and bool_timeline[1]:
                        st.sidebar.subheader("Yesterday's conversations")
                        bool_timeline[1] = False

                    elif return_time_difference(time_conversation) > 1 and return_time_difference(time_conversation) <= 30 and bool_timeline[2]:
                        st.sidebar.subheader("Previous 7 days's conversations")
                        bool_timeline[2] = False

                    elif return_time_difference(time_conversation) > 30 and bool_timeline[3]:
                        st.sidebar.subheader("Previous 30 days's conversations")
                        bool_timeline[3] = False

                    # We display title and subtitle on two separate rows in the button
                    if st.sidebar.button(f"{title}", key=i):
                        # Do something when the button is clicked
                        st.session_state.messages = return_conversation(conversation)
                        st.session_state.first_question = True
                        
            except Exception as e:
                # upload the log for bug 
                upload_bug_to_s3(S3_BUCKET_NAME, str(e))
                container = st.sidebar.container()
                container.error("Reload the page to see the previous conversations")

    prompt = load_prompt(answer_AI_type, answer_AI_persona)

    # Special prompting for gpt
    if engine_AI == "gpt-3.5-turbo":
        prompt += """
            CONTEXT:
            {context}

            PREVIOUS QUERIES:
            {previous_queries}

            GIVE YOUR ANSWER IN: 
            {language_query}

            QUERY:
            {query}

            YOUR ANSWER:"""
        # We have the prompt, then the context and finally the user question
        prompt = ChatPromptTemplate.from_messages([("system", prompt)])
    
        # We load the chatmodel GPT
        chat_model = load_chat_model()

    elif engine_AI == 'Mistral-7B-v0.2':
        # We load the chatmodel Mistral
        chat_model = load_client_mistral()


    # Start with empty messages, stored in session state
    if 'messages' not in st.session_state:
       st.session_state.messages = []
   
    if 'first_question' not in st.session_state:
       st.session_state.first_question = False

    example_question = False

    # Draw a title and some markdown
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
       
           # We store the new question
           st.session_state.memory_questions += question 

           # We check if "use memory" is checked
           if memory_AI:
               previous_questions = st.session_state.memory_questions
           else:
               previous_questions = ""
       
           # Store the user's question in a session object for redrawing next time
           st.session_state.messages.append({"role": "human", "content": question})

           # Draw the user's question
           with st.chat_message('human'):
               st.markdown(question)

           # UI placeholder to start filling with agent response
           with st.chat_message('assistant'):
               response_placeholder = st.empty()

               answer = get_answer(engine_AI, prompt, chat_model, vector_store, retriever, question, previous_questions, response_placeholder)

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
                if st.session_state.login:
                    s3_key = f'logs/conversations/users/{st.session_state.user_id}'
                    check_number = True

                elif st.session_state.without_loggin_button:
                    s3_key = f'logs/conversations/visitors/{st.session_state.user_id}.json'
                    check_number = False

                append_to_logs(st.session_state.stock_messages, question, answer, 
                               engine_AI, answer_AI_persona, answer_AI_type)
        
                upload_to_s3(S3_BUCKET_NAME, s3_key, st.session_state.stock_messages, check_number, st.session_state.new_conversation)
                
                st.session_state.new_conversation = False
                
           st.rerun()
       except Exception as e:
           # If an error occur
           st.session_state.messages.append({"role": "ai", "content": st.error("An error was detected, retry with another setup or question. Sorry for the inconvenience")})
           # Upload error to S3 bucket for further investigation
           upload_bug_to_s3(S3_BUCKET_NAME, str(e))

           s3_key = f'logs/{st.session_state.user_id}.json'

           print(e)
