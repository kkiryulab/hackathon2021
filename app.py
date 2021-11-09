from flask import Flask, Blueprint, request, abort, jsonify
from flask_restful import Api, Resource
from aitalk_webapi_sample import AITalkWebAPI
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings

import sys
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import datetime

app = Flask(__name__)
api = Api(app)


class Get(Resource):
    def get(self):
        return { 'message': 'GET request OK.' }
class Post(Resource):
    def post(self):
        json = request.get_json(force = True)
        seat = json["seat"]
        out = json["out"]

        text, url = main(seat,out)
        # url = generate(texts)

        # return { 'URL': url }
        return {"out": out, "text": text, "url": url}

api.add_resource(Get, '/get')
api.add_resource(Post, '/post')

def main(seat,out):

    # セリフの編集
    text = edit(seat,out) 

    # 音声生成
    targetfile = generate(text)

    # 音声保存
    url = save(targetfile)

    # LINE API 発射

    return text, url

def edit(seat,out):

    text = None

    # セリフの編集
    if out == "1":
        text = "朝日がでているよ!素晴らしい1日の始まりだね!"
    elif out == "2":
        text = "いま、とても気持ちの良い時間だよ。外へ出てみないかい？"
    elif out == "3":
        text = "外がすごく爽やかだよ？"
    elif out == "4":
        text = "夕日がとてもきれいだよ？見に行こうよ!" 
    elif out == "5":
        text = "夕日がきれいだよ!" 
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

    connect_str = "DefaultEndpointsProtocol=https;AccountName=hackathonkiryu;AccountKey=YcmbVD8yIYKd152BQwasa8hQTmlkyE0JrQoeWLeAJ4BFlQKZNTUrCve8icdLpdVnMn8pQZhkupnUsmaBiHsh5Q==;EndpointSuffix=core.windows.net"

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

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

## おまじない
if __name__ == "__main__":
    app.run(debug=True)