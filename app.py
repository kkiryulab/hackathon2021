from flask import Flask, Blueprint, request, abort, jsonify
from aitalk_webapi_sample import AITalkWebAPI

# api Blueprint作成　http://host/api 以下のものはここのルールで処理される
app = Flask(__name__)

@app.route('/')
def hello():
    name = "Hello World"
    return name

## おまじない
if __name__ == "__main__":
    app.run(debug=True)