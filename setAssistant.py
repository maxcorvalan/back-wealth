from openai import OpenAI
import os
import dotenv

# Cargar las variables de entorno
dotenv.load_dotenv()

# Configura tu clave de API

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def main():

    # Subir el archivo
    file_path = 'C:/Users/BENRAM/Documents/POC_Wealth/files/Estados_financieros_(PDF)96767630_202312.pdf'  # Cambia esto a la ruta de tu archivo .xlsx
    file = client.files.create(
        file=open(file_path, "rb"),
        purpose='assistants'
        )
    
    print(file.id)

    # Crear el asistente
    assistant = client.beta.assistants.create(
        name="Data visualizer",
        description="Ayudas a leer archivos financieros",
        model="gpt-4o",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
        tool_resources={
            "file_search": {
            "file_ids": [file.id]
            }
        }
        )
    print(assistant.id)

    
   
if __name__ == "__main__":
    main()
