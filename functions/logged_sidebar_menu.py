import streamlit as st
from functions.loading_examples_questions import random_questions
from functions.s3_files_functions import generate_random_number

try:
    QRCODE = st.secrets["QRCODE"]
    QRCODE_LINK = st.secrets["QRCODE_LINK"]
except:
    print("Error loading qr_image")

def loading_sidebar_menu(authenticator):
    engine_AI = st.sidebar.radio('**Powered by:**',["Mistral-7B-v0.2", "gpt-3.5-turbo"], help="Mistral-7B-v0.2 is a more powerful model than GPT-3.5")
    
    answer_AI_persona = st.sidebar.radio('**Nutrional_AI persona:**',["Normal", "Scientific", "Nutritional coach"], 
                            help="""
                                All answers will be generated with scientific knowledge with the purpose 
                                to promote better food consumption.  

                                **Normal**: It wants you to eat better foods. It will give you some anecdotes alongside.  

                                **Scientific**: It wants you to eat better foods and with scientific reasoning.  

                                **Nutritional coach**: It is your nutritional coach, nothing will satisfy him more than succeeding in convincing you in eating better foods.
                                """
    )

    language_AI = st.sidebar.selectbox('**Language:**', ['AUTO-DETECT', 'ENGLISH', 'FRENCH', 'GERMAN', 'SPANISH', 'ITALIAN'],
                                    help="""
                                    Nutritional AI should be able to auto-detect the language from the list.
                                    """)

    citing_sources_AI = st.sidebar.checkbox('Cite sources',
                                            help="""
                                            Nutritional AI cites the articles on which the model based its answers
                                            """)

    if citing_sources_AI:
        nb_article = st.sidebar.slider('Number of articles to cite', min_value=2, max_value=5, value = 3)

    if st.sidebar.button("New conversation"):
        # We store the messages, then empty the current conversation and restore the questions
        st.session_state.history_messages.append([])
        st.session_state.messages = []
        st.session_state.random_example_questions = random_questions()
        st.session_state.first_question = False
        st.session_state.new_conversation = True

    if st.sidebar.button("Donation"):
        # Added a paypal link, to help maintain the models online
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
        authenticator._implement_logout()
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

    if citing_sources_AI:
        return engine_AI, answer_AI_persona, language_AI, citing_sources_AI, nb_article
    else: 
        return engine_AI, answer_AI_persona, language_AI, citing_sources_AI, 0