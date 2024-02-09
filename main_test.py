import streamlit as st
import yaml

import streamlit_authenticator as stauth
from functions.send_mail import send_email

from yaml.loader import SafeLoader

from functions.gdpr_compliance import run_compliance_modal, get_compliance_message

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

if "login" not in st.session_state:
    st.session_state.login = False
else:
    st.session_state.login = st.session_state.login
    
if "login_button" not in st.session_state:
    st.session_state.login_button = False
else:
    st.session_state.login_button = st.session_state.login_button
if "register" not in st.session_state:
    st.session_state.register = False
else:
    st.session_state.register = st.session_state.register
    
if "sign_up_button" not in st.session_state:
    st.session_state.sign_up_button = False
else:
    st.session_state.sign_up_button = st.session_state.sign_up_button

if "forgot_pwd" not in st.session_state:
    st.session_state.forgot_pwd = False
else:
    st.session_state.sign_up_button = st.session_state.sign_up_button

if "forgot_pwd_button" not in st.session_state:
    st.session_state.forgot_pwd_button = False
else:
    st.session_state.forgot_pwd_button = st.session_state.forgot_pwd_button
    
if "successful_registration" not in st.session_state:
    st.session_state.successful_registration = False

if "successful_forgotten_pwd" not in st.session_state:
    st.session_state.successful_forgotten_pwd = False

if "successful_reset_pwd" not in st.session_state:
    st.session_state.successful_reset_pwd = False

if "reset_pwd" not in st.session_state:
    st.session_state.reset_pwd = False
else: 
    st.session_state.reset_pwd = st.session_state.reset_pwd

if "compliance_message_bool" not in st.session_state:
    st.session_state.compliance_message_bool = False



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

# When user wants to log in
if st.session_state.login == False:
    if st.sidebar.button("**Log in**"):
        st.session_state.login_button = True
        st.session_state.sign_up_button = False
        st.session_state.forgot_pwd_button = False
        st.rerun()

# When user wants to register
if st.session_state.register == False and st.session_state.login == False:
    if st.sidebar.button("**Sign up**"):
        st.session_state.login_button = False
        st.session_state.sign_up_button = True
        st.session_state.forgot_pwd_button = False
        st.rerun()

# When user forgot its password
if st.session_state.forgot_pwd == False and st.session_state.login == False:
    if st.sidebar.button("**Forgot password**"):
        st.session_state.login_button = False
        st.session_state.sign_up_button = False
        st.session_state.forgot_pwd_button = True
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

# When user is log in
if st.session_state.login:
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
        st.rerun()

    # Button to reset password
    elif st.sidebar.button("**Reset password**"):
        st.session_state.reset_pwd = True
        st.rerun()

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

    st.session_state.compliance_message_bool = False

    compliance_statut = authenticator.get_credential_information(st.session_state["email"], 'compliance_statut')
    
    get_compliance_message(compliance_statut)


#elif st.session_state["authentication_status"]:



