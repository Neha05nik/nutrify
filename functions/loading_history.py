import streamlit as st
from functions.s3_files_functions import *

S3_BUCKET_NAME  = st.secrets["S3_BUCKET"]

def loading_conversation_history():
    # Archived conversations 
    st.sidebar.markdown("---")
    st.sidebar.title("Previous conversations")
    st.sidebar.markdown("---")

    # We count the number of conversations started
    nb_conversations = len(st.session_state.history_messages)
    bool_timeline = [True, True, True, True]

    # Show previous conversations if more than 1 started
    if nb_conversations > 1:
        # If the conversation is today's old
        if bool_timeline[0]:
            st.sidebar.subheader("Today's conversations")  
            bool_timeline[0] = False

        # We read from the most recent to oldest
        for i, conversation in enumerate(st.session_state.history_messages[::-1]):
            # Each text is visible as a button
            if conversation:
                title = conversation[0]['content']

                # We display title and subtitle on two separate rows in the button
                if st.sidebar.button(f"{title}", key=i):
                    # Upload the conversation when the button is clicked
                    st.session_state.messages = st.session_state.history_messages[nb_conversations -1 - i]
                    st.session_state.first_question = True

    if st.session_state.login:
        
        try:
            # We read from the most recent to oldest
            for i, conversation in enumerate(st.session_state.previous_conversation[::-1]):
                # Each text is visible as a button
                title = return_conversation(conversation)[0]['content']
                time_conversation = return_dates(conversation)[0]

                # If the conversation is today's old
                if return_time_difference(time_conversation, "days") == 0 and bool_timeline[0]:
                    st.sidebar.subheader("Today's conversations")  
                    bool_timeline[0] = False

                # If the conversation is one days' old
                elif return_time_difference(time_conversation, "days") == 1 and bool_timeline[1]:
                    st.sidebar.subheader("Yesterday's conversations")
                    bool_timeline[1] = False

                # If the conversation is seven days' old
                elif return_time_difference(time_conversation, "days") > 1 and return_time_difference(time_conversation, "days") <= 30 and bool_timeline[2]:
                    st.sidebar.subheader("Previous 7 days's conversations")
                    bool_timeline[2] = False
                
                # If the conversation is thirty days' old
                elif return_time_difference(time_conversation, "days") > 30 and bool_timeline[3]:
                    st.sidebar.subheader("Previous 30 days's conversations")
                    bool_timeline[3] = False

                # We display title and subtitle on two separate rows in the button
                if st.sidebar.button(f"{title}", key=i):
                    # Upload the conversation when the button is clicked
                    st.session_state.messages = return_conversation(conversation)
                    st.session_state.first_question = True
                    
        except Exception as e:
            # upload the log for bug 
            upload_bug_to_s3(S3_BUCKET_NAME, str(e))
            container = st.sidebar.container()
            container.error("Reload the page to see the previous conversations")