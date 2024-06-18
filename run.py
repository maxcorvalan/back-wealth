import websockets
from openai import OpenAI
import os
import dotenv
import time
import logging
from datetime import datetime
import utils
import asyncio
import json
import html

# Cargar las variables de entorno
dotenv.load_dotenv()

# Configura tu clave de API

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

assistant_id = "asst_8LUnQH0Z2sJz6aqHhhC5e2vv"
thread_id = "thread_DzxRpmLRIOcWR3sqPtnME55L"

#message = 'necesito un gráfico comparativo de los ingresos de actividades ordinarias y los gastos de administración para los años 2022 y 2023.'

#message = client.beta.threads.messages.create(
#    thread_id = thread_id,
#    role='user',
#    content= message
#)
#
#run = client.beta.threads.runs.create(
#    thread_id = thread_id,
#    assistant_id= assistant_id
#)

def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """
    Waits for a run to complete and prints the elapsed time.
    :param client
    :param thread_id: The ID of the thread.
    :param run_id: The ID of the run.
    :param sleep_interval: Time in second to wait between checks.
    
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                return response
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)

def get_assistant_response(message_context, message_content):
    """
    Sends a message to the assistant and waits for the response.
    :param message_content: The content of the message to send.
    :return: The response from the assistant.
    """
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=message_content
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    response = wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)
    response = utils.extract_html_content(response)
    if response[1]==None:
        result = {
                        "context": message_context,
                        "natural_response": html.unescape(response[0])
                    }
    else:
        result = {
                        "context": message_context,
                        "natural_response": html.unescape(response[0]),
                        "chart" : html.unescape(response[1]).replace('\"', '\'').replace('\\n', '').replace('\\', '')
                    }
                
    return result


async def handle_client(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        data = json.loads(message)
        response = get_assistant_response(data['context'],data['message'])
        print(response)
        await websocket.send(json.dumps(response, ensure_ascii=False))


async def main():
    port = int(os.getenv('PORT', 8765))  # Default to 8765 if PORT not set
    async with websockets.serve(handle_client, '0.0.0.0', port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
