import serial
import time
import sys

def receive_serial_data(port, baudrate=115200, timeout=0.001):
    """
    시리얼 포트에서 데이터를 수신합니다.

    - Args:
        port (str): 시리얼 포트 이름 (예: "COM3", "/dev/ttyUSB0")
        baudrate (int): 통신 속도 (기본값: 115200)
        timeout (int): 타임아웃(값을 받는 시간) 설정 (기본값: 1ms)
        
    - Function:
    
    1. target = '\x02OK\x03' (STX, O, K, ETX) 데이터를 수신 받아서, 적절한 값이 Sending 되었는지 Cross Check
    
    2. 적절한 값이 Sending 되었으면, return
    
    3. 적절한 값이 Sending 되지 않았으면, Retry 2번 시도
       - Retry 시 target 값이 포함된 데이터가 들어오면 return
       - Retry 시 target 값이 포함된 데이터가 들어오지 않으면 오류 구문 출력
    
    - ETC    
    4. ser.in_waiting: 수신 받는 buffer array의 원소 수를 나타냄.
    
    예시)
    ser.in_waiting : '\x02OK\x03\x00\x00\x01\x00'
    
    print(ser.in_waiting) = 8
    
    """
    x = 1 % 10  # 나머지
    y = 1 // 10  # 몫
    # target = '\x02OK\x03'
    target = f'\x02{y}{x}OK\x03'
    N = 0
    
    try:
        # 시리얼 포트 열기
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Serial port {port} opened with baudrate {baudrate}. Waiting for data...")

            while True:
                if ser.in_waiting > 0: # ser.in_waiting: 수신 받는 buffer array의 원소 수를 나타냄.
                    print(f"ser.in_waiting: {ser.in_waiting}")
                    # 수신 데이터 읽기
                    # data1 = ser.read().decode('utf-8') # 값 하나씩 불러옴 ex) '\x02', 'O', 'K' ...
                    # data2 = ser.readline() # .decode('utf-8') 이거는 byte형을 str형으로 변환하는 코드. 따라서 utf-8로 표현하지 못하면 str로 표현이 안되는거니까 noise 변수로 취급
                    
                    try: # .decode('utf-8') 이거는 byte형을 str형으로 변환하는 코드. 따라서 utf-8로 표현하지 못하면 str로 표현이 안되는거니까 noise 변수로 취급
                        data2 = ser.readline().decode('utf-8') # 한줄씩 불러옴 ''\x00\x02OK'
                    
                    except UnicodeDecodeError as e:
                        print(f"Decode error: {e}. received data is not str.\n")
                        print(f"retry\n")
                        N += 1
                        if N > 3:
                            print("Device Error\n")
                            sys.exit()
                        continue
                                        
                    if data2.startswith('\x02'): # Received value가 STX로 시작하지 않으면, 정상 값이 아닌 노이즈 값으로 판단.
                        print("data input start\n")
                        
                        if target in data2:
                            print("Data Sending OK!\n")
                            
                        else:
                            print("Data Sending Not OK!\n")
                            print("retry\n")
                            N += 1
                            if N > 3:
                                print("Device Error\n")
                                sys.exit()
                            continue
                    
                    else:
                        print("Data Sending Not OK!\n")
                        print("retry\n")
                        N += 1
                        if N > 3:
                            print("Device Error\n")
                            sys.exit()
                        continue
                else:
                    pass

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except KeyboardInterrupt:
        print("Serial communication stopped.")

# 사용 예시
if __name__ == "__main__":
    # 사용 중인 시리얼 포트 이름으로 변경하세요 (예: "COM3" 또는 "/dev/ttyUSB0")
    port_name = "COM12"
    baudrate = 115200
    timeout = 0.01

    receive_serial_data(port_name, baudrate, timeout)