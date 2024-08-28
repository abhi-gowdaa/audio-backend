from fastapi import FastAPI, File, UploadFile
from pydub import AudioSegment, silence
import os
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile

app = FastAPI()

origins=[
    "http://localhost:3000",
    "https://audio-silence-detection.onrender.com/"
 ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

def convert_mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    return wav_path

def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3, \
         NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        
        # Save the uploaded MP3 file
        temp_mp3.write(await file.read())
        temp_mp3_path = temp_mp3.name
        temp_wav_path = temp_wav.name

    # here we convert MP3 to WAV
    wav_path = convert_mp3_to_wav(temp_mp3_path, temp_wav_path)
    
 
    myaudio = AudioSegment.from_wav(wav_path)
    dBFS=myaudio.dBFS #so this is overall softness of the audio

    normalized_sound = match_target_amplitude(myaudio, -20.0)
    length_Of_Audio=len(normalized_sound)/1000

    silences = silence.detect_silence(myaudio, min_silence_len=2000, silence_thresh=dBFS-16)
    silence_In_sec = [((start),(stop)) for start,stop in silences]
 
    timeStamp=[]

    for chunks in silence_In_sec:
        timeStamp.append( [chunk/1000 for chunk in chunks])

    # Clean up temporary files
    os.remove(temp_mp3_path)
    os.remove(temp_wav_path)

    
    return [length_Of_Audio,timeStamp]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
