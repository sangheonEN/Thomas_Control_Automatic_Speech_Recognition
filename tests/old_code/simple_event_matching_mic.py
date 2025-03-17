import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from RealTimeSTT_LEE.audio_recorder import AudioToTextRecorder
import utils
import params
import datetime
import sys
import difflib
import yaml

def isjunk(x):
    """
        공백 무시 콜백 함수
        Args:
            x: ??
        Return: x == " "

    """
    return x == " "


def gestalt_pattern_matching(s1, s2):
    """
        Gestalt pattern matching (SequenceMatcher) based similarity.
        threshold default : 0.7
    """
    similarity = difflib.SequenceMatcher(isjunk, s1, s2).ratio()

    return similarity


if __name__ == '__main__':
    
    # config load
    with open(params.CONFIG_FILE, "r") as file:
        configs = yaml.safe_load(file)
    
    recorder_config = configs['recorder_config']

    recorder = AudioToTextRecorder(**recorder_config)
    now = datetime.datetime.now()
    formatted_time = now.strftime("%H_%M_%S")
    file_name = formatted_time
    log_txt2 = open(f'{file_name}.txt','w')
    total_acc_cnt = 0
    print("Say something...")


    for i, reference_text in enumerate(params.reference_texts):
        print(f"\n scenario {i+1}:", file = log_txt2)
        print(f"\n scenario {i+1}:")

        print(f"Reference: {reference_text}", file = log_txt2)
        print(f"Reference: {reference_text}")

        start_time = time.time()
        hypothesis_text = recorder.text().rstrip(".?!")

        score_list = []

        # event_flag code dev
        for ref_text in params.event_flag.keys():

            # ref_text, inf_text similarity calculation
            similarity = gestalt_pattern_matching(ref_text, hypothesis_text)
            
            score_list.append(similarity)

        max_similarity = max(score_list)
        event_flag = score_list.index(max_similarity) + 1 if max_similarity > 0.75 else None
        
        end_time = time.time()
        process_time = end_time - start_time
               
        # log save and print
        if hypothesis_text:
            print(f"Prediction Text: {hypothesis_text}", file = log_txt2)
            print(f"Prediction Text: {hypothesis_text}")
            print(f"Processing Time : {process_time:.2f} sec", flush=True, file = log_txt2)
            print(f"Processing Time : {process_time:.2f} sec", flush=True)
            print(f"similarity : {max_similarity}", file=log_txt2)
            print(f"similarity : {max_similarity}")
            print(f"event_flag : {event_flag}", file=log_txt2)
            print(f"event_flag : {event_flag}")
            params.total_process_time += process_time

        now_event_flag = (i+3) // 3
        if now_event_flag == event_flag:
            print("Matching Complete!!!\n")
            total_acc_cnt += 1
            
        input("Press Enter to next scenario...")

    print("\n")
    print(f"Total matching accuracy : {total_acc_cnt / len(params.reference_texts)}\n", file = log_txt2)
    print(f"Total matching accuracy : {total_acc_cnt / len(params.reference_texts)}\n")
    print(f"total_processing_time : {params.total_process_time / len(params.reference_texts)}\n", file = log_txt2)
    print(f"total_processing_time : {params.total_process_time / len(params.reference_texts)}\n")
    
    log_txt2.close()

    recorder.shutdown()
    sys.exit("종료")