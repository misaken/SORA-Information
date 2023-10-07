from flask import Flask, render_template,request
import requests
from bs4 import BeautifulSoup
#import speech_recognition as sr
#from gtts import gTTS
import tempfile
from dotenv import load_dotenv
import os
#import openai
from janome.tokenizer import Tokenizer
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

load_dotenv() # .envファイルを環境変数に設定
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
#Deepl_API_KEY = "009c5eee-3137-eead-88b3-667aa463c7d6:fx"



app = Flask(__name__)

def get_NasaData(text):
    # NASAオープンデータからデータ取得
    url = "https://data.nasa.gov/"
    options = Options()
    options.add_argument('--headless')

    browser = webdriver.Chrome(options = options)
    browser.set_page_load_timeout(60)
    browser.get(url)

    # 検索欄にワードを入力
    search_box = browser.find_element(By.ID, "search-field-small")
    search_box.send_keys(text)

    #index.phpの送信ボタンを自動で押す
    #submit = browser.find_element_by_type("submit")
    search_box.submit()
    time.sleep(3)
    current_url = browser.current_url
    
    #検索結果一覧を取得
    res = requests.get(current_url)
    soup = BeautifulSoup(res.text, "html.parser")
    searched_text=soup.find_all("a",class_="browse2-result-name-link")
    DataUrl_list=[]
    for i in range(len(searched_text)):
        DataUrl_list.append(searched_text[i].get("href"))
    DataName_list=[]
    for i in range(len(searched_text)):
        DataName_list.append(searched_text[i].get_text())
    #re_list = [DataName_list, DataUrl_list]
    re_dic = dict(zip(DataName_list, DataUrl_list))
    return re_dic

def get_n(text):
    n_list = []
    t = Tokenizer()
    for token in t.tokenize(text):
        features = token.part_of_speech.split(",")
        if features[0] == "名詞":
            n_list.append(token.surface)
    return n_list

def translator(text, to_en=True):
    # APIから翻訳情報を取得
    if to_en:
        target_lang = "EN"
    else:
        taeget_lang = "JA"
    result = requests.get( 
        # 無料版のURL
        "https://api-free.deepl.com/v2/translate",
        params={ 
            "auth_key": DEEPL_API_KEY,
            "target_lang": target_lang,
            "text": text,
        },
    ) 

    translated_text = result.json()["translations"][0]["text"]
    return translated_text


"""
#音声認識
def stt(audio):
    try:
        # r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")
        output = r.recognize_google(audio, language="ja-JP", show_all=False)
        #print("Google Speech Recognition thinks you said\n" + r.recognize_google(audio, language="ja-JP", show_all=True))
        return output
    except sr.UnknownValueError:
        return "マイクが認識できません"
    except sr.RequestError as e:
        return f"リクエストエラー : {e}"

def gen_mp3(text):
    tts = gTTS(text=text, lang="ja")
    tts.save("output.mp3")
    print("音声ファイルを保存しました")

r = sr.Recognizer()
with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source)
    print("Say something!")
    audio = r.listen(source)

text = stt(audio)
print(text)

gen_mp3(text)
"""

#ルーティング
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/search", methods=["POST"])
def search_data():
    text = request.form["input"]
    n_list = get_n(text) # 名詞のみ抽出
    translated_word = []
    for word in n_list: # 翻訳
        translated_word.append(translator(word))
    keywords = " ".join(translated_word)
    searched_dic = get_NasaData(keywords)
    print(searched_dic)
    #return render_template("index.html", arr=searched_list) # 配列の場合
    return render_template("index.html", dic=searched_dic) # 辞書の場合

@app.route('/result', methods=["GET"])
def result_get():
    # GET送信の処理
    field = request.args.get("field","")
    return render_template('result.html', message = "名前は{}です。".format(field))

@app.route('/result', methods=["POST"])
def result_post():
    # POST送信の処理
    field = request.form["field"]
    print(field)
    return render_template('result.html', message = "名前は{}です。".format(field))

if __name__ == '__main__':
    app.debug = False
    app.run(host='localhost')