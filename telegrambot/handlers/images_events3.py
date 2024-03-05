import os
import random
from typing import Dict, Any
import numpy as np

import emoji
from PIL import ImageFont
from aiogram import types
import io
from hashlib import md5
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InputFile, BufferedInputFile
from redis.asyncio import Redis

from telegrambot.keyboards.keyboards import get_upload_button, get_upload_btn, \
    gen_select_face_keyboard, get_clear_button
import base64
from httpx import Client
from telegrambot.api.modules.interfaces.FrontendInterface import UploadImages, SelectFace
from telegrambot.api.modules.interfaces.TelegramEntities import TelegramUser
from telegrambot.api.modules.interfaces.InsightFaceInterface import BodyExtract, Images
from PIL import Image, ImageDraw

# REDIS_HOST = os.environ["REDIS_HOST"]
# REDIS_PORT = int(os.environ["REDIS_PORT"])
#
# redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

router = Router()  # [1]

uid = []
client = Client()

URL = "http://26.113.24.68:8000"

users: dict[int, TelegramUser] = {}


@router.message(Command("start"))  #
async def go_main(message: Message):
    # user_data[message.from_user.id] = 0
    # print(message.from_user.id)
    await message.answer("Приветствую, я бот для сравнения лиц! чтобы начать пришли мне фотографию(-и)")


@router.message(F.photo)
async def download_photo(message: Message, bot: Bot):
    if not message.from_user.id in users:
        users[message.from_user.id] = TelegramUser()
    print("len curr img in download")
    print(len(users[message.from_user.id].current_images))
    if users[message.from_user.id].is_compare_phase:
        await bot.delete_message(message.chat.id, message.message_id)
        if (users[message.from_user.id].current_error_send_id == -1):
            print('first err')
        else:
            await bot.delete_message(message.chat.id, users[message.from_user.id].current_error_send_id)
        err = await message.answer("❌ Вы не можете отправлять фотографии до обнуления! ❌")
        users[message.from_user.id].current_error_send_id = err.message_id
    else:
        # print(message.from_user.id)
        fp = io.BytesIO()
        # print(fp.read())
        await bot.download(
            message.photo[-1],
            destination=fp
        )
        users[message.from_user.id].current_images.append(fp.read())

        fp.close()

        if (users[message.from_user.id].current_send_button_id == -1):
            print('first')
        else:
            await bot.delete_message(message.chat.id, users[message.from_user.id].current_send_button_id)
        ans = await message.answer(
            "Нажмите отправить, когда закончите добавлять фото.\n⚠⚠⚠\nПосле отправки добавление фото станет невозможным ",
            reply_markup=get_upload_btn()
        )
        users[message.from_user.id].current_send_button_id = ans.message_id


async def send_images_with_bboxes(message, imges_with_bboxes, bboxes, user_id: int, bot: Bot):
    # imges_with_bboxes[0].show()

    j = 0
    await bot.send_message(chat_id=message.chat.id, text="Нажмите ОЧИСТИТЬ, чтобы обнулить сессию и начать заново",
                           reply_markup=get_clear_button())
    for img in imges_with_bboxes:
        users[user_id].selected.append([False] * len(bboxes[j]))
        # i = 1
        # buttons = [[]]
        # for button in bboxes[j]:
        #     buttons[0].append(types.InlineKeyboardButton(text=str(i), callback_data=f'facebutton_{len(imges_with_bboxes)}_{j}_{i-1}'), )
        #     i = i + 1
        # j = j + 1

        # img.show()
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        # print(buf.getvalue())

        keyboard = gen_select_face_keyboard(j, len(imges_with_bboxes), len(bboxes[j]))
        j = j + 1
        await message.answer_photo(
            BufferedInputFile(
                buf.getvalue(),
                filename="image from buffer.jpg"
            ), reply_markup=keyboard
        )
        buf.close()


@router.callback_query(F.data.startswith("facebutton"))
async def callbacks_num(callback: types.CallbackQuery):
    users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])] = not \
        users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])]

    await callback.message.edit_reply_markup(
        reply_markup=gen_select_face_keyboard(int(callback.data.split("_")[2]), int(callback.data.split("_")[1]), len(
            users[callback.from_user.id].selected[int(callback.data.split("_")[2])]),
                                              users[callback.from_user.id].selected))
    await callback.answer()


@router.callback_query(F.data.startswith("send_backend"))
async def callbacks_num(callback: types.CallbackQuery):
    users[callback.from_user.id].is_compare_phase = True

    user_id = callback.from_user.id
    client_existing = Client(cookies={"user_id": str(user_id)})
    print("len curr img")
    print(len(users[callback.from_user.id].current_images))
    images = []
    # base64images = []

    for image in users[callback.from_user.id].current_images:
        # buffer = io.BytesIO()
        image = Image.open(io.BytesIO(image))

        images.append(image)
        # image.show()
    for image in images:
        # print(image)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        myimage = buffer.getvalue()
        # print(base64.b64encode(myimage)[1500:1530])
        users[callback.from_user.id].base64images.append(base64.b64encode(myimage))
    images_idss = {}

    images_to_extract = Images()
    for image in users[callback.from_user.id].base64images:
        images_to_extract.data.append(image)
    for image in images_to_extract.data:
        # print("============")
        # print(image[10:20])
        # print(image.decode('utf-8')[10:20])
        users[user_id].images_ids.append(md5(image.decode('utf-8').encode()).hexdigest())
        images_idss[md5(image.decode('utf-8').encode()).hexdigest()] = image.decode('utf-8')

    # print(images_idss)
    client = client_existing
    images_to_upload = UploadImages(data=users[callback.from_user.id].base64images)
    print("len to upload")
    print(len(users[callback.from_user.id].base64images))
    response = client.post(URL + "/upload_images", json=images_to_upload.dict(), timeout=10.0)

    response = response.json()
    imges_with_bboxes = []
    print("len of ids")
    print(len(users[user_id].images_ids))
    for i in range(len(response["image_ids"])):
        imge = draw_rect(decode_img(images_idss[response["image_ids"][i]]), response["bboxes"][i])
        imges_with_bboxes.append(imge)
        # imge.show()
    await send_images_with_bboxes(callback.message, imges_with_bboxes, response["bboxes"], user_id, callback.bot)

    await callback.answer()


@router.message(F.text.lower().startswith("очистить"))
async def clear_data(message: Message):
    current_images = []
    print("len curr img after clear")
    print(len(current_images))
    users[message.from_user.id] = TelegramUser()
    print(users[message.from_user.id].json)
    await message.bot.send_message(chat_id=message.chat.id,
                                   text="Сессия завершена, вы снова можете отправлять фотографии",
                                   reply_markup=types.ReplyKeyboardRemove())


# @router.message(Command("select"))
# async def send_selected(message: Message):
#     client_existing = Client(cookies={"user_id": str(message.from_user.id)})
#     client = client_existing
#     faces = SelectFace()
#
#     selected = message.text.split(" ")[1:]
#
#     for i in range(len(users[message.from_user.id].images_ids)):
#         if selected[i] == 'x':
#             print('skipped')
#         else:
#             faces.id[users[message.from_user.id].images_ids[i]] = int(selected[i]) - 1
#
#     response = client.post(URL + "/select_face", json=faces.dict())
#
#     tab = response.json()["table"]
#
#     line = ''
#     for row in tab[0]:
#         line = line + '========'
#     text = line + '\n'
#     for row in tab:
#         print(row)
#         for el in row:
#             text = text + f'{round(el, 1)}% ||'
#         text = text + '\n' + line + '\n'
#
#     await message.reply(text=text)
#     # await message.reply(text=f'{tab[0]} \n {tab[1]}')


@router.message(F.text.lower().startswith("cравнить"))
async def compare(message: Message):
    client_existing = Client(cookies={"user_id": str(message.from_user.id)})
    client = client_existing
    faces = SelectFace()
    strs_compared = []
    for i in range(len(users[message.from_user.id].images_ids)):
        fass = []
        for j in range(len(users[message.from_user.id].selected[i])):
            if users[message.from_user.id].selected[i][j]:
                fass.append(j)
                strs_compared.append(f"i:{i + 1}  f:{j + 1}")
        print("is there warn")
        faces.id[users[message.from_user.id].images_ids[i]] = fass

    # selected = message.text.split(" ")[1:]

    # for i in range(len(images_ids)):
    #     if selected[i] == 'x':
    #         print('skipped')
    #     else:
    #         faces.id[images_ids[i]] = int(selected[i]) - 1
    # faces.id[images_ids[0]] = [0, 1]
    # faces.id[images_ids[1]] = [0]
    response = client.post(URL + "/select_faces", json=faces.dict())

    tab = response.json()["table"]
    legend = 'i — image   f — face '
    line = ''
    topline = ''
    print(tab)
    print(len(tab[0]))
    print(strs_compared)
    # for i in range(tab[0]):
    #     topline = topline + strs_compared[i] + " ||"
    #     line = line + '========'
    for ta in strs_compared:
        topline = topline + ta+" ||"
        line = line + '========'
    text = legend + "\n\n\n"
    text = text + topline + '\n'
    text = text + line + '\n'
    i = 0
    for row in tab:

        for el in row:
            text = text + f'{round(el, 1)}% ||'

            text = text

        text = text + strs_compared[i]
        i=i+1
        text = text + '\n' + line + '\n'

    await message.reply(text=text)
    # await message.reply(text=f'{tab[0]} \n {tab[1]}')


@router.message()
async def send_echo(message: Message):
    await message.reply(text=f'Пожалуйста, для начала работы пришлите фотографию (-и)')


def decode_img(msg):
    # msg = msg[msg.find(b"<plain_txt_msg:img>")+len(b"<plain_txt_msg:img>"):
    # msg.find(b"<!plain_txt_msg>")]
    msg = base64.b64decode(msg)
    buf = io.BytesIO(msg)
    img = Image.open(buf)
    return img


def draw_rect(img, bboxes):
    img1 = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 50)
    i = 1

    withh = 5
    for bbox in bboxes:
        img1.rectangle((bbox[0], bbox[1], bbox[2], bbox[3]), outline="red", width=withh)
        img1.text((bbox[0] + withh, bbox[1] + withh), str(i), (255, 255, 255), font=font)
        i = i + 1
    return img
