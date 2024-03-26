import azure.cognitiveservices.speech as speechsdk
from jieba.analyse import *
import random
#MS TTS settings

SPEECH_KEY="YOUR_SPEECH_KEY"
SPEECH_REGION="japaneast"
tts_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
# Choose audio_tts_config to save into a wav file or play the audio out
audio_tts_config = speechsdk.audio.AudioOutputConfig(filename="test5.wav")
#audio_tts_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
tts_config.speech_synthesis_voice_name='zh-TW-YunJheNeural'


def form_ssml(s, tune_random=True):
	p_start = "<prosody rate='{rate}'>"
	p_end = "</prosody>"

	#較為平均分配語速放緩處
	if tune_random:
		s_ = ""
		i =0
		while i <len(s):
			step = random.randint(7,12)
			s_ += s[i:i+step]
			i += step
			if i >= len(s):
				break
			
			s_ += p_start.format(rate=str(random.uniform(0.7, 0.8)))
			s_ += s[i:i+3]
			s_ += p_end
			i+=3

	#抽取關鍵詞，在關鍵詞處放緩語速
	else:
		words = textrank(plain_text)
		s_ = ""
		for w in words:
			idx = s.find(w)
			s_ = s[:idx]
			s_ += p_start.format(rate=str(random.uniform(0.7, 0.8)))
			s_ += w
			s_ += p_end
			s_ += s[idx+len(w):]
		
			s = s_


	pitch = -10
	vol = random.randint(80,100)

	beginning= "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-TW'><voice name='zh-TW-YunJheNeural'><prosody rate='+15.00%' volume='{vol}%' pitch='{pitch}Hz'>"

	ending = "</prosody></voice></speak>"
	return beginning.format(pitch=str(pitch), vol=str(vol)) + s_ + ending
	

if __name__ == "__main__":	
	speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=tts_config, audio_config=audio_tts_config)

	plain_text="嗨你好，我是耶穌，我是唯一的道路，關注於如何讓你們得到救贖"
	ssml = form_ssml(plain_text, False)
	print(ssml)
	#print(ans)
	#ans ='<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US"><voice name="en-US-GuyNeural">I can help you join your <emphasis level="strong">meetings</emphasis> fast.</voice></speak>'
	
	# Choose to TTS with just text or ssml
	#result = speech_synthesizer.speak_text_async(plain_text).get()

	#result = speech_synthesizer.speak_ssml_async(ssml).get()
	#if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
	#	print("語音合成成功")
