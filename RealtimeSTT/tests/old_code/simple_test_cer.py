import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from RealTimeSTT_LEE.audio_recorder import AudioToTextRecorder
import utils
import params
import datetime
import sys


if __name__ == '__main__':

    # print(params.event_flag.keys())
    # print(params.event_flag.values())
    # print(params.event_flag.items())

    # for i in params.event_flag.keys():
    #     print(i.rstrip(".?!"))

    recorder_config = {
        'spinner': False,
        'model': 'small',
        'language': 'ko',
        'silero_sensitivity': 0.2,
        'webrtc_sensitivity': 3,
        'device': 'cpu'
    }

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
        end_time = time.time()
        process_time = end_time - start_time
        core_text = hypothesis_text.split(" ")
        same_text = [item for item in params.core_text_list if item in core_text]

        score_list = []

        # event_flag code dev
        for ref_text in params.event_flag.keys():

            # ref_text, inf_text similarity calculation
            is_similar, similarity = utils.levenshtein_similarity(
                junk=utils.isjunk, ref_text=ref_text, inf_text=hypothesis_text, threshold=0.8)

            score_list.append(similarity)

        max_similarity = max(score_list)
        if max_similarity <= params.max_similarity_threshold:
            event_flag = None
        else:
            event_flag = score_list.index(max_similarity) + 1

        
        now_event_flag = (i+3) // 3
        # print(f"now_event_flag : {now_event_flag}")
        if now_event_flag == event_flag:
            total_acc_cnt += 1
            # print(f"\ttotal_acc_cnt = {total_acc_cnt}\n")
        

        # log save and print
        if hypothesis_text:
            cer = utils.calculate_cer(reference_text, hypothesis_text)
            print(f"Recognized: {hypothesis_text}", file = log_txt2)
            print(f"Recognized: {hypothesis_text}")
            print(f"cer: {cer:.2f}", flush=True, file = log_txt2)
            print(f"cer: {cer:.2f}", flush=True)
            print(f"Core Text : {same_text}", flush=True, file = log_txt2)
            print(f"Core Text : {same_text}")
            print(f"Processing Time : {process_time:.2f} sec", flush=True, file = log_txt2)
            print(f"Processing Time : {process_time:.2f} sec", flush=True)
            print(f"similarity : {max_similarity}", file=log_txt2)
            print(f"similarity : {max_similarity}")
            print(f"event_flag : {event_flag}", file=log_txt2)
            print(f"event_flag : {event_flag}")
            params.total_cer += cer
            params.total_process_time += process_time
            params.total_similarity += max_similarity

        input("Press Enter to next scenario...")

    print(f"\ntotal_cer : {params.total_cer / len(params.reference_texts)}", file = log_txt2)
    print(f"\ntotal_cer : {params.total_cer / len(params.reference_texts)}")
    print(f"total_similarity : {params.total_similarity / len(params.reference_texts)}", file = log_txt2)
    print(f"total_similarity : {params.total_similarity / len(params.reference_texts)}")
    print(f"total_acc_cnt : {total_acc_cnt / len(params.reference_texts)}", file = log_txt2)
    print(f"total_acc_cnt : {total_acc_cnt / len(params.reference_texts)}")
    print(f"total_processing_time : {params.total_process_time / len(params.reference_texts)}", file = log_txt2)
    print(f"total_processing_time : {params.total_process_time / len(params.reference_texts)}")
    
    log_txt2.close()

    recorder.shutdown()
    sys.exit("종료")