![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# **📘 RAG Chatbot using FAISS & HuggingFace**

An end-to-end Retrieval-Augmented Generation (RAG) chatbot that processes PDF documents and generates context-aware answers using semantic search and a local HuggingFace LLM.

---

## 👨‍💻 About the Project

This project demonstrates a complete implementation of a RAG pipeline, integrating:

>Document processing

>Vector embeddings

>Similarity search

>Large Language Model (LLM) inference

The chatbot answers user queries strictly based on the uploaded PDF content, reducing hallucination and improving factual accuracy.

---

## 🚀 Key Features

📄 PDF document ingestion

✂ Intelligent text chunking

🔢 Vector embedding generation

🗄 FAISS vector storage

🔎 Top-k similarity retrieval

🤖 Context-aware answer generation

🌐 FastAPI backend

💻 Simple frontend interface

---

## 🧠 System Architecture

>User Query

>Retriever (FAISS Similarity Search)

>Top-K Relevant Chunks

>Prompt Template (Context + Question)

>HuggingFace LLM (FLAN-T5)

>Final Generated Answer

---

## 🛠 Tech Stack

>Python

>FastAPI

>LangChain

>FAISS (Vector Database)

>Sentence Transformers

>HuggingFace Transformers

---

## 🤖 Models Used

🔹 Embedding Model

>sentence-transformers/all-MiniLM-L6-v2

>Used for semantic vector representation of text chunks

🔹 Vector Database

>FAISS

>Used for similarity search over embeddings

🔹 LLM

>google/flan-t5-small

>Framework: HuggingFace Transformers

>Pipeline Type: text2text-generation

>Max New Tokens: 512

>Integrated using HuggingFacePipeline

🔹 Why FLAN-T5?

>Lightweight and efficient

>Suitable for CPU-based inference

>Good instruction-following capability

---

## ⚙️ Installation & Setup

1️⃣ Clone Repository

```bash
git clone https://github.com/mohaktalodhikar/RAG_ChatBot.git
cd RAG-chatbot
```

2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```
Or manually:

```bash
pip install langchain langchain-community langchain-huggingface \
faiss-cpu transformers sentence-transformers pypdf fastapi uvicorn
```

3️⃣ Run Backend (FastAPI)

```bash
cd Backend
uvicorn app:app --reload
```

Backend runs at:

http://127.0.0.1:8000/docs

4️⃣ Run Frontend

```bash
cd frontend
python -m http.server 3000
```

Open in browser:

http://localhost:3000

---

## 📌 Learning Outcomes

>Through this project, I gained hands-on experience in:

>Building end-to-end RAG pipelines

>Vector similarity search

>Prompt engineering with retrieved context

>Integrating HuggingFace LLMs

>Backend API development with FastAPI


