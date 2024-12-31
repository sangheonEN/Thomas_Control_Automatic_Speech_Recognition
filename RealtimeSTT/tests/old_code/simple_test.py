import time
from RealtimeSTT import AudioToTextRecorder

core_text_list = ["환자분", "성함이", "어떻게", "되세요.", "되세요?", 
                  "안녕하세요.", 
                  "입을", "벌려보세요.", "벌려", "여세요.", "열어주세요.", "아", "하세요.", "벌려보시겠어요?", "벌려보시겠어요.", "더", "크게", "아하세요.",
                  "불편하세요.", "불편하세요?", "어디가", 
                  "진료", "시작하겠습니다.", 
                  "통증이", "동증이", "느껴진다면", "왼쪽", "팔을", "들어주세요.", 
                  "느껴지시나요.", "느껴지시나요?", 
                  "다시", "시작해도", "될까요.", 
                  "끝났습니다.", "수고하셨습니다.", 
                  "네", "알겠습니다."] 

if __name__ == '__main__':
    recorder = AudioToTextRecorder(spinner=False, model="tiny", language="ko")

    print("Say something...")

    while (True):
        start_time = time.time()
        # text = recorder.text().rstrip(".?!,")
        text = recorder.text()
        end_time = time.time()
        process_time = end_time - start_time
        core_text = text.split(" ")
        same_text = [item for item in core_text_list if item in core_text]
        print(text, end = " ", flush=True)
        print(f"Core Text : {same_text}", flush=True)
        print(f"Processing Time : {process_time:.2f} sec", flush=True)
        

        # if recorder.is_recording and start_time is None:
        #     start_time = time.time()

        # text = recorder.text()
        # if text and start_time is not None:
        #     end_time = time.time()
        #     process_time = end_time - start_time
        #     print(f"Recognized: {text}")
        #     print(f"Processing Time: {process_time:.2f} (sec)")

        #     start_time = None
    
        # if not recorder.is_recording and start_time is not None:
        #     start_time = None