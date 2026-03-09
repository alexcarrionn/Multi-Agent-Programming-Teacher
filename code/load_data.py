"""
Script para cargar los documentos desde la carpeta data/...
Estructura de carpetas esperada en data/:
    data/
    ├── rubricas/         → source_id = "rubrica_<nombre>"
    ├── teoria/           → source_id = "teoria_<nombre>"
    ├── practicas/        → source_id = "practica_<nombre>"
    └── ejercicios/       → source_id = "ejercicio_<nombre>"
Formatos esperados: . pdf, . docx, . txt, . md, . ipynb, .xlsx

"""
import os
import sys 
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
import docx
import hashlib
from rich.console import Console
from rag.indexer import index_documents
from langdetect import detect
from config.settings import settings
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
console = Console()

# Aseguramos que el path raíz del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

#Primero validamos variables de entorno 
REQUIRED_ENV_VARS = ["QDRANT_URL", "QDRANT_API_KEY", "QDRANT_COLLECTION"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

if missing_vars:
    console.print(f"[bold red]Error: Las siguientes variables de entorno son obligatorias pero no están definidas: {', '.join(missing_vars)}[/bold red]")
    console.print(":warning: [yellow] Por favor, asegúrate de definir estas variables en tu archivo .env antes de ejecutar el programa.[/yellow]")
    sys.exit(1)

#Una vez que configuramos las variables de entorno, comprobramos que los docuemntos estan en español o el idioma en 
# en el que se quiera trabajar. Para ello configuramos una header con el idioma, detectamos el idioma y lo hacemos
EXPECTED_LANGUAGE = "es"  # Cambia esto si quieres trabajar con otro idioma


def load_pdf(file_path):
    """Función para cargar un archivo PDF y devolver su contenido como texto."""
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        console.print(f"[bold red]Error al leer el PDF {file_path}: {e}[/bold red]")
    
    return text

def load_txt(file_path):
    """Funcion para extraer el texto de un txt"""
    return file_path.read_text(encoding="utf-8", errors="ignore").strip()

def load_docx(file_path):
    """Funcion para extraer el texto de un docx"""
    doc = docx.Document(file_path)
    texto = []
    for para in doc.paragraphs:
        texto.append(para.text)
    return '\n'.join(texto)

def load_md(file_path):
    """Funcion para extraer el texto de un md"""
    return file_path.read_text(encoding="utf-8", errors="ignore").strip()

#Podriamos añadir mas funciones segun el tipo de documento que queramos cargar, por ejemplo para ipynb, xlsx, etc.

#una vez que hemos hecho las funciones que se encargaran de leer los datos de los documentos, definimos
# los tipos de documentos que se pueen cargar 
SUPPORTED_FORMATS = {
    ".pdf": load_pdf,
    ".txt": load_txt,
    ".docx": load_docx,
    ".md": load_md,
    #".ipynb": load_ipynb,
    #".xlsx": load_xlsx,
}

def create_hash(text: str) -> str:
    """Funcion que se encarga de crear un hash a partir del texto del documento, para detectar cambios en el mismo."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

#Creamos el source id a partir de la ruta, data_root es la carpeta /data

def create_source_id(file_path: Path, data_root: Path, text:str) -> str:
    """ Esta funcion se va a encargar de crear el source id de cada documento para poder guardarlo en la base 
    de datos vectorial. Para ello se usará la ruta relativa del fichero. 
    Ejemplo: data/Intoduccion_programacion/temas/tema1.pdf -> Intoduccion_programacion/temas/tema1"""

    ruta_relativa = file_path.relative_to(data_root)
    parts = list(ruta_relativa.parts) # Excluye la extensión y añade el nombre del archivo sin extensión

    if len(parts) == 1:
        #Quiere decir que el documento esta en la direccion /data directamente 
        return file_path.stem
    else:
        #Usamos la subcarpeta como prefijo y el nombre del fichero como sufijo
        subfolder = parts[0] # Obtenemos la subcarpeta
        name = file_path.stem # Obtenemos el nombre del fichero sin la extension
        hash_contenido = create_hash(text) # Creamos un hash del contenido del documento para detectar cambios en el mismo
        return f"{subfolder}_{name}_{hash_contenido}" #devolvemos el source id con el hash del contenido por si se cambia el documento 

#Funcion para detectar el idioma del texto del docuemnto 
def detect_language(text: str) -> str:
    #para simplicidad vamos a coger los primero 500 caracteres 
    try:
        return detect(text[:500])
    except Exception as e:
        console.print(f"[yellow]No se pudo detectar el idioma del texto: {e}[/yellow]")
        return None


#Funcion que cumprueba que se ha indexado con anterioridad un documento con el mismo source id. 
def source_already_indexed(source_id: str) -> bool:
    """Funcion que se encarga de comprobar si un documento con el mismo source_id ya ha sido indexado en QDrant."""
    #Primero creamos el cliente de QDrant
    client = QdrantClient(
            url = settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY,
        )

    #Si la coleccion no existe, no hay nada indexado
    if not client.collection_exists(settings.QDRANT_COLLECTION):
        return False

    #Buscamos si existe algun documento con el mismo source_id en la coleccion, 
    #para ello hacemos una consulta en la base de datos de QDrant
    results, _ = client.scroll(
    collection_name=settings.QDRANT_COLLECTION,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.source_id",
                match=models.MatchValue(value=source_id),
            )
        ]
    ),
    limit=1, # Solo necesitamos saber si hay al menos uno
    )

    return len(results) > 0


#Hacemos una funcion para cargar un unico documento
def load_document(file_path: Path, data_root: Path, replace_existing_source: bool = True) -> bool: 
    """Funcion que se encarga de carga un único documento, extraer su texto e indexarlo en QDrant."""
    extension = file_path.suffix.lower()

    #Comprobamos que el formato del documento es soportado
    if extension not in SUPPORTED_FORMATS:
        console.print(f"Formato no soportado: {file_path.name} ({extension})")
        return False

    #Extraemos el texto del documento usando la función correspondiente
    loader = SUPPORTED_FORMATS[extension]
    texto = loader(file_path)

    if not texto or not texto.strip():
        console.print(f"[yellow]El documento {file_path.name} está vacío o no se pudo extraer texto.[/yellow]")
        return False
    
    # Comprobamos el idioma del texto para saber si se utiliza o no
    idioma = detect_language(texto)
    if idioma and idioma != EXPECTED_LANGUAGE:
        console.print(f"[yellow]⚠ Idioma incorrecto ({idioma}), se omite: {file_path.name}[/yellow]")
        return False
    if idioma is None:
        console.print(f"[dim]No se pudo detectar idioma en {file_path.name}, se indexa igualmente.[/dim]")

    #Creamos el source_id a partir de la ruta del documento
    source_id = create_source_id(file_path, data_root, texto)

    #Comprobamos el indexado, si existe no hacemos nada.
    if source_already_indexed(source_id): 
        console.print(f"[blue]El documento {file_path.name} ya está indexado, se omite.[/blue]")
        return True

    #Indexamos el documento en QDrant
    index_documents(text=texto, source_id=source_id, replace_existing_source=replace_existing_source)
    console.print(f"[green]Documento indexado correctamente: {file_path.name} (source_id: {source_id})[/green]")
    return True

#Hacemos una funcion para cargar todos los documentos de la carpeta data/ y la subcarpeta elegida en el Rag correspondiente
def load_documents_from_folder(folder_path: Path, data_root: Path, replace_existing_source: bool = True) -> None:
    """Carga todos los documentos soportados de una carpeta (recursivamente) y los indexa en QDrant."""
    if not folder_path.exists() or not folder_path.is_dir():
        console.print(f"[bold red]La carpeta {folder_path} no existe o no es un directorio.[/bold red]")
        return

    #Obtenemos todos los archivos de la carpeta y subcarpetas que tengan un formato soportado
    archivos = [f for f in folder_path.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS]

    if not archivos:
        console.print(f"[yellow]No se encontraron documentos soportados en {folder_path}[/yellow]")
        return

    console.print(f"[bold blue]Se encontraron {len(archivos)} documentos en {folder_path}[/bold blue]")

    exitos = 0
    fallos = 0
    for archivo in archivos:
        resultado = load_document(archivo, data_root, replace_existing_source)
        if resultado:
            exitos += 1
        else:
            fallos += 1

    console.print(f"[bold green]Carga finalizada: {exitos} documentos indexados, {fallos} fallidos.[/bold green]")





