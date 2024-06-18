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
#dotenv.load_dotenv()

# Configura tu clave de API
client = OpenAI(api_key='sk-proj-ZAsIEIovHmy64dt4zNI7T3BlbkFJb14c0xpjDSExkNS46TDv')

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

def delete_thread(thread_id):
    try:
        response = client.beta.threads.delete(thread_id)
        if response['deleted']:
            print(f"Thread {response['object']} deleted")
        else:
            print(f"Thread {response['object']} not deleted")
    except Exception as e:
        print(f"Error deleting thread {response['object']}: {e}")

def delete_threads_client(id_cliente):
    try:
        delete_thread(thread_dict[id_cliente][0])
        delete_thread(thread_dict[id_cliente][1])
        thread_dict[id_cliente] = []
    except Exception as e:
        print(f"Error deleting threads: {e}")

def create_threads(id_cliente):
    try:
        if id_cliente not in thread_dict:
            thread_id = client.beta.threads.create()
            thread_id2 = client.beta.threads.create()

            thread_dict[id_cliente] = [thread_id.id, thread_id2.id]
            print(f"Threads created with ids {thread_id.id}, {thread_id2.id} ")
        else:
            print(f"Threads already created")
    except Exception as e:
        print(f"Error creating threads for {id_cliente}: {e}")

thread_dict = {}

files_dict = {
    'banchile': 'file-XrxQALifGFNHL9TJ5JtrrHNA',
    'bci': 'file-8yXk6ipdnshkugMHQHHfivRE',
    'santander': 'file-0RWWUf50OhdTQ7vROnNizgdR',
    'fintual': 'file-339MfWdTQgLvgAgXHirx6nXq'
}

def get_assistant_response(message_context, message_content, assistant_id, thread_id, message_files=[]):
    """
    Sends a message to the assistant and waits for the response.
    :param message_content: The content of the message to send.
    :return: The response from the assistant.
    """
    if message_context == 0:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role='user',
            content=message_content,
        )
    elif message_context == 1 and len(message_files) > 0:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role='user',
            content=message_content,
            attachments=[
                {"file_id": files_dict[message_files[0]], "tools": [{"type": "file_search"}]}
            ],
        )
    elif message_context == 2 and len(message_files) > 1:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role='user',
            content=message_content,
            attachments=[
                {"file_id": files_dict[message_files[0]], "tools": [{"type": "file_search"}]},
                {"file_id": files_dict[message_files[1]], "tools": [{"type": "file_search"}]}
            ],
        )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    response = wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)
    response = utils.extract_html_content(response)
    if response[1] is None:
        result = {
            "context": message_context,
            "natural_response": utils.clean_cite(html.unescape(response[0]))
        }
    else:
        result = {
            "context": message_context,
            "natural_response": utils.clean_cite(html.unescape(response[0])),
            "chart": html.unescape(response[1]).replace('\"', '\'').replace('\\n', '').replace('\\', '')
        }

    return result

assistant_id_array = ["asst_8LUnQH0Z2sJz6aqHhhC5e2vv",
                      "asst_8LUnQH0Z2sJz6aqHhhC5e2vv",
                      "asst_YaaHWKvHKWxn6DbSbJx1YKwW"]

#==== Cuando se haga el deploy hay que crear nuevos threads basados en el inicio de sesion
thread_id_array = ["thread_x1BUWgcQja74t8qizNkOfUUZ",
                   "thread_x1BUWgcQja74t8qizNkOfUUZ",
                   "thread_HgJqhmuqLO6fmxBIJIzBlSBG"]

async def handle_client(websocket, path):
    async for message in websocket:
        print(f"Received message: {message}")
        data = json.loads(message)

        if data['context'] == 4:
            create_threads(data['code'])
            response = {
                'context': 4,
                'message': '400',
                'ip': data['code']
            }

        else:
            assistant_id = assistant_id_array[data['context']]
            thread_id = thread_dict.get(data['code'], thread_id_array[data['context']])[data['context'] % 2]
            response = get_assistant_response(data['context'], data['message'], assistant_id, thread_id)
            
        await websocket.send(json.dumps(response, ensure_ascii=False))

async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
