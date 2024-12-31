import time
from RealtimeSTT import AudioToTextRecorder
import utils
import params


if __name__ == '__main__':

    # print(params.event_flag.keys())
    # print(params.event_flag.values())
    # print(params.event_flag.items())

    recorder = AudioToTextRecorder(spinner=False, model="small", language="ko")

    similarity_threshold = 0.8
    print("Say something...")

    while (True):

        start_time = time.time()
        inf_text = recorder.text().rstrip(".?!")

        # 1차 개발 그냥 threshold 이상이면, 바로 event로 간주
        # 성능 별로면, score_list에 다 저장하고 가장 높은 score의 인덱스가 event로 간주 

        # event_flag code dev
        for ref_text in params.event_flag.keys():

            # ref_text, inf_text similarity calculation 
            is_similar, similarity = utils.levenshtein_similarity(junk=None, ref_text=ref_text, inf_text=inf_text, threshold=similarity_threshold)

            # threshold
            if similarity >= similarity_threshold:
                event_text = ref_text
                break

            else:
                continue
        
        event_flag = params.event_flag[event_text]

        end_time = time.time()
        process_time = end_time - start_time
        
        print(f"inf_text : {inf_text}\n")
        print(f"similarity : {similarity}\n")
        print(f"event_flag : {event_flag}\n")
        print(f"Processing Time : {process_time}\n")