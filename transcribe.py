from torch import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from pathlib import Path
import librosa
import os
import soundfile as sf
import datetime
import shutil
import subprocess

SAMPLE_RATE = 16000

# How long each chunk is in seconds
BLOCK_LENGTH = 45

# BASE_PATH = "C:/Users/frost/OneDrive/Documents/audiorecorder/Transcribe_Path/"
# CONVERTED_AUDIO_PATH = "C:/Users/frost/OneDrive/Documents/audiorecorder/Converted_Audio_Path/"
# RESAMPLED_FOLDER = "C:/Users/frost/OneDrive/Documents/audiorecorder/Resampled_Folder/"
# AUDIO_REPORT_FOLDER = "C:/Users/frost/OneDrive/Documents/audiorecorder/Audio_Report/"

BASE_PATH = str(Path().absolute()).replace("\\", "/") + "/"
# BASE_PATH = str(Path().absolute()) + "\\"

CONVERTED = Path("converted/")
CONVERTED.mkdir(parents=True, exist_ok=True)
CONVERTED_AUDIO_PATH = str(CONVERTED.absolute()).replace("\\", "/") + "/"
# CONVERTED_AUDIO_PATH = str(CONVERTED.absolute()) + "\\"

RESAMPLED = Path("resampled/")
RESAMPLED.mkdir(parents=True, exist_ok=True)
RESAMPLED_FOLDER = str(RESAMPLED.absolute().replace("\\", "/")) + "/"
# RESAMPLED_FOLDER = str(RESAMPLED.absolute()) + "\\"

REPORT = Path("report/")
REPORT.mkdir(parents=True, exist_ok=True)
AUDIO_REPORT_FOLDER = str(REPORT.absolute()).replace("\\", "/") + "/"
# AUDIO_REPORT_FOLDER = str(REPORT.absolute()) + "\\"

# BASE_PATH = "C:/Users/Devin/Videos/wav2/audio/"
# CONVERTED_AUDIO_PATH = "C:/Users/Devin/Videos/wav2/pathconverted/"
# RESAMPLED_FOLDER = "C:/Users/Devin/Videos/wav2/resampled/"
# AUDIO_REPORT_FOLDER = "C:/Users/Devin/Videos/wav2/audioreport/"

EXTENSIONS_TO_CONVERT = ['.mp3','.mp4']

PROCESSOR = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-960h-lv60-self")
MODEL = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-large-960h-lv60-self")

def preprocessing(base_path, converted_audio_path):
    for file in os.listdir(base_path):
        file_name, file_extension = os.path.splitext(file)
        print("\nFile name: " + file)
        if file_extension == ".wav":
            shutil.copy(base_path + file, converted_audio_path + file)
        elif file_extension in EXTENSIONS_TO_CONVERT:
            subprocess.call(['ffmpeg', '-i', base_path + file, base_path + file_name + ".wav"])
            shutil.move(base_path + file_name + ".wav", converted_audio_path + file_name + ".wav")
            print(file + " is converted into " + file_name +".wav")
        else:
            print("ERROR: Unsupported file type")

def resample(file, sample_rate): 
    path = CONVERTED_AUDIO_PATH + file
    audio, sr = librosa.load(path, sr=sample_rate) 
    length = librosa.get_duration(audio, sr=sr)
    sf.write(os.path.join(RESAMPLED_FOLDER,file), audio, sr) 
    resampled_path = os.path.join(RESAMPLED_FOLDER,file) 
    return resampled_path, length

def asr_transcript(processor, model, resampled_path, length, block_length):
    start_time = datetime.datetime.now()
    chunks = length//block_length
    if length % block_length != 0:
        chunks += 1
    transcript = ""   
    stream = librosa.stream(resampled_path, block_length=block_length, frame_length=16000, hop_length=16000)
    print ('Every chunk is ',block_length,'sec. long')
    print("Number of chunks",int(chunks))
    for n, speech in enumerate(stream):
        current_time = datetime.datetime.now()
        time_elapsed = current_time - start_time
        print(f"Time Elapsed: {time_elapsed}")
        print ("Transcribing the chunk number " + str(n+1))
        separator = '\n'
        # separator = ' '
        # if n % 2 == 0:
        #     separator = '\n'
        transcript += generate_transcription(speech, processor, model) + separator
    print("Encoding complete. Total number of chunks: " + str(n+1) + "\n")
    return transcript

def generate_transcription(speech, processor, model):
    if len(speech.shape) > 1:
        speech = speech[:, 0] + speech[:, 1]   
    input_values = processor(speech, sampling_rate = SAMPLE_RATE, return_tensors="pt").input_values
    logits = model(input_values).logits             
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.decode(predicted_ids[0])
    return transcription.lower()

def generate_textfile(transcript, audio_report_folder, file, length):
    today = datetime.date.today()
    report = f"REPORT\nFile name: {file}\nDate: {today}" \
         f"\nLength: {datetime.timedelta(seconds=round(length,0))}" \
         f"\nFile stored at: {os.path.join(audio_report_folder, file)}.txt\n"
    report += transcript   
    filepath = os.path.join(audio_report_folder,file)
    text = open(filepath + ".txt","w")
    text.write(report)
    text.close()
    print("\nReport stored at " + filepath + ".txt")

def speech_to_text():
    preprocessing(BASE_PATH, CONVERTED_AUDIO_PATH)
    for file in os.listdir(CONVERTED_AUDIO_PATH):
        resampled_path, length = resample(file, SAMPLE_RATE)
        transcript = asr_transcript(PROCESSOR, MODEL, resampled_path, length, BLOCK_LENGTH)
        generate_textfile(transcript, AUDIO_REPORT_FOLDER, file, length)
    return transcript

if __name__ == "__main__":
    print(speech_to_text())