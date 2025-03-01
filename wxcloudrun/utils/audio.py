import os
import requests
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk


def recognize_from_url(open_id, audio_url: str):
    # Azure 语音服务配置
    speech_config = speechsdk.SpeechConfig(
        subscription="7TcuMWrUOoqaoFJu8yMrI7EgeFZJW5uKB8VsoMp0Hy6UA1i2E004JQQJ99BCACYeBjFXJ3w3AAAYACOGbxve",
        region="eastus",
    )

    speech_config.speech_recognition_language = "zh-CN"

    # 下载音频文件
    response = requests.get(audio_url)
    if response.status_code != 200:
        print("无法下载音频文件:", response.status_code)
        return

    # 存入临时文件
    original_audio_file = "temp_audio_original_{}.wav".format(open_id)
    with open(original_audio_file, "wb") as f:
        f.write(response.content)

    # 转换音频格式（3-bit → 16-bit PCM）
    converted_audio_file = "temp_audio_converted_{}.wav".format(open_id)
    # 加载音频（pydub 支持自动检测格式）
    audio = AudioSegment.from_file(original_audio_file)

    # 转换为 16-bit PCM（Azure 语音服务要求的格式）
    audio = audio.set_sample_width(2)  # 16-bit = 2 bytes
    audio = audio.set_frame_rate(16000)  # 推荐使用 16kHz 采样率
    audio = audio.set_channels(1)  # 单声道

    # 导出转换后的文件
    audio.export(converted_audio_file, format="wav")

    # 创建 AudioConfig
    audio_config = speechsdk.audio.AudioConfig(filename=converted_audio_file)

    # 初始化语音识别器
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )

    print("正在识别音频文件...")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    # 处理识别结果
    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("识别结果:", speech_recognition_result.text)
        return speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("未识别到语音:", speech_recognition_result.no_match_details)
        raise Exception("未识别到语音")
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    else:
        print(speech_recognition_result.reason)
        raise Exception("识别语音出错")


if __name__ == '__main__':
    text = recognize_from_url("test", "https://7072-prod-9g5b6d374032de85-1327836217.tcb.qcloud.la/voices/orjoY7et_lrDdpT85J0BwKufgEsk/1740798917726-62.wav")
    print(text)
