import serial
import time
import sys
import os

class Serial_protocol:
    """
    Serial 통신을 위한 파라미터를 저장하고, 이벤트 기능을 통해 전달 받은 event_flag 변수를 sending하는 클래스입니다.
    
    params:
        1. port=""
        2. baudrate=115200
        3. timeout=0.001
        4. input_type='int'
        5. endianness='big'
        6. push_button_trigger=False
        
    functions:
        1. sending_param: 데이터 송신
        2. received_param: 데이터 수신
        3. close: serial 객체 종료
        4. reopen_serial: serial 객체 재연결


    """


    def __init__(self, port="", baudrate=115200, timeout=0.001, input_type='int', endianness='big', push_button_trigger = False):
        """
        self.port : port 정보
        self.baudrate : 보레이트 정보
        self.timeout: 최소 시간 초과 변수
        self.input_type: sending input type
        self.input_byte: the byte of sending input type
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.endianness = endianness
        self.push_button_trigger = push_button_trigger
        if input_type == 'int':
            self.input_byte = 8
        else:
            self.input_byte = None

        # 시리얼 포트 설정
        self.ser = serial.Serial(
            port=self.port,      # Windows의 경우 COM 포트 번호를 지정
            baudrate=self.baudrate,    # 보드레이트 설정
            timeout=self.timeout         # 타임아웃 시간 (초)
        )

        """ debug용
            try:

                # 시리얼 포트 설정
                self.ser = serial.Serial(
                    port=self.port,      # Windows의 경우 COM 포트 번호를 지정
                    baudrate=self.baudrate,    # 보드레이트 설정
                    timeout=self.timeout         # 타임아웃 시간 (초)
                )

            except serial.SerialException as e:
                print(f"Error opening serial port: {e}")
        """
    
        
    def preprocess(self, tens, units, recorder):
        """
        HW팀의 요청사항에 맞게 데이터 전송 전처리
        예시)
        - 문자기준: Start of Text / Event_num(10의 자리) / Event_num2(1의 자리) / End of Text
        - Event_flag가 10 이면, 0x02 / 0x31 / 0x30 / 0x03
        - Hex: 0x02 / 0x32 / 0x31 / 0x03

        "환자분 안녕하세요": 1                         -> 0x02 0x30 0x31 0x03
        "환자분 성함이 어떻게 되세요": 2                -> 0x02 0x30 0x32 0x03
        "어디가 불편하세요": 3                         -> 0x02 0x30 0x33 0x03
        "환자분 진료 시작하겠습니다": 4                 -> 0x02 0x30 0x34 0x03
        "환자분 아 하세요": 5                          -> 0x02 0x30 0x35 0x03
        "환자분 입을 더 크게 벌려보시겠어요": 6          -> 0x02 0x30 0x36 0x03
        "통증이 느껴진다면 왼쪽 팔을 들어주세요": 7      -> 0x02 0x30 0x37 0x03
        "환자분 통증이 느껴지시나요": 8                 -> 0x02 0x30 0x38 0x03
        "환자분 다시 진료 시작해도 될까요" : 9          -> 0x02 0x30 0x39 0x03
        "환자분 진료 끝났습니다. 수고하셨습니다" : 10    -> 0x02 0x31 0x30 0x03

        val= [2,ord(str(x)),ord(str(y)),3]의 의미는 아스키코드 10진수 기준으로 2는 문자로 STX고 3은 ETX이다. 
        그리고 ord(문자) = 아스키 10진수로 출력되어 str(0)은 48, str(1)은 49로 출력된다.
        그후 bytearray를 적용하면 원소 값이 hex로 변환되어 전송. 
        """
        
        # 초기 변수
        OK_target = f'\x02{tens}{units}OK\x03'
        sec = 5 # received 대기 시간
        cnt = 0 # retry count
        cnt_N = 3 # retry 시도 횟수
        exit_flag = False

        # 전송 data 형식으로 array 변환
        val = [2, ord(str(tens)), ord(str(units)), 3]
        # print(f"[2,ord(str(x)),ord(str(y)),3] : {val}")

        byte_array = bytearray(val)
        print(f"byte_array : {byte_array}")

        # data sending!
        self.ser.write(byte_array)
        
        
        # micom to pc response data receive code
        start_time = time.time()

        # N초간 receive 처리
        print("Cross Check Sending data correct\n")
        try:
            while time.time() - start_time < sec:
                
                if self.ser.in_waiting > 0: # 데이터가 들어왔을때!
                    try:
                        
                        data = self.ser.readline().decode('utf-8')  # '\n' 제거
                        print(f"Received data1:{data}")
                        
                    # only str data received
                    except UnicodeDecodeError as e:
                        print(f"Decode error: {e}. received data is not str.\n")
                        print(f"retry\n")
                        self.ser.write(byte_array)
                        cnt += 1
                        if cnt > cnt_N:
                            exit_flag = True
                            break
                        continue
                    
                    # sending data matching! cross check!
                    if OK_target in data:
                        print("OK_target in data OK!\n")
                        return
                            
                    else:
                        print(f"retry\n")
                        self.ser.write(byte_array)
                        cnt += 1
                        if cnt > cnt_N:
                            exit_flag = True
                            break
                        continue
                    
                else: # 데이터가 안들어왔을때
                    continue
                
            # 5초 지나도 데이터가 송신 안되었을때
            print("No data received for 5 seconds.\n")
            recorder.shutdown()
            time.sleep(1.0)
            sys.exit()
            
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            
        if exit_flag == True:
            print("Device Error\n")
            recorder.shutdown()
            time.sleep(1.0)
            sys.exit()
        else:
            pass
            


    def sending_param(self, event_flag, recorder):
        """
        int 데이터를 바이트로 변환하여 전송 (8바이트, Big-endian)

        Args:
            event_flag: 이벤트 기능을 통해 최종적으로 선택된 event_flag

        Returns: N/A
        """

        try:

            units = event_flag % 10  # 나머지
            tens = event_flag // 10  # 몫

            # print(units)
            # print(tens)

            self.preprocess(tens, units, recorder)

        except serial.SerialException as e:
            print(f"self.ser.write error: {e}\n")
            print(f"객체 종료 후 reopen 시도\n")
            self.close()
            time.sleep(0.2)
            self.serial_state_check()

        print(f"Sent event: {event_flag}")


    def check_push_button(self):
        """
        수신된 데이터를 반환하는 함수

        Args: N/A

        Returns: int 데이터면, data 반환. 아니면, None 반환
        """
        
        data1 = self.ser.readline().decode('utf-8')
        time.sleep(0.08)
        data2 = self.ser.readline().decode('utf-8')
        
        # print(f"data1: {data1}\n")
        # print(f"data2: {data2}\n")
        # STOP 상태에 있다가 START 상태로 변환될때 STOPSTART가 같이 들어오는 data일때 True해서 넘김
        if "STOP" in data1 and "START" in data2:
            self.push_button_trigger = True
        else:
            self.push_button_trigger = False
        
        """
        # 그냥 Received data 1개로만 판단하는 코드
        # STOP 상태에 있다가 START 상태로 변환될때 STOPSTART가 같이 들어오는 data일때 True해서 넘김
        # data = self.ser.readline().decode('utf-8')  # '\n' 제거
        
        # print(f"data: {data}\n")
        # if "STOPSTART" in data:
        #     self.push_button_trigger = True
        # else:
        #     self.push_button_trigger = False
        
        """
        

    def close(self):
        """Close the serial connection if open."""
        if self.ser.is_open:
            self.ser.close()
            time.sleep(0.2)


    def serial_state_check(self):

        if self.ser.is_open:
            print("Serial port is already open.\n")
            return

        else:
            # 오픈 안되었겠지만 혹시 모르니까 close
            self.close()
            self.reopen_serial()


    def reopen_serial(self):
        """Attempts to reopen the serial port after closing it."""

        try:
            self.ser.open()
            time.sleep(0.2)
            print("serial reopen 완료!!!!!!!!!\n")

        except serial.SerialException as e:
            # serial.serialutil.SerialException: could not open port 'COM8': FileNotFoundError(2, '지정된 파일을 찾을 수 없습니다.', None, 2)
            print(f"reopen serial error : {e}\n")
