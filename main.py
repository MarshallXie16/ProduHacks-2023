from flask import Flask, render_template, request
from flask_socketio import SocketIO
import openai
import docx2txt
from flask import Flask, request, jsonify, render_template
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import openai
import base64
import io
import os
import pygame
from pygame import mixer
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
import soundfile as sf

app = Flask(__name__, static_folder='static')

# Set up your Google and OpenAI API credentials
google_credentials_path = "C:/Users/Lyric/Downloads/basic-strata-382418-6f8ce922e875.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials_path
# OpenAI API key
openai.api_key = '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'

# homepage
@app.route('/', methods=['GET'])
def homepage():
    return render_template('splash.html')

# signup page
@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

# login page
@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/signin', methods=['GET'])
def signin():
    return render_template('homepage.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global uploaded_file
    file = request.files['input_document']
    try:
        # download the uploaded file
        file.save('uploads/' + file.filename)
        file_path = file.filename
        try:
            # for text files
            print(f'the name of the uploaded file is: {file.filename}')
            with open("uploads/" + file_path, "r") as file:
                uploaded_file = file.read()
                api_response = get_api_response(uploaded_file)
                # processes and formats response
                processed_response = process_response(api_response)
        except:
            # for docx files
            uploaded_file = docx2txt.process("uploads/" + file_path)
            api_response = get_api_response(uploaded_file)
            processed_response = process_response(api_response)
        # writes chat history on a text file
        with open("chat_history.txt", "w") as output:
            output.write(processed_response)
            output.close()
        # starts the chatbot
        return render_template("chat.html", starter=api_response)
    except:
        # error page if invalid file
        return render_template("error.html")


# processes audio input
@app.route('/process_audio', methods=['POST'])
def process_audio():
    # obtains audio data
    audio_data = request.json.get('audio_data')
    # checks for invalid audio
    if not audio_data:
        return jsonify({"error": "No audio data provided."}), 400

    try:
        # Decode base64 audio data
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
        #write_chat_block(transcript)
        # generates response using ChatGPT API
        bot_response = get_audio_response(transcript)
        # Convert the generated response to an audio file using Google's Text-to-Speech API
        tts_client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=bot_response)
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

        # write decoded audio into mp3 file
        with open("temp.mp3", "wb") as f:
            f.write(tts_response.audio_content)

        # Load audio file
        data, samplerate = sf.read('temp.mp3')

        # Play audio file
        sd.play(data, samplerate)

        # Wait for audio to finish playing
        sd.wait()
        #write_chat_block(bot_response)
        return jsonify({"success": True})


    except Exception as e:
        return jsonify({"error": str(e)}), 500
def write_chat_block():
    pass
# obtains next chat response
@app.route("/get")
def get_bot_response():
    global prompt_list
    # gets user message from text input
    user_input = request.args.get('msg')
    # creates prompt with past context
    prompt = create_prompt(user_input, prompt_list)
    print(prompt)
    try:
        # performs API call to get response
        bot_response = get_chat_response(prompt)
    except:
        bot_response = "Sorry, but we have reached the limit of this conversation. Please start a new one."
    print(bot_response)
    print("prompt list:".format(prompt_list))
    return bot_response

# the initial chat response
def get_api_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Pretend you are my kind and helpful tutor. You will ask me revision questions based on my notes. Be as detailed as possible and only ask by one question at a time. Correct any mistakes I make and provide feedback on my answers. Start with only 1 question."},
            {"role": "user", "content": f'Can you quiz me? Here are my notes: {user_input}'}
        ]
    )
    parse_response = response['choices'][0]['message']['content']
    update_message(parse_response, prompt_list)
    return parse_response

# subsequent chat responses
def get_chat_response(prompt):
    try:
        # calls API and returns a JSON file
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "Pretend you are my kind and helpful tutor. You will ask me revision questions based on my notes. Be as detailed as possible and only ask by one question at a time. Correct any mistakes I make and provide feedback on my answers. Be as concise as possible."},
                {"role": "user", "content": f'{prompt}'}
            ]
        )
        # parses JSON response
        parse_response = response['choices'][0]['message']['content']
        # adds the new response onto the end of prompt list (for future context)
        update_message(parse_response, prompt_list)
        # return parse_response for display
        return parse_response

    except Exception as e:
        print("ERROR", e)



# takes user_input and converts to prompt
def create_prompt(user_input, pl):
    # adds human message to prompt_list
    update_message(user_input + " ", pl)
    # takes prompt list and converts to string
    prompt = "".join(pl)
    # returns the prompt, which will be used in API call
    return prompt

# processes API response
def process_response(api_response):
    return api_response

def update_message(message, prompt_list):
    # appends message to prompt_list
    prompt_list.append(message)

def get_audio_response(user_input):
    # creates prompt with past context
    prompt = create_prompt(user_input, prompt_list)
    print(prompt)
    try:
        # performs API call to get response
        bot_response = get_chat_response(prompt)
    except:
        bot_response = "Sorry, but we have reached the limit of this conversation. Please start a new one."

    return bot_response



if __name__ == '__main__':
    prompt_list = []
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
