import os
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware

# =========================
# CREATE FASTAPI APP
# =========================

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# FIX: You cannot use allow_origins=["*"] with allow_credentials=True
# It will cause strict browser CORS failures (Failed to Fetch).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False, # Changed to False
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    query: str

# =========================
# INITIALIZE GLOBAL MODELS
# =========================

print("Loading Embeddings and LLM models...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
print("Embeddings Model Loaded")

pipe = pipeline(
    "text2text-generation",
    model="google/flan-t5-small",
    max_new_tokens=512
)
llm = HuggingFacePipeline(pipeline=pipe)
print("LLM Loaded")

prompt = PromptTemplate.from_template("""You are an expert AI assistant. Provide a clear, well-structured answer to the question based on the provided context.

Guidelines:
1. Give a direct, concise answer without repetition
2. Use proper formatting with paragraphs and bullet points where appropriate
3. If the context doesn't contain the answer, say so clearly
4. Do not repeat the same information multiple times
5. Keep the response focused and relevant

Context: {context}

Question: {question}

Provide a clear, structured answer:""")

# Global state for the RAG chain
qa_chain = None

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def clean_response(text):
    # ... (Keep your exact clean_response function here, no changes needed)
    if not text:
        return "No response generated."
    
    if "page_content='" in text:
        try:
            start = text.find("page_content='") + len("page_content='")
            end = text.rfind("'") if text.rfind("'") > start else len(text)
            text = text[start:end]
        except:
            pass
    
    text = text.replace('\\n', ' ').replace('\\t', ' ')
    text = text.replace("\'n", " ").replace("'n", " ")
    text = text.replace(' n ', ' ')
    text = re.sub(r'(\w+)-n([a-z])', r'\1-\2', text)
    text = re.sub(r'(\w+)\s+no([a-z])', r'\1 o\2', text)
    text = re.sub(r'(^|[\s.,!?;:])n([A-Za-z])', r'\1\2', text)
    text = re.sub(r'\s+n\s+', ' ', text)
    text = text.replace(' nof ', ' of ')
    text = re.sub(r"\w+='[^']*',?\s*", "", text)
    text = re.sub(r'\w+=[^\s,]+,?\s*', "", text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace(' .', '.').replace(' ,', ',')
    
    sentences = text.split('. ')
    unique_sentences = []
    seen = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence not in seen and len(sentence) > 10:
            seen.add(sentence)
            unique_sentences.append(sentence)
    
    cleaned = '. '.join(unique_sentences)
    cleaned = cleaned.strip()
    
    if cleaned and not cleaned[-1] in '.!?':
        cleaned += '.'
    
    return cleaned

# =========================
# API ENDPOINTS
# =========================

# FIX: Removed `async` from def. Heavy CPU tasks and shutil operations 
# block the async event loop and cause ERR_CONNECTION_RESET.
@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    global qa_chain
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
    file_path = f"temp_{file.filename}"
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"Saved uploaded file: {file_path}")
        
        # Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print("PDF Loaded Successfully")
        
        # Split Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        docs = text_splitter.split_documents(documents)
        print(f"Text Split into {len(docs)} chunks")
        
        # Store in FAISS
        vectorstore = FAISS.from_documents(docs, embeddings)
        print("Vector Database Created")
        
        # Create Retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Update Global RAG Chain
        qa_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
        )
        print("RAG Chain Updated Successfully")
        
        return {"message": "File uploaded and processed successfully", "filename": file.filename}
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
        
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/ask")
def ask_question(data: Question):
    global qa_chain
    if qa_chain is None:
        raise HTTPException(status_code=400, detail="Please wait for the PDF to finish processing before asking questions.")
        
    try:
        print(f"Processing question: {data.query}")
        raw_response = qa_chain.invoke(data.query)
        cleaned_response = clean_response(raw_response)
        return {"answer": cleaned_response, "raw_length": len(raw_response), "cleaned_length": len(cleaned_response)}
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the answer.")