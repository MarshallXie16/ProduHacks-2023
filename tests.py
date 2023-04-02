import io
from google.cloud import speech_v1p1beta1 as speech
from google.oauth2 import service_account
import openai
from gtts import gTTS
from pygame import mixer
from flask import Flask, request, jsonify, render_template
import base64
import tempfile
from flask import Flask, request, jsonify
import os
import wave
import numpy as np
import pyaudio

app = Flask(__name__)

# Set up your Google and OpenAI API credentials
google_credentials_path = "C:/Users/Lyric/Downloads/basic-strata-382418-6f8ce922e875.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials_path
openai.api_key = "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"

@app.route('/')
def new():
    return render_template('new.html')

@app.route("/save_audio", methods=["POST"])
def save_audio():
    audio_file = request.files["audio"]
    audio_data = np.frombuffer(audio_file.read(), dtype=np.float32)
    record_audio("recorded_audio.wav", audio_data)
    return jsonify({"status": "success"})

@app.route("/record_audio", methods=["POST"])
def record_audio(filename, audio_data):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes((audio_data * (2**15 - 1)).astype(np.int16).tobytes())
    wf.close()
    p.terminate()


# processes audio
@app.route('/process_audio', methods=['POST'])
def process_audio():
    record_audio("user_audio.wav", seconds=3)
    text = audio_to_text("user_audio.wav")

    print(f"User: {text}")
    response = get_openai_response(text)
    print(f"AI: {response}")
    play_text(response)

'''# Records the audio
def record_audio(filename, seconds=3):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = seconds

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")

    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    '''

# convert audio to text using Google's Speech-to-Text API
def audio_to_text(filename):
    client = speech.SpeechClient()

    with io.open(filename, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        return result.alternatives[0].transcript

    return ""

# get a response from OpenAI's API
def get_openai_response(text):
    prompt = f"User: {text}\nAI:"
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.8,
    )

    return response.choices[0].text.strip()

# plays text as audio
def play_text(text):
    tts = gTTS(text, lang="en")

    # Close mixer if already initialized
    if mixer.get_init() is not None:
        mixer.music.stop()
        mixer.quit()

    # Save new audio file
    response_file = "responses/response.mp3"
    tts.save(response_file)

    # Initialize, load new audio file, and play
    mixer.init()
    mixer.music.load(response_file)
    mixer.music.play()

    # Wait for audio to finish playing
    while mixer.music.get_busy():
        pass

    # Close the mixer
    mixer.quit()

# Main loop
if __name__ == "__main__":
    app.run(debug=True)


'''while True:
    audio_filename = "user_audio.wav"
    record_audio(audio_filename)
    text = audio_to_text(audio_filename)
    print(f"User: {text}")

    response = get_openai_response(text)
    print(f"AI: {response}")

    play_text(response)'''

