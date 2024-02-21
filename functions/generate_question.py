from mistralai.models.chat_completion import ChatMessage
from functions.loading_models import load_OpenAI_GPT4
from langchain.schema import HumanMessage

def get_openAI_requery(question):
    try:
        content = f"""
            # Question:
            "{question}"
            Given the above question, rephrase and expand it to help you do better answering.
            Maintain all information in the original question.
            Return only the rephrased question and in english.
        """

        gpt4_model = load_OpenAI_GPT4()

        new_question = gpt4_model.invoke([HumanMessage(content=content)])
        
        return new_question.content
    
    except Exception as e: 
        print(e)
        return question

def get_mistral_requery(client_mistral, question):
    try:
        content = f"""
            # Question:
            "{question}"
            Given the above question, rephrase and expand it to help you do better answering.
            Maintain all information in the original question.
            Return only the rephrased question and in english.
        """
        
        new_question = client_mistral.chat(
            model="mistral-small",
            messages=[ChatMessage(role="user", content=content)],
            temperature=0.4
                )
        return question#new_question.choices[0].message.content
    
    except Exception as e: 
        print(e)
        return question