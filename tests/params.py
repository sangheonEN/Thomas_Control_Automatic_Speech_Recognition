import os
import sys
import yaml


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

CONFIG_FILE = resource_path('recorder_config.yaml')

with open(CONFIG_FILE, "r", encoding='UTF8') as file:
    configs = yaml.safe_load(file)

# 2. 전역 원본 설정 저장 (상대 경로 유지)
recorder_config = configs["recorder_config"]
communicator_config = configs["communicator_config"]
similarity_config = configs["similarity_config"]
gui_config = configs["gui_default_config"]
event_flag = configs["event_flag"]


# faster whisper, silero model, openwakeword, pvporcupine 관련 폴더 명을 활용해 절대 경로 치환
def get_processed_recorder_config():
    cfg = dict(recorder_config)
    if cfg.get("model"):
        cfg["model"] = resource_path(os.path.join("faster_whisper_model", cfg["model"]))
    if cfg.get("silero_model_path"):
        cfg["silero_model_path"] = resource_path(cfg["silero_model_path"])
    if cfg.get("openwakeword_model_paths"):
        cfg["openwakeword_model_paths"] = resource_path(cfg["openwakeword_model_paths"])
    if cfg.get("openwakeword_embedding_model_path"):
        cfg["openwakeword_embedding_model_path"] = resource_path(cfg["openwakeword_embedding_model_path"])
    if cfg.get("openwakeword_melspec_model_path"):
        cfg["openwakeword_melspec_model_path"] = resource_path(cfg["openwakeword_melspec_model_path"])
    if cfg.get("pvporcupine_keyword_paths"):
        cfg["pvporcupine_keyword_paths"] = resource_path(os.path.join("pvporcupine", cfg["pvporcupine_keyword_paths"]))
    return cfg


# 이벤트 매칭 유사도 계산 모델 관련 폴더 명을 활용해 절대 경로 치환
def get_processed_similarity_config():
    cfg = dict(similarity_config)
    if cfg.get("model_path"):
        cfg["model_path"] = resource_path(cfg["model_path"])
    return cfg


# gui 관련 폴더 명을 활용해 절대 경로 치환
def get_processed_gui_config():
    cfg = dict(gui_config)
    if cfg.get("icon_path"):
        cfg["icon_path"] = resource_path(cfg["icon_path"])
    if cfg.get("ui_file_path"):
        cfg["ui_file_path"] = resource_path(cfg["ui_file_path"])
    return cfg


# 설정 갱신 함수 (update_config 이후 호출 시 사용)
def update_config_globals(new_config):
    global recorder_config, communicator_config, similarity_config, gui_config, event_flag
    recorder_config = new_config["recorder_config"]
    communicator_config = new_config["communicator_config"]
    similarity_config = new_config["similarity_config"]
    gui_config = new_config["gui_default_config"]
    event_flag = new_config["event_flag"]