import os
from dotenv import load_dotenv
 
load_dotenv()
 
CHROMA_PATH = "./chroma_db_pdf"
SQLITE_DB_PATH = "./app_data.db"
CSV_FEEDBACK_FILE = "good_responses.csv"

AZURE = {
    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
    "chat": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
    "embed": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
}