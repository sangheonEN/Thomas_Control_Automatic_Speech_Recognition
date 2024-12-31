"""
# 1. inf text similarity calculation using levenshtein_similarity
# 2. event flag calculation using max similarity score
# 3. Developing functions tailored to event flags (run voice file)
4. Added "Thomas" voice wake-up feature 
- Future work of robot control communication technology is necessary

"""

import time
from RealtimeSTT import AudioToTextRecorder
import utils
import params

if __name__ == '__main__':

    # print(params.event_flag.keys())
    # print(params.event_flag.values())
    # print(params.event_flag.items())

    recorder = AudioToTextRecorder(spinner=False, model="small", language="ko")

    wake_word = "토마스"  # Define the wake-up word

    while True:
        # Wait for the wake-up word
        print("Waiting for wake-up word...")
        while True:
            inf_text = recorder.text().rstrip(".?!")
            print(f"Detected text: {inf_text}")

            # Check if the wake-up word is detected
            if wake_word in inf_text:
                print("Wake-up word detected!")
                break    

        while (True):
            print("Say something...")

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
            if max_similarity <= 0.5:
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

            break
