import re
from openai import OpenAI
import os
import dotenv

# Cargar las variables de entorno
dotenv.load_dotenv()

# Configura tu clave de API

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def clean_string(text):
    # Reemplazar \n con espacios
    text = text.replace('\\n', ' ')
    # Reemplazar \ con nada
    text = text.replace('\\', '')
    # Eliminar espacios duplicados
    text = re.sub(' +', ' ', text)
    
    return text.strip()

def clean_cite(text):
    # Expresión regular para encontrar cualquier cosa entre 【 y 】
    pattern = r'【[^】]+】'
    # Reemplazar las coincidencias con una cadena vacía
    text = re.sub(pattern, '', text)

    return text.strip()

def extract_html_content(text):
    # Eliminar cualquier línea que contenga <script src="..."></script>
    script_src_pattern = r'<script\s+src="[^"]*"></script>'
    text = re.sub(script_src_pattern, '', text, flags=re.IGNORECASE)

    # Dividir el contenido en líneas
    content = text.splitlines()

    # Eliminar las líneas que coinciden con la expresión regular
    pattern_to_remove = re.compile(r'<script\s+src="[^"]*"></script>', re.IGNORECASE)
    content = [line for line in content if not pattern_to_remove.search(line)]

    # Unir las líneas nuevamente
    text = '\n'.join(content)

    # Buscar la primera etiqueta HTML
    pattern = r"(<[^>]+>)"
    match = re.search(pattern, text)
    
    if match:
        # Encuentra la posición donde comienza la primera etiqueta HTML
        html_start = match.start()
        message_content = text[:html_start].strip()
        html_content = text[html_start:].strip()
        return message_content, html_content
    else:
        return text, None

def upload_file(path= "C:/Users/BENRAM/Documents/POC_Wealth/files/Estados_financieros_(PDF)96767630_202312.pdf"):
    """
    Uploads a file to openai
    """
    
    file = client.files.create(
        file=open(path, "rb"),
        purpose='assistants'
        )
    
    return file.id

def delete_file():
    """
    Deletes a file from openai
    """

def create_thread():
    """
    Creates a thread for an assistant
    """