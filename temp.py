from google.cloud import speech_v1p1beta1 as speech
import io
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/C:\Users\Lyric\Downloads\\basic-strata-382418-6f8ce922e875.json"

def transcribe_audio_file(file_path):
    client = speech.SpeechClient()

    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US"
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

if __name__ == "__main__":
    file_path = "C:\Users\Lyric\Downloads\DON'T QUIT - Motivational Speech.wav"
    transcribe_audio_file(file_path)

