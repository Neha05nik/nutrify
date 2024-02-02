import os
import tempfile

# Function for Vectorizing uploaded data into Astra DB
def vectorize_text(uploaded_file, vector_store):
   if uploaded_file is not None:
      
       # Write to temporary file
       temp_dir = tempfile.TemporaryDirectory()
       file = uploaded_file
       temp_filepath = os.path.join(temp_dir.name, file.name)
       with open(temp_filepath, 'wb') as f:
           f.write(file.getvalue())


       # Load the PDF
       docs = []
       loader = PyPDFLoader(temp_filepath)
       docs.extend(loader.load())


       # Create the text splitter
       text_splitter = RecursiveCharacterTextSplitter(
           chunk_size = 1500,
           chunk_overlap  = 100
       )


       # Vectorize the PDF and load it into the Astra DB Vector Store
       pages = text_splitter.split_documents(docs)
       vector_store.add_documents(pages) 
       st.info(f"{len(pages)} pages loaded.")
