import asyncio
import websockets
import ssl
import paho.mqtt.client as mqtt
import json
import configparser

# Config files
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

HOST = config["API"]["host"]
API_KEY = config["API"]["api_key"]

# --- WSS configs ---
URL = "wss://192.168.0.35/ws"

# --- Mosquitto configs ---
BROKER = "mosquitto"
TOPIC = "data"

ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations("cert.pem")

mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

async def client():
    print("Verbinden met de server...")

    try:
        async with websockets.connect(URL, ssl=ssl_context) as ws:
            print("Verbonden met de server.")

            # authorization
            await ws.send(API_KEY)
            print(f"API {API_KEY} verzonden, wacht op bevestiging...")

            # initiële response
            naam = await ws.recv()
            print("Initieel bericht ontvangen:", naam)

            counter = 1
            while True:
                await ws.send("get")
                print("------------------")
                print(f"{counter}: Get-commando verzonden, wacht op antwoord...")
                print("------------------")

                msg = await ws.recv()
                print(f"Message recieved: {msg}")

                decoded_msg = decode(msg)
                print(f"Decoded message: {decoded_msg}")

                mqtt_client.publish(TOPIC, decoded_msg)

                await asyncio.sleep(5)  # wacht 5 seconden voordat je het volgende bericht stuurt
                counter += 1

    except Exception as e:
        print("Fout opgetreden:", e)

def decode(msg):
    print("Decoding message...")

    data = json.loads(msg)

    shift = data["caesarcode"]
    encrypt_name = data["encrypted_name"]
    encrypt_msg = data["encrypted_boodschap"]

    name = caesar(shift, encrypt_name)
    message = caesar(shift, encrypt_msg)

    data_out = json.dumps({
        "encrypted_name": encrypt_name,
        "encrypted_boodschap": encrypt_msg,
        "caesarcode": shift,
        "decrypted_name": name,
        "boosdschap": message
    })

    print("Message decoded...")
    return data_out


def caesar(key, message):
    new_message = ""

    print(f"Decoding with key: {key}")

    for i in message:
        elem_int = ord(i)

        if(elem_int >= 65 and elem_int <= 90):
            new_message += chr((elem_int - 65 - key) % 26 + 65)
        elif (elem_int >= 97 and elem_int <= 122):
            new_message += chr((elem_int - 97 - key) % 26 + 97)
        else:
            new_message += chr(elem_int)
        
    return new_message
    


print("Starten Broker...")
mqtt_client.connect(BROKER, 1883, 60)
mqtt_client.loop_start()

print("Starten client...")
asyncio.run(client())