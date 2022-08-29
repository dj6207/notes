import socket
import threading
import shutil
import wave
import datetime
from pathlib import Path

HEADER = 64
DECODE_FORMAT = "utf-8"
DISCONNECT_MSG = "quit"
RECORD = "record"
STOP = "stop"

CHANNELS = 1
RATE = 44100

TRANSCRIBE = Path("transcribe/")
TRANSCRIBE.mkdir(parents= True, exist_ok= True)

FILE_EXTENSION = ".wav"

# For Linux
BASE_PATH = str(Path().absolute()).replace("\\", "/") + "/"
TRANSCRIBE_PATH = str(TRANSCRIBE.absolute()).replace("\\", "/") + "/"

# For Windows
# BASE_PATH = str(Path().absolute()) + "\\"
# TRANSCRIBE_PATH = str(TRANSCRIBE.absolute()) + "\\"


# BASE_PATH = "C:/Users/frost/OneDrive/Documents/audiorecorder/auto-note-taker/"

SERVER = socket.gethostbyname(socket.gethostname())
CMD_PORT = 5050
AUD_PORT = 5060
CMD_ADDRESS = (SERVER, CMD_PORT)
AUD_ADDRESS = (SERVER, AUD_PORT)
CMD_SERVERSOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
CMD_SERVERSOCKET.bind(CMD_ADDRESS)
AUD_SERVERSOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
AUD_SERVERSOCKET.bind(AUD_ADDRESS)

def create_wavfile(frames):
    output_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + FILE_EXTENSION
    wf = wave.open(output_name, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    try:
        shutil.move(BASE_PATH  + output_name, TRANSCRIBE_PATH  +  output_name)
    except FileNotFoundError as fnf:
        print(fnf)

def record_command(recording):
    if not recording.is_set():
        recording.set()

def stop_command(recording, frames):
    if recording.is_set():
        recording.clear()
        create_wavfile(frames)
        frames.clear()

def disconnect_command(recording, frames):
    recording.clear()
    frames.clear()

def print_command(cmd_addr, cmd):
    print(f"{cmd_addr} {cmd}")

def call_command(command, recording, frames, cmd_addr):
    cmd = {
        RECORD : lambda : record_command(recording),
        STOP : lambda : stop_command(recording, frames),
        DISCONNECT_MSG : lambda : disconnect_command(recording, frames)
    }
    try:
        cmd[command]()
        print_command(cmd_addr, command)
    except KeyError as _:
        print_command(cmd_addr, command)


def handle_cmd(cmd_conn, cmd_addr, frames, recording):
    try:
        while True:
            cmd_len = cmd_conn.recv(HEADER).decode(DECODE_FORMAT)
            if cmd_len:
                cmd_len = int(cmd_len)
                cmd = cmd_conn.recv(cmd_len).decode(DECODE_FORMAT)
                call_command(cmd, recording, frames, cmd_addr)
    except socket.error as msg:
         print(f"Socket Error: {msg}" )

def handle_audio(aud_conn, recording, frames):
    while True:
        if recording.is_set():
            data = aud_conn.recv(2048)
            frames.append(data)

def start():
    print("Server starting")
    CMD_SERVERSOCKET.listen()
    AUD_SERVERSOCKET.listen()
    print(f"Server ip {SERVER}")
    print(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    recording = threading.Event()
    recording.clear()
    frames = []
    while True:
        cmd_conn, cmd_addr = CMD_SERVERSOCKET.accept()
        aud_conn, aud_addr = AUD_SERVERSOCKET.accept()
        print(f"{cmd_addr} Command Socket Connected")
        print(f"{aud_addr} Audio Socket Connected")
        cmd_thread = threading.Thread(target=handle_cmd, args=(cmd_conn, cmd_addr, frames, recording))
        cmd_thread.start()
        aud_thread = threading.Thread(target=handle_audio, args=(aud_conn, recording, frames))
        aud_thread.start()
    
if __name__ == "__main__":
    start()