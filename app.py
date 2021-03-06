# flask
from flask import Flask, Blueprint, request, abort, jsonify
from flask_restful import Api, Resource

# aitalk
from aitalk_webapi_sample import AITalkWebAPI

# azure
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings

# line
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage, AudioSendMessage, messages, ImageSendMessage, StickerSendMessage)

# others
import sys
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import datetime
import requests
import json
import re

app = Flask(__name__)
api = Api(app)

# define HTTP methods
class Get(Resource):
    def get(self):
        return { 'message': 'GET request OK.' }
class Post(Resource):
    def post(self):
        json = request.get_json(force = True)
        seat = json["seat"]
        out = json["out"]
        wind = json["wind"]

        text, url = main(seat,out, wind)

        return {"seat": seat, "out": out, "text": text, "wind": wind, "url": url}

api.add_resource(Get, '/get')
api.add_resource(Post, '/post')

# define functions
def main(seat,out,wind):

    # セリフの編集
    text = edit(seat,out,wind)

    # 音声生成
    targetfile = generate(text)

    # 音声保存
    url = save(targetfile)

    # LINE API 発射
    line_api(url, text)

    return text, url

def edit(seat,out,wind):

    # セリフの編集
    if out == "1": #朝時間通知
        if wind == "normal":
            text = "朝日が出ていて、良い風が吹いてるよ!素晴らしい一日の始まりだね!"
        else:
            text = "朝日がでているよ!素晴らしい1日の始まりだね!"

    elif out == "2": # おすすめ通知
        text = "いま、とても気持ちの良い時間だよ。外へ出てみないかい？"
    
    elif out == "3": # 日中通知
        if wind == "normal":
            text = "良い風が吹いてるよ!爽やかな天気だよ!"
        else:
            text = "外がすごく爽やかだよ？"
    
    elif out == "4": # 夕焼け通知
        text = "夕日がとてもきれいだよ？見に行こうよ!" 
    
    elif out == "5": # 夕時間通知
        text = "夕日がきれいだよ!" 
    
    elif out == "6": # お天気ヘッドライン（大阪）
        url = 'https://www.jma.go.jp/bosai/forecast/data/overview_forecast/270000.json'
        response = requests.get(url)
        body = json.loads(response.text)
        headline = body["headlineText"]
        result = re.sub(r'してください', 'してね', headline)
        result = re.sub(r'なります', 'なるよ', result)
        text = result
        
    else:
        text = "" 
    
    # 長時間在席時のメッセージ追加
    if seat == "1":
        text = text + "お仕事頑張っていて偉いね。ひと段落ついたら休憩しようよ！"
    else:
        pass
    
    return text

def generate(text):

    OUT_DIR = './'

    now = datetime.datetime.now()

    target_text = text
    target_file = 'aitalk_' + now.strftime('%Y%m%d_%H%M%S') + '.m4a' # mp3, ogg, m4a, wav いずれかのファイルパス
    # filename = './output/log_' + now.strftime('%Y%m%d_%H%M%S') + '.csv'

    # (2) AITalkWebAPIを使うためのインスタンス作成
    aitalk = AITalkWebAPI()

    # 出力ファイルから出力形式を決定
    ext = os.path.splitext(target_file)[1][1:]
    if ext == 'm4a':	# m4a拡張子はaacと設定
        ext = 'aac'

    # (3) インスタンスに指定したいパラメータをセット
    aitalk.text = target_text
    aitalk.speaker_name = 'yuzuru_emo'
    # aitalk.speaker_name = 'aoi_emo'
    # aitalk.speaker_name = 'akane_west_emo'
    aitalk.pitch = 0.9
    aitalk.range = 1.5
    aitalk.style = '{"j":"0.5"}'
    aitalk.ext = ext

    # (4) 合成
    if not aitalk.synth():
    # エラー処理
        print(aitalk.get_error(), file=sys.stderr)
    #  return 1

    # (5) ファイル保存
    if not aitalk.save_to_file(OUT_DIR + target_file):
        print('failed to save', file=sys.stderr)

    return target_file

def save(target_file):

    base_url = 'https://hackathonkiryu.blob.core.windows.net/hackathon/'

    BLOB_CONNECT_STRING = os.environ['APPSETTING_BLOB_CONNECT_STRING']

    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECT_STRING)

    my_content_settings = ContentSettings(content_type="audio/x-m4a")

    container_name = "hackathon"
    local_file_name = target_file
    upload_file_path = './' + target_file

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True, content_settings=my_content_settings)

    url = base_url + target_file

    return url

def line_api(url, text):
    LINE_ACCESS_TOKEN = os.environ['APPSETTING_LINE_ACCESS_TOKEN']

    line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

    audio_messages = AudioSendMessage(url,duration=1)
    text_messages = TextSendMessage(text)
    image_message = ImageSendMessage(
    #夕日の写真
    original_content_url='https://hackathonkiryu.blob.core.windows.net/hackathon/IMG_0948.jpeg',
    preview_image_url='https://hackathonkiryu.blob.core.windows.net/hackathon/IMG_0948.jpeg'
    #取得した写真
    # original_content_url='https://hack2021goudou.blob.core.windows.net/hackcont/camcap.jpg',
    # preview_image_url='https://hack2021goudou.blob.core.windows.net/hackcont/camcap.jpg'
)
    sticker_message = StickerSendMessage(
    package_id='446',
    sticker_id='1988'
)
    line_bot_api.broadcast(audio_messages)
    line_bot_api.broadcast(text_messages)
    # line_bot_api.broadcast(text_message)
    line_bot_api.broadcast(sticker_message)
    line_bot_api.broadcast(image_message)


## おまじない
if __name__ == "__main__":
    app.run(debug=True)
