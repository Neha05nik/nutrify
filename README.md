# Nutritional AI: A Chatbot for Personalized Nutritional Advice

## Overview:
Nutritional AI is a chatbot designed to provide tailored nutritional advice using Retrieval-Augmented Generation (RAG)

Nutritional AI ensures highly accurate and personalized responses to user queries, enhancing the overall user experience.

Nutritional AI will be linked to my other project: https://github.com/RubenHf/project_nutrition.git (https://nutritious-food-app.rubenhalifa.com/)

Nutritional AI has been build to work on Streamlit: https://nutritional-chatbox.streamlit.app/

Nutritional AI is powered either by Open-AI gpt-3.5-turbo or Mistral-7B-v0.2

## Key Features:
Tailored Nutritional Advice: Nutritional AI offers differents style of answers.

Retrieval-Augmented Generation: Nutritional AI combines the power of retrieval-based methods with generation models to deliver precise and context-aware responses.

Scientific Database: Nutritional AI's knowledge base is enriched with information sourced from scientific abstracts, ensuring the advice provided is grounded in the most cited nutritional research.

Retrieval-Augmented Generation + Database: Script that scrap NCBI database to feed the database use by the Nutritional AI

## Getting Started

### Prerequisites:

To get started with Nutritional AI, ensure you have the following prerequisites installed:

- Python 3.11 or higher
- streamlit==1.31.0
- ragstack-ai==0.6.0
- openai==1.12.0
- tiktoken==0.5.2
- langchain_openai==0.0.3
- langchain_community==0.0.16
- mistralai==0.0.12
- langchain==0.1.4
- streamlit_modal==0.1.2
- boto3==1.34.39
- PyJWT==2.8.0
- bcrypt==4.1.2
- extra_streamlit_components==0.1.60

  You will also have to get multiple keys and setup a .streamlit/secrets.toml file
  For the database, I use [AstraDB](https://astra.datastax.com/)https://astra.datastax.com/
  You can setup a database, free of charge. You will have to have a token from Astra, an Endpoint and the Collection.
  To retrieve articles from NCBI, you will have to create a key
  To vectorize the texts into the database, you can choose either GPT encoder or Hugging face (get also a key).
  For using the chat generator, you will have to get an Open AI key if you use GPT or an Mistral key if you want to use Mistral.

  Others things included in the project, but that can be taken out: Email for sending forgotten password and Qrcode.

### Installation:
Clone the repository and install the necessary dependencies:

```bash
$ git clone https://github.com/RubenHf/RAG_Scientific_Article.git
$ cd RAG_Scientific_Article
$ pip install -r requirements.txt

## Usage:
### To launch the chatbot
```bash
$ streamlit run main.py

### To launch the AstraDB script feeder
```bash
$ streamlit run NCBI_retriever.py



