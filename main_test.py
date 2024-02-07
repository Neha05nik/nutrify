import streamlit as st
import streamlit_authenticator as stauth
from functions.send_mail import send_email

import yaml
from yaml.loader import SafeLoader

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
else:
    st.session_state.successful_registration = st.session_state.successful_registration

# Draw a title and some markdown
st.title("Your personal nutritional AI ")
st.markdown("""Your generative AI will guide you in your nutritional choice!""")

if st.session_state.successful_registration:
    st.success('User registered successfully')
    st.session_state.successful_registration = False

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
        st.session_state.sign_up_button = True
        st.session_state.login_button = False
        st.session_state.forgot_pwd_button = False
        st.rerun()

# When user forgot its password
if st.session_state.forgot_pwd == False and st.session_state.login == False:
    if st.sidebar.button("**Forgot password**"):
        st.session_state.sign_up_button = False
        st.session_state.login_button = False
        st.session_state.forgot_pwd_button = True
        st.rerun()

# When user is log in
if st.session_state.login:
    st.sidebar.title(f'Welcome *{st.session_state["username"]}*')
    if st.sidebar.button("**Logout**"):
        # Restart the parameters for loging in or Signing in 
        st.session_state.login = False
        st.session_state.register = False
        st.session_state["authentication_status"] = None
        st.rerun()

if st.session_state.login_button:
    authenticator.login()

if st.session_state["authentication_status"] and st.session_state.login == False:
    st.session_state.login = True
    st.session_state.login_button = False
    st.rerun()
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')

if st.session_state.sign_up_button:
    try:
        email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(preauthorization=False)
        if email_of_registered_user:
            #st.session_state.login = True
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            st.session_state.successful_registration = True
        
            # Quitting the register and launching the login
            st.session_state.sign_up_button = False
            st.session_state.login_button = True

            st.rerun()
    except Exception as e:
        st.error(e)

if st.session_state.forgot_pwd_button:
    try:
        username_of_forgotten_password, email_of_forgotten_password, new_random_password = authenticator.forgot_password()
        # We ask for the email used in the registration
        if username_of_forgotten_password:
            # The developer should securely transfer the new password to the user.
            st.success('New password sent to your email')
            send_email(email_of_forgotten_password, new_random_password)
            st.session_state.password = new_random_password
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)

        elif username_of_forgotten_password == False:
            st.error('Username not found')

    except Exception as e:
        st.error(e)
   
#if st.session_state["authentication_status"]:
#    try:
 #       if authenticator.reset_password(st.session_state["username"]):
  #         st.success('Password modified successfully')
   # except Exception as e:
    #    st.error(e)



