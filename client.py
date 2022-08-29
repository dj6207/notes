import pyaudio
import socket
import threading
from datetime import datetime

HEADER = 64
ENCODE_FORMAT = "utf-8"
DISCONNECT_MSG = "quit"
RECORD = "record"
STOP = "stop"
HELP = "help"
TIME = "time"

COMMANDS = """
record   Starts recording audio
stop     Stops recording audio
quit     Disconnect client
help     Displays list of commands
"""

AUDIO = pyaudio.PyAudio()
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

CLIENT = socket.gethostbyname(socket.gethostname())
CMD_PORT = 5050
AUD_PORT = 5060
CMD_ADDRESS = (CLIENT, CMD_PORT)
AUD_ADDRESS = (CLIENT, AUD_PORT)

def send_cmd(msg, cmd_clientsocket):
    message = msg.encode(ENCODE_FORMAT)
    msg_len = len(message)
    send_len = str(msg_len).encode(ENCODE_FORMAT)
    send_len += b' ' * (HEADER - len(send_len))
    cmd_clientsocket.send(send_len)
    cmd_clientsocket.send(message)

def record_command(recording):
    if recording.is_set():
        print("Recording had already started")
    else:
        print("Start Recording")
        recording.set()

def stop_command(recording):
    if recording.is_set():
        print("Stopped Recording")
        recording.clear()
    else:
        print("Recording has not started")

def help_command():
    print(COMMANDS)

def time_command(recording, start_time):
    if recording.is_set():
        current_time = datetime.now()
        elapsed = current_time - start_time
        print(f"Time Elapsed: {elapsed}")
    else:
        print("Recording has not started")

def call_commands(command, recording, start_time):
    cmd = {
        RECORD : lambda : record_command(recording),
        STOP : lambda : stop_command(recording),
        TIME : lambda : time_command(recording, start_time)
    }
    try:
        cmd[command]()
    except KeyError as _:
        help_command()

def manage_cmd(recording, connected):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cmd_socket:
            cmd_socket.connect(CMD_ADDRESS)
            connected.set()
            start_time = datetime.now()
            while True:
                command = input(">>> ")
                send_cmd(command, cmd_socket)
                if command == DISCONNECT_MSG:
                    print("Disconnecting from server")
                    break
                call_commands(command, recording, start_time)
    except socket.error as msg:
        print(f"CMD Socket Error: {msg}")
    finally:
        connected.clear()
        recording.clear()

def manage_aud(recording, stream, connected):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as aud_socket:
            aud_socket.connect(AUD_ADDRESS)
            while connected.is_set():
                if recording.is_set():
                    data = stream.read(CHUNK)
                    aud_socket.send(data)
    except socket.error as msg:
        print(f"AUD Socket Error: {msg}")
    finally:
        stream.close()
        recording.clear()

def start():
    recording = threading.Event()
    connected = threading.Event()
    recording.clear()
    connected.clear()
    stream = AUDIO.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    CMD_thread = threading.Thread(target=manage_cmd, args=(recording, connected))
    AUD_thread = threading.Thread(target=manage_aud, args=(recording, stream, connected))
    CMD_thread.start()
    AUD_thread.start()

if __name__ == "__main__":
    start()