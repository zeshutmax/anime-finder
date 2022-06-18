import asyncio
import json
import os
import logging
import requests
import urllib.parse

# from dotenv import load_dotenv
# load_dotenv()

import telebot
from telebot import types
from telebot import formatting
from telebot.async_telebot import AsyncTeleBot

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

TOKEN = os.environ['TOKEN']
MAX_RETRIES = 5
MAX_RESULTS = 1

bot = AsyncTeleBot(TOKEN, parse_mode=None)


def convertToTime(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%02d:%02d:%02d" % (hour, minutes, seconds)


def findAnime(fileId):

    try:
        filepath = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={fileId}"
        ).json()['result']['file_path']

        for i in range(MAX_RETRIES):

            r = requests.get(
                "https://api.trace.moe/search?cutBorders&anilistInfo&url={}".format(urllib.parse.quote_plus(
                    f"https://api.telegram.org/file/bot{TOKEN}/{filepath}"))
            )

            if r.status_code == 200:
                break

        if r.json()['error']:
            raise ValueError(r.json()['error'])
        else:
            data = r.json()['result']
            variants = list()

            i = 0
            for d in data:
                anime = dict()
                anime['title'] = d['anilist']['title']
                anime['episode'] = d['episode'] or '1'
                anime['similarity'] = str(round(d['similarity'] * 100)) + '%'
                anime['timeFrom'] = convertToTime(d["from"])
                anime['video'] = d["video"]
                variants.append(anime)

                if i+1 == MAX_RESULTS:
                    break

                i += 1

            return variants
    except ValueError as error:
        return error

def getQuota():
    r = requests.get("https://api.trace.moe/me")
    return r.json()

@bot.message_handler(commands=['quota'])
async def handle_quota(message):
    await bot.send_message(message.chat.id, getQuota())

@bot.message_handler(commands=['start', 'help'])
@bot.message_handler(regexp="аниме")
async def handle_start_help(message):
    await bot.send_message(message.chat.id, 'Привет! \nОтправь мне скриншот из аниме 🤩')


@bot.message_handler(content_types=['photo'])
async def send_welcome(message):
    await bot.send_message(message.chat.id, 'Секундочку, уже ищу ...')

    photo = message.photo[-1]
    variants = findAnime(photo.file_id)

    for anime in variants:
        await bot.send_video(message.chat.id, anime['video'])
        await bot.reply_to(
            message,
            formatting.format_text(
                f"Я на {anime['similarity']} уверен, что это кадр из",
                formatting.hcode(anime['title']['romaji']),
                f"\nСерия №{anime['episode']}",
                f"Начинается с {formatting.hcode(anime['timeFrom'])}",
                separator="\n"
            ),
            parse_mode='HTML'
        )


@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, 'Это не скриншот! Отправь мне скриншот')


asyncio.run(bot.polling())
