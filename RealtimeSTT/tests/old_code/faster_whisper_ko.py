from faster_whisper import WhisperModel
import os

# model = WhisperModel("arc-r/faster-whisper-large-v2-Ko")
model = WhisperModel(os.path.join(os.path.dirname(os.path.abspath(__file__)), "faster_whisper_model", "medium"))

segments, info = model.transcribe("D:/STT_V1/STT/RealtimeSTT/tests/test_data/환자분통증이느껴지시나요_1003.wav")
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))