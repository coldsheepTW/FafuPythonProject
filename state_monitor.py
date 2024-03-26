#from ast import mod
import os
import time
import numpy as np
import azure.cognitiveservices.speech as speechsdk
from openai import OpenAI
from audio2face_streaming_utils import push_audio_track_stream
from audio2face_streaming_utils import push_audio_track
from audio2face_streaming_utils import push_empty_chunks, push_empty, push_track_delay
from text_filter import text_filter
from makeTTS import form_ssml
from threading import Thread
import soundfile
import random
import socket # for TCP socket communications with Unreal Engine
import cv2

# socket settings
HOST, PORT= "localhost", 9999


# Microsoft ASR settings
SPEECH_KEY="YOUR_SPEECH_KEY"
SPEECH_REGION="japaneast"
#asr_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
asr_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
asr_config.speech_recognition_language="zh-TW"
asr_config.set_profanity(speechsdk.ProfanityOption.Raw)
audio_asr_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=asr_config, audio_config=audio_asr_config)

#MS TTS settings
#tts_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
tts_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)

audio_tts_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
tts_config.speech_synthesis_voice_name='zh-TW-YunJheNeural'

#speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=tts_config, audio_config=audio_tts_config)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=tts_config, audio_config=None)


# GPT settings
OPENAI_API_KEY="YOUR_OPENAI_KEY"
#client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY)
gpt_region = 'taiwan'
paras = {}
paras['taiwan'] = {}
paras['taiwan']['max_tokens'] = 750
paras['taiwan']['penalty'] = 0.1

#CV2 face detection settings
cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
video_capture = cv2.VideoCapture(0)

human_threshold = 500 #看現場遠近調整數值，用來判定人的正臉是否已足夠靠近(長+寬)

def recognize_from_microphone():

    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
        return True, speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        return False, None
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
        return False, None

def get_gpt_resutls(question):
	# After fine tunning GPT, this prompt can be simplified in the future.
	gpt_prompt = "假設你是耶穌，你有時可引述聖經，請簡短回答此問題，並在回答內去掉假設部分，若難以回答或問題不明確可請對方再次提問：" + question
		
	response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role":"user",
                "content": gpt_prompt,
            }
        ],
        max_tokens=400,
        temperature=0.7,
    )

	ans = response.choices[0].message.content
	print(ans)
	return ans


class ChainState:
	def __init__(self):
		#TODO: redesign these two status types again to add face recognition
		#self.idle = True
		#self.hasUser = False

		self.listening = True
		self.thinking = False
		self.speaking = False


if __name__ == "__main__":

	chain_state = ChainState()

	#Settings of push audio data to Audio2Face
	url = "localhost:50051"  # ADJUST
	instance_name = "/World/audio2face/PlayerStreaming"
	sf = 16000

	default_ans_audio_path = "wavs/dont_want_answer.wav"
	thinking_audio_paths = ["wavs/think1.wav","wavs/think2.wav","wavs/think3.wav","wavs/think4.wav"]
	

	while True:
		#TODO: Add hasUser with cv2 face detection
		#TODO: Add socket TCP to push status to UE
		if not chain_state.listening:
			continue

		if chain_state.listening and not chain_state.thinking and not chain_state.speaking:
			#TODO: Empty task only for idle status, will be removed after UE animation done.
			empty_task = Thread(target=push_empty, args=[url, sf, instance_name] )
			empty_task.start()
			print("Listeing...")
			success, question = recognize_from_microphone()

		if success: #Go to chatGPT3 if ASR succeeded
			chain_state.listening = False
			chain_state.thinking = True
			print("Starting GPT...")
			# Delay task is called to buy more time for GPT respond
			data,sr = soundfile.read(random.choice(thinking_audio_paths), dtype="float32")
			delay_task = Thread(target=push_track_delay, args=[url, data, sf, instance_name, chain_state] )
			delay_task.start()
	
			result = get_gpt_resutls(question)
			ans = text_filter(result)
			
			print("Starting TTS...")    
			# default_ans_audio_path speaks:"啊，我不想回答這個問題" if there are no text left after text_filter
			data,sr = soundfile.read(default_ans_audio_path, dtype="float32")
			if len(ans) > 0:
				ans = form_ssml(ans)
				speech_synthesis_result = speech_synthesizer.speak_ssml_async(ans).get()
				wav_data = speech_synthesis_result.audio_data
				data = np.frombuffer(wav_data, dtype=np.int16, offset=44).astype(np.float32) / 32767.0
				if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
					print("語音合成成功")

			print("Speaking...")
			while chain_state.speaking:
				time.sleep(0.2)

			chain_state.thinking = False
			chain_state.speaking = True

			# Push audio to Omniverse Audio2Face
			push_audio_track(url, data, sf, instance_name)

			chain_state.speaking = False
			chain_state.listening = True

		else:
			chain_state.speaking = False
			chain_state.listening = True
			
