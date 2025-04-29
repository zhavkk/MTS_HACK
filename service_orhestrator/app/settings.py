# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

RAG_URL = os.getenv("RAG_URL")
IE_URL = os.getenv("EIA_URL")
AS_URL = os.getenv("ASA_URL")
QSA_URL = os.getenv("QSA_URL")