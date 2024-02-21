from functions.loading_models import load_OpenAI_GPT4, load_Mistral_SMALL
from langchain.schema import HumanMessage

def get_openAI_requery(question):
    try:
        content = f"""
            # Question:
            "{question}"
            Given the above question, rephrase and expand it to help you do better answering.
            Maintain all information in the original question.
            Only write the rephrased question and in english.
            YOUR ANSWER:
        """

        gpt4_model = load_OpenAI_GPT4()

        new_question = gpt4_model.invoke([HumanMessage(content=content)])
        
        return new_question.content
    
    except Exception as e: 
        print(e)
        return question

def get_mistral_requery(question):
    try:
        content = f"""
            # Question:
            "{question}"
            Given the above question, rephrase and expand it to help you do better answering.
            Maintain all information in the original question.
            Only write the rephrased question and in english.
            YOUR ANSWER:
        """
        mistral_small = load_Mistral_SMALL()

        new_question = mistral_small.invoke([HumanMessage(content=content)])

        return new_question.content

    except Exception as e: 
        print(e)
        return question