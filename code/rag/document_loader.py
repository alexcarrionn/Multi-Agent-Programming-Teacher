import os 
from langchain_community.document_loaders.pdf import PDFPlumberLoader 
from langchain_text_splitters import RecursiveCharacterTextSplitter
#Clase que se va a hacer cargo de cargar el documento PDF y dividirlo en partes más pequeñas para su procesamiento posterior.
class DocumentLoader:
    #Metodo que recibe la ruta del documento PDF, lo carga y lo divide en partes utilizando un text splitter.
    def load_document(self, path: str):
       