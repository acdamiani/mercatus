import requests
import json
import gtts as spech
import time
import datetime
import uuid
import os
import RPi.GPIO as GPIO
import sys
from mfrc522 import SimpleMFRC522


def time_period(t):
    if (t > 0) and (t <= 12):
        return "Morning"
    elif (t > 12) and (t <= 16):
        return "Afternoon"
    elif t > 16:
        return "Evening"


def acro(s):
    return " ".join(s)


def say(text):
    p = f"/tmp/mercatus-audio-{uuid.uuid4().hex}.mp3"

    tts = speech.gTTS(text)
    tts.save(p)

    os.system(f"mpv {p}")
    os.remove(p)


reader = SimpleMFRC522()

try:
    while True:
        print("Hold a tag near the reader")
        (
            id,
            text,
        ) = reader.read()

        p = f"/tmp/mercatus-audio-{uuid.uuid4().hex}.mp3"

        print(datetime.datetime.now().hour)

        response = json.loads(
            requests.get(
                "https://zunrw2co73.execute-api.us-east-2.amazonaws.com/default/tradeStocks"
            ).text
        )
        bought_s = response["data"]["bought_symbols"]
        bought_a = []

        for x in bought_s:
            bought_a.append(acro(x))

        bought = ",".join(bought_a)

        if bought == "":
            say(f"Did not buy anything today")
        else:
            say(f"The bot bought these stocks today: {bought}")
except KeyboardInterrupt:
    GPIO.cleanup()
    raise
