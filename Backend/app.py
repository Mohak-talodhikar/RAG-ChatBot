import os
import re
import sqlite3
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
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

# =========================
# CHAT HISTORY DATABASE
# =========================

DB_PATH = "chats.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        pdf_filename TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT,  -- 'user' or 'assistant'
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )''')
    conn.commit()
    conn.close()

init_db()

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

def save_chat(conversation_id, role, content, pdf_filename=None):
    """Save a message to the chat history."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
              (conversation_id, role, content))
    c.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
              (conversation_id,))
    conn.commit()
    conn.close()

def get_chat_messages(conversation_id):
    """Get all messages for a conversation."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
    messages = c.fetchall()
    conn.close()
    return [{"role": msg[0], "content": msg[1]} for msg in messages]

def create_conversation(title, pdf_filename=None):
    """Create a new conversation and return its id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO conversations (title, pdf_filename) VALUES (?, ?)",
              (title, pdf_filename))
    conn.commit()
    conversation_id = c.lastrowid
    conn.close()
    return conversation_id

def get_all_conversations():
    """Get all conversations with their message counts."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT c.id, c.title, c.pdf_filename, c.created_at, 
                 (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as msg_count
                 FROM conversations c ORDER BY c.updated_at DESC""")
    convos = c.fetchall()
    conn.close()
    return [(id, title, pdf_filename, created_at, msg_count) for id, title, pdf_filename, created_at, msg_count in convos]

# =========================
# API ENDPOINTS
# =========================

@app.get("/chats")
def list_chats():
    """Get all conversations with message counts and last updated time."""
    conversations = get_all_conversations()
    return conversations

@app.post("/chats")
def create_chat():
    """Create a new conversation."""
    title = "New Conversation"
    # The backend already has a default title, but we can extract if provided
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO conversations (title) VALUES (?)", (title,))
    conn.commit()
    conversation_id = c.lastrowid
    conn.close()
    return {"id": conversation_id, "title": title}

@app.get("/chats/{conversation_id}")
def get_chat(conversation_id: int):
    """Get a specific conversation with all its messages."""
    messages = get_chat_messages(conversation_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, pdf_filename, created_at FROM conversations WHERE id = ?", (conversation_id,))
    convo = c.fetchone()
    conn.close()
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": {"id": conversation_id, "title": convo[0], "pdf_filename": convo[1], "created_at": str(convo[2]), "messages": messages}}

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
        
        # Create a new conversation for this PDF
        conv_id = create_conversation(title=file.filename, pdf_filename=file.filename)
        save_chat(conv_id, "system", f"PDF uploaded: {file.filename}", pdf_filename=file.filename)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE conversations SET pdf_filename = ? WHERE id = ?", (file.filename, conv_id))
        conn.commit()
        conn.close()
        
        return {"message": "File uploaded and processed successfully", "filename": file.filename, "conversation_id": conv_id}
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
        
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/ask")
def ask_question(data: Question, background_tasks: BackgroundTasks):
    global qa_chain
    if qa_chain is None:
        raise HTTPException(status_code=400, detail="Please wait for the PDF to finish processing before asking questions.")
        
    try:
        print(f"Processing question: {data.query}")
        
        # Save user message
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM conversations ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        conversation_id = row[0] if row else None
        
        if conversation_id is None:
            # Create a default conversation if none exists
            conversation_id = create_conversation(title="New Conversation")
        
        save_chat(conversation_id, "user", data.query)
        
        raw_response = qa_chain.invoke(data.query)
        cleaned_response = clean_response(raw_response)
        
        # Save assistant message
        save_chat(conversation_id, "assistant", cleaned_response)
        
        # Refresh conversation data for response
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT updated_at FROM conversations WHERE id = ?", (conversation_id,))
        updated_at = c.fetchone()[0]
        conn.close()
        
        return {"answer": cleaned_response, "raw_length": len(raw_response), "cleaned_length": len(cleaned_response), "conversation_id": conversation_id, "updated_at": updated_at}
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the answer.")