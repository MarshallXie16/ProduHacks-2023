from flask import Flask, request, jsonify, render_template
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import openai
import base64
import io
import os
import pygame
from pygame import mixer

# Set up your Google and OpenAI API credentials
google_credentials_path = "C:/Users/Lyric/Downloads/basic-strata-382418-6f8ce922e875.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials_path
openai.api_key = "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"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    audio_data = request.json.get('audio_data')

    if not audio_data:
        return jsonify({"error": "No audio data provided."}), 400

    try:
        # Decode base64 audio data and convert it to the expected format for Google's Speech-to-Text API
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        audio_file = io.BytesIO(audio_bytes)
        # Transcribe the audio using Google's Speech-to-Text API
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_file.read())
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=48000,
            language_code="en-US",

        )

        response = client.recognize(config=config, audio=audio)
        if not response.results:
            return jsonify({"error": "No speech detected."}), 400

        transcript = response.results[0].alternatives[0].transcript

        # Generate response using OpenAI's API
        api_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful tutor. You will ask me revision questions based on my notes. Be as detailed as possible and be polite. Start by asking only one question."},
                {"role": "user", "content": f'{transcript}'}
            ]
        )
        parse_response = api_response['choices'][0]['message']['content']
        print(api_response)
        # Convert the generated response to an audio file using Google's Text-to-Speech API
        tts_client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=parse_response)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        tts_response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        from pydub import AudioSegment
        from pydub.playback import play

        with open("temp.mp3", "wb") as f:
            f.write(tts_response.audio_content)

        import sounddevice as sd
        import soundfile as sf

        # Load audio file
        data, samplerate = sf.read('temp.mp3')

        # Play audio file
        sd.play(data, samplerate)

        # Wait for audio to finish playing
        sd.wait()
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=4000, debug=True)


