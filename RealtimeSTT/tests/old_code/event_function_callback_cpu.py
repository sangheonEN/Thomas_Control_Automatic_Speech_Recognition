"""
1. inf text similarity calculation using levenshtein_similarity
2. event flag calculation using max similarity score
3. Developing functions tailored to event flags (run voice file)
- Future work of robot control communication technology is necessary

window 기준
_transcription_worker -> torch.multiprocess
_audio_data_worker -> torch.multiprocess
_recording_worker -> threading.Thread

1. AudioToTextRecorder 객체 생성되자마자 아래 두 audio data worker는 계속 실행

_audio_data_worker data=stream.read(buffer_size)

_audio_data_worker audio_queue.put(processed_data)

2. 녹화 시작 flag가 True 되었을때,

_recording_worker self.frames.append(data)

3. 음성 감지 멈췄을때,

wait_audio self.audio=audio_array.astype(np.float32) / INT16_MAX_ABS_VALUE

transcribe self.parent_transcription_pipe.send((self.audio, self.language))
_audio_data_worker data=stream.read(buffer_size)

-----
2024/10/08 추가해야하는 기능
1) 마이크 음성 크기 줄이기. -> WINDOW 마이크 볼륨 기능
2) 정확도 평가를 위한 코드 적용 -> 말한 뒤에 제대로 EVENT FLAG를 출력하는지 COUNT
3) text() 호출시 콜백함수로 제어신호 event_function 전달 코드작성.
2024/10/08 3)까지 완료

2024/10/28 추가한 기능
1) Serial 통신을 활용한 int 형식 데이터 송수신 기능 추가
2024/10/28 완료

개발해야하는 기능
4) 이벤트 FLAG로 사용하는 정답 TEXT가 추가 될 수 있으니, event_flag 번호를 얻는 방법을 index로 말고 다른 걸로 하는 방법 찾기.
5) wake word 모델이 활성화된 후 토마스까지 text 추론 되는 문제 해결.
6) wake word 를 가지고 지금 처럼 wake word 말하고 한 문장 말하고 하는게 아니고 그냥 음성인식을 모듈을 활성화할지 안할지를 정하는 트리거로 사용할지 판단.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import logging
from RealTimeSTT_LEE.audio_recorder import AudioToTextRecorder
import utils


if __name__ == '__main__':

    recorder_config = {
        'spinner': False,
        'model': 'small',
        'language': 'ko',
        'silero_sensitivity': 0.2,
        'webrtc_sensitivity': 3,
        'reduce_noise_flag': False,
        'silero_use_onnx': True,
        'silero_deactivity_detection': True,
        'level': logging.ERROR,
        'device': 'cpu',

        # wake word args
        # 'post_speech_silence_duration' : 0.2,
        # 'wake_words_sensitivity' : 0.002, # 현재 실험해보니까 0.0008 ~ 0.00099까지 그냥 무음상태, oww prediction score 값이 출력됨.토마스로 외치니까 0.0015까지 올라감. 크게 외치면 0.002까지 올라감. 근데 아직 사용 못할듯, oww 성능이 제대로 안나옴
        # 'wake_word_buffer_duration' : 3.0,
        # 'wakeword_backend' : "oww",
        # 'openwakeword_model_paths' : "C:/Users/admin/Desktop/STT/RealtimeSTT/wake_word_model/hey_tho__ma__s.onnx",
        # 'wake_word_timeout' : 3.0
    }

    communicator_config = {
        'port': 'COM8',
        'baudrate': 9600,
        'timeout': 1,
        'input_type': 'int',
        'endianness': 'big', # 바이트 배열로 변환할 때의 바이트 순서 big or little
    }
    
    check_mic_connection = utils.check_mic_connection()
    communicator = utils.check_communicator(communicator_config)
    recorder = AudioToTextRecorder(**recorder_config)
    
    print("Say something...")

    try:

        while (True):

            start_time = time.time()
            recorder.text(utils.main_process, start_time, communicator)
            
    except KeyboardInterrupt:
        communicator.close()
        print("Serial protocol terminated due to KeyboardInterrupt\n")
