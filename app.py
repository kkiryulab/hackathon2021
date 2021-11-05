from flask import Flask, Blueprint, request, abort, jsonify
from aitalk_webapi_sample import AITalkWebAPI
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings

import sys
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

app = Flask(__name__)

@app.route('/')
def generate():

    OUT_DIR = './'

    target_text = 'これはテストです。'
    target_file = 'output.m4a'	# mp3, ogg, m4a, wav いずれかのファイルパス

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

    save()

    return "OK"

def save():

    connect_str = "DefaultEndpointsProtocol=https;AccountName=hackathonkiryu;AccountKey=YcmbVD8yIYKd152BQwasa8hQTmlkyE0JrQoeWLeAJ4BFlQKZNTUrCve8icdLpdVnMn8pQZhkupnUsmaBiHsh5Q==;EndpointSuffix=core.windows.net"

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    my_content_settings = ContentSettings(content_type="audio/x-m4a")

    container_name = "hackathon"
    local_file_name = "sample4.m4a"
    upload_file_path = "./output.m4a"

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True, content_settings=my_content_settings)

## おまじない
if __name__ == "__main__":
    app.run(debug=True)