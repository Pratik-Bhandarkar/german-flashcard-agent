# config.py
# Central configuration for the German Flashcard Agent.
# All settings, API keys, and feature flags live here.
# Never hardcode these values directly in agent or tool files.

import os
from dotenv import load_dotenv

# Load values from the .env file into the environment
load_dotenv()

# --- LLM Settings ---
# Toggle between local Ollama and OpenAI depending on environment
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"

# Used when USE_LOCAL_LLM is True
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Used when USE_LOCAL_LLM is False
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- DeepL Settings ---
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")

# --- Database Settings ---
# SQLite database path — lives in the data/ folder
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/flashcards.db")

# --- Pipeline Settings ---
# Supported input types for the parser agent
SUPPORTED_INPUT_TYPES = ["image", "pdf", "text"]

# --- Tesseract Settings ---
# Path to the Tesseract executable on Windows
# This is required because pytesseract is just a wrapper around the Tesseract program
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Target language for translations
DEEPL_TARGET_LANG = os.getenv("DEEPL_TARGET_LANG", "EN-GB")