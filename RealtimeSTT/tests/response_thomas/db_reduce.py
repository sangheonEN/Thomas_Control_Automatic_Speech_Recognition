import os
from pydub import AudioSegment
import numpy as np

base_dir = os.path.dirname(__file__)

# Load the MP3 file
audio_segment = AudioSegment.from_mp3(os.path.join(base_dir, "mynameisthomas.mp3"))

# Constants
INT16_MAX_ABS_VALUE = 32768.0  # Maximum absolute value for int16

# Load the MP3 file using pydub
output_filename = os.path.join(base_dir,"mynameisthomas_reduced.mp3")

# Convert the audio to raw PCM format
audio_raw_data = audio_segment.raw_data

# Get the sample width, frame rate, and channels from the AudioSegment
sample_width = audio_segment.sample_width
frame_rate = audio_segment.frame_rate
channels = audio_segment.channels

# Convert the raw PCM data to a numpy array
audio_array = np.frombuffer(audio_raw_data, dtype=np.int16)

# If the audio has multiple channels, reshape to separate them (assuming stereo)
if channels == 2:
    audio_array = audio_array.reshape((-1, 2))

# Normalize the audio data to float32
normalized_audio = audio_array.astype(np.float32) / INT16_MAX_ABS_VALUE

# Apply decibel reduction
dB_reduction = -20  # Example decibel reduction
scaling_factor = 10 ** (dB_reduction / 20)
processed_audio = normalized_audio * scaling_factor

# Convert the processed audio back to int16 format
processed_audio_int16 = (processed_audio * INT16_MAX_ABS_VALUE).astype(np.int16)

# If the audio was stereo, ensure to handle both channels correctly
if channels == 2:
    processed_audio_int16 = processed_audio_int16.reshape((-1, 2))

# Convert processed numpy array back to raw PCM bytes
processed_audio_raw_data = processed_audio_int16.tobytes()

# Create a new AudioSegment from the processed raw data
processed_audio_segment = AudioSegment(
    data=processed_audio_raw_data,
    sample_width=sample_width,
    frame_rate=frame_rate,
    channels=channels
)

# Save the modified audio to a new MP3 file
processed_audio_segment.export(output_filename, format="mp3")

print(f"Audio processing complete. Saved as '{output_filename}'.")
