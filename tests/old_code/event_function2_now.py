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
추가해야하는 기능
1) 마이크 음성 크기 줄이기. -> WINDOW 마이크 볼륨 기능
2) 정확도 평가를 위한 코드 적용 -> 말한 뒤에 제대로 EVENT FLAG를 출력하는지 COUNT
3) 이벤트 FLAG로 사용하는 정답 TEXT가 추가 될 수 있으니, event_flag 번호를 얻는 방법을 index로 말고 다른 걸로 하는 방법 찾기


"""

import time
from RealtimeSTT import AudioToTextRecorder
import utils
import params


if __name__ == '__main__':

    check_mic_connection = utils.check_mic_connection()

    recorder_config = {
        'spinner': False,
        'model': 'small',
        'language': 'ko',
        'silero_sensitivity': 0.2,
        'webrtc_sensitivity': 3,
        'reduce_noise_flag' : False,
        'silero_use_onnx' : True,
        # 'wake_words_sensitivity' : 0.0015, # 현재 실험해보니까 0.0008 ~ 0.00099까지 그냥 무음상태, oww prediction score 값이 출력됨.토마스로 외치니까 0.0015까지 올라감. 크게 외치면 0.002까지 올라감. 근데 아직 사용 못할듯, oww 성능이 제대로 안나옴  
        # 'wake_word_buffer_duration' : 1.0,
        # 'wakeword_backend' : "oww",
        # 'openwakeword_model_paths' : "C:/Users/admin/Desktop/STT/RealtimeSTT/wake_word_model/thomas_oww.onnx",
        # 'wake_word_timeout' : 3.0
    }

    recorder = AudioToTextRecorder(**recorder_config)

    print("Say something...")

    while (True):

        start_time = time.time()
        inf_text = recorder.text().rstrip(".?!")

        # score_list에 다 저장하고 가장 높은 score의 인덱스가 event로 간주

        score_list = []

        # event_flag code dev
        for ref_text in params.event_flag.keys():

            # ref_text, inf_text similarity calculation
            is_similar, similarity = utils.levenshtein_similarity(
                junk=utils.isjunk, ref_text=ref_text, inf_text=inf_text, threshold=0.8)

            score_list.append(similarity)

        max_similarity = max(score_list)
        if max_similarity <= params.max_similarity_threshold:
            event_flag = None
        else:
            event_flag = score_list.index(max_similarity) + 1


        print(f"inf_text : {inf_text}\n")
        print(f"similarity : {max_similarity}\n")
        print(f"event_flag : {event_flag}\n")
        
        # event_function using event_flag
        utils.event_function(event_flag)

        end_time = time.time()
        process_time = end_time - start_time

        print(f"Processing Time : {process_time}\n")
