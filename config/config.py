<<<<<<< HEAD
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


INDEX_NAME = "langchain-telegram-index"

DB_DIR = 'data/db'
INPUT_FILE_PATH = 'data/input/sample.pdf'
=======
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


INDEX_NAME = "langchain-telegram-index"

DB_DIR = 'data/db'
INPUT_FILE_PATH = 'data/input/sample.pdf'
>>>>>>> 46136b5b1e138d910cb9b03bf2f2e08b619929e4
OUTPUT_DIR = 'data/output'