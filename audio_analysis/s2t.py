import os
import io
import uuid
import flask
import shutil
import requests

from pydub import AudioSegment
from pydub.utils import mediainfo

from google.cloud import speech
from time import gmtime, strftime
from termcolor import colored

#GLOBALS
CWD = "."
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= "./codiste.json"
DEFAULT_LANGUAGE_CODE = "en-US"
MIN_WORD_COUNT = 2
FILLERWORDS_LIST = ['umm', 'uhh','err']
FALSE_STATUS = 400
OK_STATUS = 200

"""Converting Audio File to WAV Format"""
def get_wav(audio_url, filename):
    # get audio data from file
    response = requests.get(audio_url)

    try:
        os.makedirs(os.path.join(CWD, "audio", f"{filename}"))
    except:
        raise ValueError("Folder Already Exists")
        
    with open(os.path.join(CWD, "audio", f"{filename}/{filename}"), 'wb') as f:
        f.write(response.content)
       
    audio = AudioSegment.from_file(os.path.join(CWD, "audio", f"{filename}/{filename}"))
    audio = audio.set_channels(1)
    file_handle = audio.export(os.path.join(CWD, "audio", f"{filename}/{filename}.wav"), format='wav')
    info = mediainfo(os.path.join(CWD, "audio", f"{filename}/{filename}")) 
    
    return int(info['sample_rate']), float(info['duration'])
    
"""Transcribing audio using Google Cloud Speech APIs"""
def transcribe(filename, sample_rate):
    # Instantiates a client
    client = speech.SpeechClient()

    
    with io.open(os.path.join(CWD, "audio", f"{filename}/{filename}.wav"), "rb") as audio_file:
        content = audio_file.read()

    #speech to text
    audio = speech.RecognitionAudio(content=content) 
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        sample_rate_hertz=sample_rate,
        language_code=DEFAULT_LANGUAGE_CODE,
    )

    response = client.recognize(config=config, audio=audio)
    
    shutil.rmtree(os.path.join(CWD, "audio", f"{filename}"))
    return response

"""Finding repeatation of unique words from transcription"""
def find_repetation_of_unique_words(wordlist):
    wordfreq = [wordlist.count(p) for p in set(wordlist)]
    return dict(list(zip(wordlist,wordfreq)))
       
"""Calculte metrices"""     
def get_metrices(transcribed_output, audio_url, audio_duration):
     
    transcription = ""
    
    for result in transcribed_output.results:
        transcription = transcription + result.alternatives[0].transcript
        
    transcription_lst = transcription.split(" ")
    wordsPerMinute = int(len(transcription_lst)/(audio_duration/60))
    
    repeated_words = find_repetation_of_unique_words(transcription_lst)
    
    commonWords = []
    for key, value in repeated_words.items():
        if value >= MIN_WORD_COUNT:
            commonWords.append(key)
            
    print(commonWords)

    fillerWords = []
    
    for word in FILLERWORDS_LIST:
        if word in transcription_lst:
            fillerWords.append(word)
            
    print(fillerWords)
    
    return wordsPerMinute, commonWords, fillerWords

"""Analysing Audio, This needs to be multi-threaded"""
def analyse(par):   
    try:
        audio_url = par['audio_url']  
    except:
        audio_url = None
        
    if audio_url == None or audio_url == "":
        return {"data": {}, "status": False, "message": "Audio URL Null"}, FALSE_STATUS
    
    filename = 'audio_'+ str(uuid.uuid4()) + '_' + str(strftime("%Y_%m_%d-%H_%M_%S", gmtime()))
    
    try:
        sample_rate, audio_duration = get_wav(audio_url, filename)  
        transcribed_output = transcribe(filename, sample_rate)
        wordsPerMinute, commonWords, fillerWords = get_metrices(transcribed_output, audio_url, audio_duration)
    except Exception as e:
        print(e)
        try:
            shutil.rmtree(os.path.join(CWD, "audio", f"{filename}"))
        except:
            pass
        return {"data": {}, "status": False, "message": "Processing Failed"}, FALSE_STATUS
        
    data = {"wordsPerMinute": wordsPerMinute, 
            "commonWords": commonWords, 
            "fillerWords": fillerWords, 
            "total_duration": audio_duration,
            "name": os.path.basename(audio_url),
            "data": str(strftime("%Y_%m_%d-%H_%M_%S", gmtime()))}
    
    return flask.jsonify(data), OK_STATUS
