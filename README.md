# github에서는 오직 source code의 history를 저장하기 위함. 그래서 수정된 코드만 업로드하여 이력을 관리할것임. D:\STT_V1\STT\RealtimeSTT_Button\tests\ 경로에 faster_whisper_model, silero_model 폴더 및 내부 파일을 넣어야 정상적으로 코드가 작동됩니다. 필요하시면 jteks6@gmail.com으로 연락주세요.

# VERSION 업데이트 설명
v1.0 : pvporcupine 모델 wake word 활용 코드 수정 pvporcupine_access_key, pvporcupine_keyword_paths ...

v1.1 : 버튼식 음성 처리 프로세스에서 연속적 음성 처리 프로세스로 변경했고, 시리얼 통신 USB PORT 연결 끊김 시 재연결 반복 시도 기능 추가. qt_main.py 코드 QT 기능 추가

v1.2 : AudioToTextRecorder 클래스의 audio_data_worker process graceful shutdown, recording_worker process graceful shutdown 적용 (상세 내용은 음성인식모듈프로그램관련기술_습득교훈_개선사항_자체개발 excel 파일의 개선사항 12번, 15번 참고)

# 기능 설명

1. QT 클라이언트
    1) 음성 인식에 필요한 파라미터 Config 설정
    2) 마이크 연결 확인, PORT 연결 확인
    3) 음성 인식 시작 / 종료
    4) 음성 인식 결과 출력 창 / 결과 문구 초기화 버튼
    5) 음성 인식 시나리오 조회 / 삭제 / 수정 / 추가 기능

2. 음성 인식 기능 (AudioToTextRecorder) 
    1) sub_processer : _audio_data_worker (sr, chunksize 설정 기준 오디오 stream 열기 pyaudio.PyAudio().open(...), 마이크 재연결 시도 기능)
    2) sub_processer : _transcription_worker (STT 모델 로드, audio data 전달받아서 transcribe 처리, transcribe 최종 text 추론 결과 전달)
    3) main processer : recording_thread, VAD(silero_speech)_thread, multi process parameters
    * https://www.notion.so/jteks6/Ai-b91d10702b364510bec1035067a8387c?source=copy_link

3. 시리얼 통신 기능 
    1) 시리얼 통신 연결 기능, USB 연결 끊김 시 재연결 시도 기능 포함
    2) 시리얼 통신 연결 후 MICOM 장치와 데이터 송/수신 기능 (수신 받은 데이터 queue로 관리)

4. 시나리오 텍스트 매칭 기능
    1) 2*M / (len(inf_text) + len(scenario_text)). M : 음절 매칭 수
       * 향후 M / len(scenario_text) 시나리오 텍스트 기준으로 매칭 유사도 측정 알고리즘으로 변경 예정

# source description.

1. qt_main.py : Main code. 
    1) Thomas Connection 객체 생성
    2) Mic Connection 기능
    3) RealTimeSTT 객체 생성
    4) scenario text matching 객체 생성
    5) MICOM Sending the Event parameters

2. async_serial_protocol.py : Serial 통신을 위한 파라미터를 저장하고, 이벤트 기능을 통해 전달 받은 event_flag 변수를 sending하는 클래스를 포함하는 src
    1) MICOM Connection / Reconnection, parameters 송/수신

3. text_similarity.py : Senario reference와 Prediction text 간의 유사도를 계산하는 변수와 함수가 구현된 클래스를 포함하는 src.

4. utils.py : 기타 처리 기능들이 포함되는 src.
    1) event_matching
    2) list_input_devices
    3) check_mic_connection

5. params.py : 시나리오에 reference text 및 전역 parameters가 포함되는 src.
    1) recorder_config.yaml 파일의 config 파라미터 정보를 읽어와서 초기화.
    2) 상대경로가 필요한 파라미터에 상대경로 적용
    3) 프로그램에서 관련 파라미터 업데이트 시 파라미터 업데이트 처리

6. recorder_config.yaml : 프로그램에 필요 파라미터 설정 값 세팅