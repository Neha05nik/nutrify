import streamlit as st
import yaml

import streamlit_authenticator as stauth
from functions.send_mail import send_email
from streamlit_modal import Modal

from yaml.loader import SafeLoader

from functions.gdpr_compliance import run_compliance_modal, get_compliance_message
from functions.logging import generate_random_number

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

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

# Draw a title and some markdown
st.title("Your personal nutritional AI ")
st.markdown("""Your generative AI will guide you in your nutritional choice!""")

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
        st.rerun()

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

    if st.session_state.without_loggin_button:
        # Generate a random user number 
        if "user_id" not in st.session_state:
            st.session_state.user_id = f"user_{generate_random_number()}"
        else:
            st.session_state.user_id = st.session_state.user_id

        st.sidebar.title(f'Welcome *{st.session_state.user_id}*')
    else: 
        # We track the first part of the email
        username = st.session_state["email"].split('@')[0]

        st.sidebar.title(f'Welcome *{username}*')

    # Logout from account
    if st.sidebar.button("**Logout**"):
        # Restart the parameters for loging in or Signing in 
        st.session_state.login = False
        st.session_state.register = False
        st.session_state["authentication_status"] = None
        st.session_state.reset_pwd = False
        if st.session_state.without_loggin_button:
            st.session_state.without_loggin_button = False
            st.session_state.user_id = f"user_{generate_random_number()}"
            st.session_state.compliance_button = False
            st.session_state.compliance_message = False

        st.rerun()

    # We open the Option menu if clicked on
    if st.sidebar.button("**Options**"):
        st.session_state.option_menu = True
        st.session_state.reset_pwd = False
        st.rerun()
    
    if st.session_state.option_menu:    
        modal = Modal(
        "Options menu",
        key="menu",
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
            quitting_option = st.button("**Quit**")

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
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
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
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)

                    st.session_state.successful_reset_pwd = True

                    st.rerun()
            except Exception as e:
                st.error(e)

        # We check if the compliance_message was asked to the user, mandatory in the first connexion
        try:
            compliance_message = authenticator.get_credential_information(st.session_state["email"], 'compliance_message')
            compliance_statut = authenticator.get_credential_information(st.session_state["email"], 'compliance_statut')
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
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)

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
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)

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
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)

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




