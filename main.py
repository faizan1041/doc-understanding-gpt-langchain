from telegram.ext import Updater, MessageHandler, Filters
from typing import Any, List, Dict
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI
from local_vector_store import ingest_docs
from config.config import *
import openai
from urllib.parse import urlparse
import os
from pathlib import Path  # Import pathlib
from langchain import PromptTemplate, HuggingFaceHub, LLMChain

import google.generativeai as genai

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])


from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from langchain.llms import GooglePalm

from config.config import *


template = "Hey, Google here. So you want me to analyze a document. Please upload it!"

class DocumentAnalyzer:
    def __init__(self):
        self.analyzing_document = False
        self.document_uploaded = False
        self.index_type = "documents"
        self.conversation_history = []
        self.file_path = None
        self.chat_history = []
        self.document_names = set()
        self.initialize_apis()
        self.selected_api = None
        print("Server started... ")

    def initialize_apis(self):
        self.chat = ChatOpenAI(verbose=True, temperature=0)
        self.fact_llm = GooglePalm(temperature=0)


    def run_llm(self, query: str, chat_history: List[Dict[str, Any]] = []) -> Any:
        docsearch = ingest_docs(self.file_path, self.index_type)
        if any(keyword in query.lower() for keyword in {"google", "google palm", "Google"}):
            qa = ConversationalRetrievalChain.from_llm(
                llm=self.fact_llm,  
                retriever=docsearch.as_retriever(),
            )
            return qa({"question": query, "chat_history": chat_history})
        else:
            qa = ConversationalRetrievalChain.from_llm(
                llm=self.chat,  
                retriever=docsearch.as_retriever(),
            )
            return qa({"question": query, "chat_history": chat_history})
    

    def analyze_document(self, query):
        generated_response = self.run_llm(query, self.chat_history)
        formatted_response = generated_response['answer']
        self.chat_history.append((query, generated_response["answer"]))
        return formatted_response


    def process_message(self, update, context):
        user_message = update.message.text
        keywords = {"document", "documents", "file", "analyze", "analyse", "report"}

        if self.analyzing_document:
            print("Analyzing document: -------> ")
            # Continue analyzing the document
            self.conversation_history.append({"role": "user", "content": user_message})
            response = self.analyze_document(user_message)
            self.conversation_history.append({"role": "assistant", "content": response})
            update.message.reply_text(response)
        elif any(keyword in user_message.lower() for keyword in keywords) and not self.document_uploaded:
                self.analyzing_document = True
                self.document_uploaded = False
                update.message.reply_text("You want to analyze a document. Please upload the document.")
        else:
            print("I did not see a document so Im here")
            # Continue regular conversation
            self.conversation_history.append({"role": "user", "content": user_message})
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history
            )
            assistant_reply = response.choices[0].message["content"]
            update.message.reply_text(assistant_reply)
            self.conversation_history.append({"role": "assistant", "content": assistant_reply})



    def download_and_analyze(self, update, context):
        if update.message.document:
            print("---------------- Document Found ------------------")
            file_id = update.message.document.file_id
            print(f"file ID: {file_id}")
            print("--------------------------------------------------")
            document = context.bot.get_file(file_id)
            self.document_names.add(document)
            file_extension = Path(document.file_path).suffix.lower()
            if file_extension in ['.pdf', '.docx', '.txt']:
                parsed_url = urlparse(document.file_path)
                filename = os.path.basename(parsed_url.path)
                self.file_path = f'{OUTPUT_DIR}/{filename}'
                document.download(self.file_path)
                self.document_uploaded = True
                docsearch = ingest_docs(self.file_path, self.index_type)
                response = "You uploaded a document. Please ask anything about it."
                self.analyzing_document = True
            else:
                response = "Unsupported file format. Please upload a PDF, DOCX, or TXT document."
                    
            self.conversation_history.append({"role": "assistant", "content": response})
            update.message.reply_text(response)
        if self.analyzing_document and context.bot.get_file(update.message.document):
            document = context.bot.get_file(update.message.document)
            self.document_names.add(document)
            file_extension = Path(document.file_path).suffix.lower()
            if file_extension in ['.pdf', '.docx', '.txt']:
                parsed_url = urlparse(document.file_path)
                filename = os.path.basename(parsed_url.path)
                self.file_path = f'{OUTPUT_DIR}/{filename}'
                document.download(self.file_path)
                self.document_uploaded = True
                update.message.reply_text("Document uploaded. Ask away.")
            else:
                update.message.reply_text("Unsupported file format. Please upload a PDF, DOCX, or TXT document.")
 
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    doc_analyzer = DocumentAnalyzer()

    text_handler = MessageHandler(Filters.text & ~Filters.command, doc_analyzer.process_message)
    document_handler = MessageHandler(Filters.document & ~Filters.command, doc_analyzer.download_and_analyze)

    dispatcher.add_handler(text_handler)
    dispatcher.add_handler(document_handler)

    updater.start_polling()
    updater.idle()
    

if __name__ == "__main__":
    main()

