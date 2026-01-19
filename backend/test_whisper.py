from speech_to_text import transcribe

result = transcribe("data/audio/test_audio.mp3")
text = result["text"]
segments = result["segments"]
print(text)