import sounddevice as sd
import scipy.io.wavfile as wav

sample_rate = 16000
duration = 5

print("Recording ...")

audio = sd.rec(int(sample_rate*duration), samplerate=sample_rate, channels=1, dtype='int16')
sd.wait()
print("Recording finished.")

drill = ["S_Max_C2292371", "S_Max_C22X0050", "S_Max_M25", "air_gun"]

wav.write("S_Max_C22X0050.wav", sample_rate, audio)
