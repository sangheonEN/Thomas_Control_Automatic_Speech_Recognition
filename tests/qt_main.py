import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import yaml
import threading
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal
from serial.tools import list_ports
import torch.multiprocessing as mp
import logging


import params
import utils
from async_serial_protocol import AsyncSerialCommunicator
from RealTimeSTT_LEE.audio_recorder import AudioToTextRecorder
from text_similarity import Similarity_cal


class MainWindow(QtWidgets.QMainWindow):
    # 메인 스레드에서 안전하게 UI 업데이트를 수행하기 위한 시그널 정의
    updateTextSignal = pyqtSignal(str)
    showErrorSignal = pyqtSignal(str, str)
    
    def __init__(self):
        super(MainWindow, self).__init__()
        # ui 파일 경로는 params.gui_config에 지정된 값을 사용 (예: design_gridlayout_tab_adjust20250415.ui)
        ui_path = params.get_processed_gui_config()["ui_file_path"]
        uic.loadUi(ui_path, self)
        # 사용 가능한 연결 port 번호 표시
        self.load_serial_ports()
        # 사용 가능한 mic name, index combobox표시
        self.load_mic_devices()
        
        # 시그널과 슬롯 연결: 백그라운드 스레드의 메시지를 메인 스레드에서 처리하도록 함.
        self.updateTextSignal.connect(self.update_text)
        self.showErrorSignal.connect(self.show_error_message)

        # Tab1 위젯에 해당하는 위젯 연결 (ui_process_define.txt에 기술된 이름 활용)
        # 예를 들어 comboBox_1, comboBox_2, comboBox_3, pushButton_1~pushButton_5, textEdit, label_4
        self.pushButton_1.clicked.connect(self.update_config)
        self.pushButton_2.clicked.connect(self.check_serial)
        self.pushButton_3.clicked.connect(self.check_mic)
        self.pushButton_4.clicked.connect(self.toggle_stt)
        self.pushButton_5.clicked.connect(self.reset_output)
        
        # Tab2 – event_flag 관리 (pushButton_6 ~ pushButton_9, tableWidget)
        self.pushButton_6.clicked.connect(self.query_event_flag)
        self.pushButton_7.clicked.connect(self.add_event_flag)
        self.pushButton_8.clicked.connect(self.delete_event_flag)
        self.pushButton_9.clicked.connect(self.modify_event_flag)
        self.load_event_flag_table()
        
        # 아이콘 경로 설정 – label_4에 표시될 mic_active/mic_deactive 아이콘
        icon_config = params.get_processed_gui_config()
        self.icon_active_path = os.path.join(icon_config['icon_path'], "mic_active_64.png")
        self.icon_deactive_path = os.path.join(icon_config['icon_path'], "mic_deactive_64.png")
        self.update_mic_icon(active=False)
        
        self.stt_running = False # text() 전사처리 while문 동작 flag
        self.communicator = None # 시리얼 통신 객체
        self.recorder = None # 음성 인식 모듈 객체
        self.shutdown_flag = False # 종료 신호 flag 변수

    def load_serial_ports(self):
        self.comboBox_2.clear()  # 기존 포트 항목 비우기

        ports = list_ports.comports()
        
        if not ports:
            self.updateTextSignal.emit("⚠️ 연결된 시리얼 포트를 찾을 수 없습니다.")
            return
        
        for port in ports:
            label = f"{port.device} - {port.description}"
            self.comboBox_2.addItem(label, port.device)

        # self.comboBox_2.clear()  # 기존 포트 항목 비우기

        # usb_ports = [
        #     port.device
        #     for port in list_ports.comports()
        #     if "USB Serial Port" in port.description  # ← 핵심 필터
        # ]

        # if not usb_ports:
        #     self.updateTextSignal.emit("⚠️ USB Serial Port를 찾을 수 없습니다.")
        # else:
        #     self.comboBox_2.addItems(usb_ports)
        #     self.updateTextSignal.emit(f"🔌 사용 가능한 USB 포트: {', '.join(usb_ports)}")

    def update_text(self, message):
        # 메인(UI) 스레드에서 호출되어 textEdit 위젯을 안전하게 업데이트함.
        self.textEdit.append(message)

    def update_config(self):
        # pushButton_1: comboBox에서 선택한 값들을 recorder_config.yaml 업데이트
        language = self.comboBox_1.currentText()
        port = self.comboBox_2.currentData()
        baudrate = self.comboBox_3.currentText()
        mic_index = self.comboBox_4.currentData()  # 사용자 선택 index 가져오기

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recorder_config.yaml')
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        config['recorder_config']['language'] = language
        config['communicator_config']['port'] = port
        config['recorder_config']['input_device_index'] = mic_index

        try:
            config['communicator_config']['baudrate'] = int(baudrate)
        except:
            config['communicator_config']['baudrate'] = baudrate
        with open(config_path, "w", encoding="UTF8") as f:
            yaml.dump(config, f, allow_unicode=True)

        # params 전역 변수 업데이트
        params.update_config_globals(config)

        self.updateTextSignal.emit("Configuration updated.")

    def check_serial(self):
        # pushButton_2: 시리얼 포트 존재 여부 확인
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recorder_config.yaml')
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)

        port = config['communicator_config']['port']
        available_ports = [comport.device for comport in list_ports.comports()]

        if port in available_ports:
            self.updateTextSignal.emit(f"Serial port {port} is available.")
            self.serialConnected = True
        else:
            self.updateTextSignal.emit(f"Serial port {port} not found!")
            self.serialConnected = False

    def load_mic_devices(self):
        self.comboBox_4.clear()
        mic_list = utils.list_input_devices()
        for index, name in mic_list:
            # self.comboBox_4.addItem(f"[{index}] {name}", userData=index)
            self.comboBox_4.addItem(f"{name}", userData=index)

    def check_mic(self):
        # pushButton_3: 마이크 연결 확인
        try:
            result_flag, result_describe = utils.check_mic_connection()
            self.micConnected = result_flag
            self.updateTextSignal.emit(result_describe)
        except Exception as e:
            self.micConnected = result_flag
            self.updateTextSignal.emit(result_describe)
            logging.exception(f"마이크 체크 중 오류 발생 : {str(e)}")

    def toggle_stt(self):
        # 음성인식 시작 전에 마이크 연결 여부 검사
        if not getattr(self, "micConnected", False):
            QtWidgets.QMessageBox.warning(self, "마이크 확인", "마이크 연결이 확인되지 않았습니다. 먼저 '마이크 연결 확인' 버튼을 눌러주세요.")
            return
        
        if not getattr(self, "serialConnected", False):
            QtWidgets.QMessageBox.warning(self, "디바이스 연결 확인", "디바이스 Port 연결이 확인되지 않았습니다. 먼저 '디바이스 연결 확인' 버튼을 눌러주세요.")
            return
        
        # pushButton_4: 음성인식 시작/종료 토글 기능
        if not self.stt_running:
            self.pushButton_4.setText("음성 인식 종료")
            self.stt_running = True
            # 백그라운드 스레드에서 STT 루프 실행 (시그널을 통해 UI 업데이트)
            self.stt_thread = threading.Thread(target=self.run_stt)
            self.stt_thread.start()
            self.start_shutdown_monitor()
        else:
            self.pushButton_4.setText("음성 인식 시작")
            # 종료 시, 비동기 통신기와 녹음기의 종료 함수 호출
            self.shutdown_all_stt_components()

            if self.stt_thread is not None:
                self.updateTextSignal.emit("Waiting for STT thread to finish...")
                self.stt_thread.join(timeout=5)
            if self.stt_thread.is_alive():
                print("STT thread did not finish in time.")
                # self.updateTextSignal.emit("STT thread did not finish in time.")
            else:
                print("STT thread has been terminated.")
                # self.updateTextSignal.emit("STT thread has been terminated.")
            self.updateTextSignal.emit("Speech recognition stopped.")

    def run_stt(self):
        # 백그라운드 스레드에서 asyncio 기반 음성인식 루프 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.stt_loop())
        except Exception as e:
            self.updateTextSignal.emit(f"STT error: {e}")
            logging.exception(f"qt stt_loop 함수 thread 처리 시 error 발생 내용 : {e}")
        finally:
            loop.close()


    async def stt_loop(self):

        recorder_config = params.get_processed_recorder_config()
        similarity_config = params.get_processed_similarity_config()

        self.communicator = AsyncSerialCommunicator(params.communicator_config["port"],
                                                    params.communicator_config["baudrate"])
        await self.communicator.ensure_connection()
        self.recorder = AudioToTextRecorder(**recorder_config)
        similarity_cal = Similarity_cal(similarity_config['model_path'])
        self.updateTextSignal.emit("Say something...")
        self.update_mic_icon(active=True)

        # await self.communicator.monitor_push_button() # -> 얘가 문제네. 얘가 종료되지 않아서 run_stt thread가 종료되지 않는 문제 발생.
        # 개선 내용 : asyncio.create_task를 활용하여 self.communicator.monitor_push_button()을 새로운 loop로 생성
        #            그 후 음성 인식 종료 버튼 클릭 시 self.stt_running가 False, monitor_task.cancel()로 종료 후 메인 loop break
        # ----------------------------------------------------------------------------------------------------------------------
        while self.stt_running:

            try:
                if self.recorder:
                    inf_text = await asyncio.to_thread(self.recorder.text)
                else:
                    logging.warning("❌ self.recorder is None, STT를 건너뜁니다.")
                    return
            except Exception as e:
                logging.exception(f"STT 처리 시 error 발생 내용 : {e}")
            try:

                event_flag, max_similarity = utils.event_matching(inf_text, similarity_cal, params.similarity_config)
             
            except Exception as e:
                logging.exception(f"이벤트 매칭 기능 처리 시 error 발생 내용 : {e}")

            # self.updateTextSignal.emit(f"Event flag: {event_flag}")
            self.updateTextSignal.emit(f"Recognized Text: {inf_text}")
            # self.updateTextSignal.emit(f"Similarity: {max_similarity}")
            if event_flag is None:
                if self.communicator is not None:
                    await self.communicator.clear_queue()
                continue
            tens = event_flag // 10
            units = event_flag % 10
            thomas_event_state = await self.communicator.async_sending_param(tens, units, thomas_event_state="ok")
            if thomas_event_state != "ok":
                self.showErrorSignal.emit(
                    "Serial Error",
                    f"Error 내용 : {thomas_event_state} 통신 문제로 장치를 확인하세요."
                )
                self.shutdown_all_stt_components()
                self.shutdown_flag = True
                return
            self.updateTextSignal.emit(f"Final event state: {thomas_event_state}")
            await asyncio.sleep(0.01)

    def reset_output(self):
        # pushButton_5: textEdit 내용을 초기화
        self.textEdit.clear()

    def update_mic_icon(self, active=False):
        # label_4: 음성인식 활성 여부에 따라 아이콘 변경
        if active:
            self.label_4.setPixmap(QtGui.QPixmap(self.icon_active_path))
        else:
            self.label_4.setPixmap(QtGui.QPixmap(self.icon_deactive_path))

    def load_event_flag_table(self):
        # if not self.stt_running:
        #     QtWidgets.QMessageBox.warning(self, "음성 인식 종료 확인", "음성 인식이 종료되지 않았습니다. 음성 인식을 먼저 종료해주세요.")
        #     return
        # recorder_config.yaml의 event_flag 내용을 tableWidget에 표시 (Tab2)
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recorder_config.yaml')
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        event_flag = config.get("event_flag", {})
        sorted_events = sorted(event_flag.items(), key=lambda x: x[1])
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["시나리오", "번호"])
        self.tableWidget.setRowCount(len(sorted_events))
        for row, (scenario, number) in enumerate(sorted_events):
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(scenario))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(str(number)))

    def query_event_flag(self):
        # pushButton_6: YAML 파일의 event_flag 목록을 조회하여 테이블 업데이트
        self.load_event_flag_table()
        # self.updateTextSignal.emit("Event flag table refreshed.")

    def add_event_flag(self):
        if self.stt_running:
            QtWidgets.QMessageBox.warning(self, "음성 인식 종료 확인", "음성 인식이 종료되지 않았습니다. 음성 인식을 먼저 종료해주세요.")
            return

        # pushButton_7: 입력 다이얼로그를 통해 event_flag 항목 추가
        scenario, ok1 = QtWidgets.QInputDialog.getText(self, "추가", "시나리오 입력:")
        if not ok1 or not scenario:
            return
        number, ok2 = QtWidgets.QInputDialog.getInt(self, "추가", "번호 입력:")
        if not ok2:
            return
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recorder_config.yaml')
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        config["event_flag"][scenario] = number
        with open(config_path, "w", encoding="UTF8") as f:
            yaml.dump(config, f, allow_unicode=True)

        # ✅ 3. params.event_flag 수동 갱신
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        params.event_flag = config.get("event_flag", {})
        
        self.load_event_flag_table()
        # self.updateTextSignal.emit("Event flag added.")

    def modify_event_flag(self):
        if self.stt_running:
            QtWidgets.QMessageBox.warning(self, "음성 인식 종료 확인", "음성 인식이 종료되지 않았습니다. 음성 인식을 먼저 종료해주세요.")
            return
        # pushButton_8: 입력 다이얼로그를 통해 기존 event_flag 항목 수정
        scenario, ok1 = QtWidgets.QInputDialog.getText(self, "수정", "수정할 시나리오 입력:")
        if not ok1 or not scenario:
            return
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recorder_config.yaml')
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        if scenario not in config["event_flag"]:
            self.updateTextSignal.emit("해당 시나리오가 존재하지 않습니다.")
            return
        number, ok2 = QtWidgets.QInputDialog.getInt(self, "수정", "새 번호 입력:")
        if not ok2:
            return
        config["event_flag"][scenario] = number
        with open(config_path, "w", encoding="UTF8") as f:
            yaml.dump(config, f, allow_unicode=True)
        
        # ✅ 3. params.event_flag 수동 갱신
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        params.event_flag = config.get("event_flag", {})

        self.load_event_flag_table()
        # self.updateTextSignal.emit("Event flag modified.")

    def delete_event_flag(self):
        if self.stt_running:
            QtWidgets.QMessageBox.warning(self, "음성 인식 종료 확인", "음성 인식이 종료되지 않았습니다. 음성 인식을 먼저 종료해주세요.")
            return
        # pushButton_9: 입력 다이얼로그를 통해 event_flag 항목 삭제
        scenario, ok = QtWidgets.QInputDialog.getText(self, "삭제", "삭제할 시나리오 입력:")
        if not ok or not scenario:
            return
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recorder_config.yaml')
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        if scenario in config["event_flag"]:
            del config["event_flag"][scenario]
            with open(config_path, "w", encoding="UTF8") as f:
                yaml.dump(config, f, allow_unicode=True)
            self.load_event_flag_table()
            self.updateTextSignal.emit("Event flag deleted.")
        else:
            self.updateTextSignal.emit("해당 시나리오가 존재하지 않습니다.")
        
                # ✅ 3. params.event_flag 수동 갱신
        with open(config_path, "r", encoding="UTF8") as f:
            config = yaml.safe_load(f)
        params.event_flag = config.get("event_flag", {})

    def show_error_message(self, title, message):
        QtWidgets.QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        self.updateTextSignal.emit("🛑 창 종료 요청 감지됨. 리소스를 정리합니다...")

        self.shutdown_all_stt_components()
        
        event.accept()  # 창 닫기 허용

    def shutdown_all_stt_components(self):
        self.stt_running = False

        if self.communicator:
            self.communicator.close()
            self.communicator = None

        if self.recorder:
            self.recorder.shutdown()
            self.recorder = None

        self.update_mic_icon(active=False)

    def monitor_shutdown_flag(self):
        if self.shutdown_flag and self.stt_thread and not self.stt_thread.is_alive():
            self.shutdown_timer.stop()
            print("🧹 STT thread has finished, shutting down UI.")
            self.close()  # 또는 QtWidgets.QApplication.quit()

    def start_shutdown_monitor(self):
        self.shutdown_timer = QtCore.QTimer()
        self.shutdown_timer.timeout.connect(self.monitor_shutdown_flag)
        self.shutdown_timer.start(50)  # 100ms 간격으로 체크

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # 로그 설정
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main_error_log.txt')
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    mp.freeze_support()
    
    try:    
        main()
    except Exception as e:
        logging.exception(f"메인 코드 예외 발생 내용 : {e}")