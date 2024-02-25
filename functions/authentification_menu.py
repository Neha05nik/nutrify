import streamlit as st

from functions.send_mail import send_email
from streamlit_modal import Modal

from functions.gdpr_compliance import run_compliance_modal, get_compliance_message
from functions.s3_authenticator import loading_authenticator, saving_configs
from functions.s3_files_functions import *

S3_BUCKET_NAME  = st.secrets["S3_BUCKET"]

def get_authentification_menu():

    # We are loading the authenticator object and the config from the S3
    authenticator, config = loading_authenticator("nutritional_ai/config.yaml")

    init_buttons = ["successful_registration", "successful_forgotten_pwd", "successful_reset_pwd", 
                "compliance_message_bool", "option_menu", "new_conversation", "previous_conversation"]

    for init_b in init_buttons:
        st.session_state[init_b] = st.session_state.get(init_b, False)
        #if init_b not in st.session_state:
         #   st.session_state[init_b] = False

    # Just to show that the registration worked
    if st.session_state.successful_registration:
        st.success('User registered successfully')
        st.session_state.successful_registration = False

    # Just to show that the new password was sent
    if st.session_state.successful_forgotten_pwd:
        st.success('New password sent to your email')
        st.session_state.successful_forgotten_pwd = False

    # Just to show that the password was successfully modified
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
                st.session_state.previous_conversation = None
            else:
                st.session_state.user_id = st.session_state["email"]
                st.session_state.new_conversation = True

                # We read the previous conversations
                s3_key = f'logs/conversations/users/{st.session_state.user_id}'
                st.session_state.previous_conversation = loading_s3_conversations(S3_BUCKET_NAME, s3_key)
            
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

