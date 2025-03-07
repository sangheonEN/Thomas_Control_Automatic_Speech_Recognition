import os
import editdistance
import pyaudio
import sys
from pydub import AudioSegment
from pydub.playback import play
import time
import serial

import params
from serial_protocol import Serial_protocol


def main_process(inf_text, start_time, communicator, similarity_cal, similarity_config, recorder):
    """
        inf_text를 calculate_event_flag에 전달하여 최종 event_flag를 전달받고 communicator를 활용해 토마스에 event_flag를 sending!
        
        Args:
            inf_text: STT 추론 TEXT
            start_time: main process 실행 시작 시간
            communicator: utils.Serial_protocol(**communicator_config)

        Return: N/A

    """

    similarity_function = similarity_config["function"]
    threshold = similarity_config["threshold"]

    if similarity_function == "gestalt_pattern_matching":
        event_flag, max_similarity, _ = similarity_cal.gestalt_pattern_matching(inf_text, threshold)
    else:
        event_flag, max_similarity, _ = similarity_cal.sentence_transformers(inf_text, threshold)

    print(f"inf_text : {inf_text}\n")
    print(f"similarity : {max_similarity}\n")
    print(f"event_flag : {event_flag}\n")

    if event_flag == None:
        return
    
    else:
        
        # communicator.serial_state_check()
        # # Serial Protocol
        # communicator.sending_param(event_flag, recorder)
        
        # print(f"received data : {communicator.received_param()}\n")
        end_time = time.time()
        process_time = end_time - start_time

        print(f"Processing Time : {process_time}\n")

        # event_function using event_flag
        event_function(event_flag)
    


def run_voice_file(event_flag):
    """
        event_flag에 따라서 MP3 파일 재생

        Args:
            event_flag: 최종 event_flag 변수
        Return: N/A

    """
    base_dir = os.path.dirname(__file__)
    voice_dir = os.path.join(base_dir, "response_thomas")

    if event_flag == 1:
        audio = AudioSegment.from_mp3(os.path.join(voice_dir, "yes_hello.mp3"))
        play(audio)

    elif event_flag == 2:
        audio = AudioSegment.from_mp3(os.path.join(voice_dir, "thomas.mp3"))
        play(audio)

    elif event_flag == 3:
        print("어디가 불편하세요는 나중에 정의\n")

    elif event_flag == 4:
        audio = AudioSegment.from_mp3(os.path.join(voice_dir, "yes.mp3"))
        play(audio)

    elif event_flag == 8:
        print("통증이 느껴지세요는 나중에 정의\n")

    elif event_flag == 9:
        audio = AudioSegment.from_mp3(os.path.join(voice_dir, "yes.mp3"))
        play(audio)

    else:
        audio = AudioSegment.from_mp3(os.path.join(
            voice_dir, "Thankyouforyoureffort.mp3"))
        play(audio)


def event_function(event_flag):
    """
    event_flag 전달

    "환자분 안녕하세요": 1, # Run voice file
    "환자분 성함이 어떻게 되세요": 2, # Run voice file
    "어디가 불편하세요": 3, # Run voice file
    "환자분 진료 시작하겠습니다": 4, # Run voice file
    "환자분 아 하세요": 5, # Signal transmission of mouth opening motion
    "환자분 입을 더 크게 벌려보시겠어요": 6, # Signal transmission of a wide-opening mouth movement
    "통증이 느껴진다면 왼쪽 팔을 들어주세요": 7, # Signal transmission of a raising left arm
    "환자분 통증이 느껴지시나요": 8, # Run voice file
    "환자분 다시 진료 시작해도 될까요" : 9, # Run voice file
    "환자분 진료 끝났습니다 수고하셨습니다" : 10 # Run voice file

    """

    if event_flag == 5:

        print("Signal transmission of mouth opening motion\n")

    elif event_flag == 6:

        print("Signal transmission of a wide-opening mouth movement\n")

    elif event_flag == 7:

        print("Signal transmission of a raising left arm\n")

    elif event_flag == None:
        print("Nothing runs")

    else:
        run_voice_file(event_flag)


def calculate_cer(reference, hypothesis):
    """
        cer 계산 함수
        Args:
            reference: reference text
            hypothesis: prediction text
        Return: cer

    """
    distance = editdistance.eval(reference, hypothesis)
    cer = distance / len(reference) if len(reference) > 0 else 0
    return cer


def check_mic_connection():
    """
    Check if any microphone is connected.

    sys.exit(0) 또는 exit(0): 프로그램이 성공적으로 실행
    sys.exit(1), exit(1), 또는 기타 0이 아닌 코드: 프로그램에 오류가 발생했거나 비정상적으로 종료

    * 마이크가 연결 되지 않아도 audio device가 'name': 'Input ()'으로 잡히는 경우가 발생함. 나중에 다른 pc에서도 hostApi 번호가 인식되었을때 0이고 안되었을때 3이면 이걸 기준으로 판단해서 인식 안된 경우라고 예외처리 해보자. 
    인식되었을때 default_device 출력 내용: {'index': 1, 'structVersion': 2, 'name': 'Headset(LG HBS-PL6S AI)', 'hostApi': 0, 'maxInputChannels': 1, 'maxOutputChannels': 0, 'defaultLowInputLatency': 0.09, 'defaultLowOutputLatency': 0.09, 'defaultHighInputLatency': 0.18, 'defaultHighOutputLatency': 0.18, 'defaultSampleRate': 44100.0}
    인식 안되었을때 default_device 출력 내용: {'index': 1, 'structVersion': 2, 'name': 'Input ()', 'hostApi': 3, 'maxInputChannels': 2, 'maxOutputChannels': 0, 'defaultLowInputLatency': 0.01, 'defaultLowOutputLatency': 0.01, 'defaultHighInputLatency': 0.08533333333333333, 'defaultHighOutputLatency': 0.08533333333333333, 'defaultSampleRate': 44100.0}

    :return: True if a microphone is found, False otherwise.
    """
    audio = pyaudio.PyAudio()

    try:
        # Try to get the default input device info
        default_device = audio.get_default_input_device_info()
        input_device_index = default_device['index']

        # print(f"default_device: {default_device}")
        # print(f"input_device_index: {input_device_index}")

        # Check if a valid input device index is found
        if input_device_index is not None:
            print(f"Microphone '{default_device['name']}' is connected.")
            return True

    except OSError:
        # Handle the error if no default input device is available
        print("No default input mic device available.")
        sys.exit(1)


def check_communicator(communicator_config):
    try:
        communicator = Serial_protocol(**communicator_config)
        if communicator.ser.is_open:
            print("Serial connection established.")
            return communicator
    except serial.SerialException as e:
        # Handle the error if no default input device is available
        print(f"No connected thomas device available. Error : {e}")
        # sys.exit(1)
        raise RuntimeError(f"No connected thomas device available. Error: {e}") from e
    
    
    """ 사용 가능한 포트 확인 debug
        # import serial.tools.list_ports
        # ports = serial.tools.list_ports.comports()
        # available = [port.device for port in ports]
        # print("현재 사용 가능한 포트:", available)
    """