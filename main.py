from flask import Flask, render_template, request
from flask_socketio import SocketIO
import openai
import docx2txt
# Imports the Google Cloud client library
from google.cloud import speech

app = Flask(__name__, static_folder='static')
# OpenAI API key
openai.api_key = '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'
# idk wtf this does
socketio = SocketIO(app)

# homepage
@app.route('/', methods=['GET'])
def homepage():
    return render_template('homepage.html')

# signup page
@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

# login page
@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global uploaded_file
    file = request.files['input_document']
    try:
        file.save('uploads/' + file.filename)
        file_path = file.filename
        try:
            # for text files
            print(f'the name of the uploaded file is: {file.filename}')
            with open("uploads/" + file_path, "r") as file:
                uploaded_file = file.read()
                # should return openAI API response
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
            output.write(api_response)
            output.close()
        return render_template("chat.html", starter=api_response)
    except:
        # error page if invalid file
        return render_template("error.html")


# obtains next chat response
@app.route("/get")
def get_bot_response():
    # gets user message from text input
    user_input = request.args.get('msg')
    # creates prompt with past context
    prompt = create_prompt(user_input, prompt_list)
    print(prompt)
    # performs API call to get response
    bot_response = get_chat_response(prompt)
    print(bot_response)
    return bot_response

def get_api_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful tutor. You will ask me revision questions based on my notes. Be as detailed as possible and be polite. Start by asking only one question."},
            {"role": "user", "content": f'Can you quiz me? Here are my notes: {user_input}'}
        ]
    )
    parse_response = response['choices'][0]['message']['content']
    update_message(parse_response, prompt_list)
    return parse_response

def get_chat_response(prompt):
    try:
        # calls API and returns a JSON file
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a helpful tutor. You will ask me revision questions based on my notes. Be as detailed as possible and be polite. Start by asking only one question."},
                {"role": "user", "content": f'{prompt}'}
            ]
        )
        print(response)
        parse_response = response['choices'][0]['message']['content']
        update_message(parse_response, prompt_list)
        print(parse_response)
        return parse_response

    except Exception as e:
        print("ERROR", e)



# takes user_input and converts to prompt
def create_prompt(user_input, pl):
    # adds human message to prompt_list
    update_message(user_input, pl)
    # takes prompt list and converts to string
    prompt = "".join(pl)
    # returns the prompt, which will be used in API call
    return prompt

def process_response(api_response):
    return api_response

def update_message(message, prompt_list):
    # appends message to prompt_list
    prompt_list.append(message)

if __name__ == '__main__':
    prompt_list = []
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
