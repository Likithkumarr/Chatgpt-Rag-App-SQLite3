## 📄 Project Description: Chatgpt-rag-app
This is a Retrieval-Augmented Generation (RAG) application built with Python and Streamlit. It allows users to upload documents and have intelligent conversations with an AI that stays grounded in the provided context.

## ✨ Key Features
- Dual-LLM Logic:
     - Uses a primary model for standard queries and a specialized secondary model for "retries" when a user provides negative feedback.
- Contextual Retrieval:
     -  Integrates ChromaDB as a vector store to perform semantic searches on uploaded documents.
- Intelligent Fallback:
     - If the system cannot find an answer in your documents, it seamlessly falls back to a general AI response to ensure you are never left without an answer.
- Session Management:
     - Persists chat history across interactions using a custom SQL-based session store.

## 🛠️ Tech Stack
- Frontend: Streamlit
- Orchestration: LangChain
- LLM: Azure OpenAI (GPT models)
- Vector Database: ChromaDB
- Data Processing: NumPy & PyPDF2

## 🚀 Getting Started
- Clone the repo: git clone https://github.com/Likithkumarr/Chatgpt-rag-app.git
- Install dependencies: pip install -r requirements.txt
- Set up Environment Variables: Create a .env file with your Azure OpenAI keys.
- Run the App: streamlit run app.py
