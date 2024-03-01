import os
import random
from typing import Dict, Any
import numpy as np


from PIL import ImageFont
from aiogram import types
import io
from hashlib import md5
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InputFile, BufferedInputFile
from redis.asyncio import Redis

from telegrambot.keyboards.keyboards import get_main_keyboard, get_upload_button, get_upload_btn,gen_select_face_keyboard
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
current_images = []
uid = []
client = Client()
images_ids = []

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
    print(message.from_user.id)
    fp = io.BytesIO()
    print(fp.read())
    await bot.download(
        message.photo[-1],
        destination=fp
    )
    current_images.append(fp.read())

    fp.flush()
    print(users[message.from_user.id].current_send_button_id)
    if (users[message.from_user.id].current_send_button_id == -1):
        print('first')
    else:
        await bot.delete_message(message.chat.id, users[message.from_user.id].current_send_button_id)
    ans = await message.answer(
        "Нажмите отправить, когда закончите ",
        reply_markup=get_upload_btn()
    )
    users[message.from_user.id].current_send_button_id = ans.message_id
    print(users[message.from_user.id].current_send_button_id)


async def send_images_with_bboxes(message, imges_with_bboxes, bboxes,user_id:int):
    # imges_with_bboxes[0].show()
    print(message.from_user.id)
    j = 0
    for img in imges_with_bboxes:
        users[user_id].selected.append([False]*len(bboxes[j]))
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
        print("keygen data")
        print(f'{len(bboxes[j])}      {len(imges_with_bboxes)}')
        keyboard = gen_select_face_keyboard(j,len(imges_with_bboxes),len(bboxes[j]))
        j = j + 1
        await message.answer_photo(
            BufferedInputFile(
                buf.getvalue(),
                filename="image from buffer.jpg"
            ), reply_markup=keyboard
        )
        buf.close()
    print(users[user_id].selected)


@router.callback_query(F.data.startswith("facebutton"))
async def callbacks_num(callback: types.CallbackQuery):
        print(callback.message.message_id)
        print("айдишка папы калбэка кнопки:")
        print(callback.from_user.id)
        print(callback.data.split("_")[1:])
        users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])] = not users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])]
        print(users[callback.from_user.id].selected)

        print(users[callback.from_user.id].selected[int(callback.data.split("_")[2])])
        await callback.message.edit_reply_markup(reply_markup=gen_select_face_keyboard(int(callback.data.split("_")[2]),int(callback.data.split("_")[1]),len(users[callback.from_user.id].selected[int(callback.data.split("_")[2])]),users[callback.from_user.id].selected))
        await callback.answer()






@router.callback_query(F.data.startswith("send_backend"))
async def callbacks_num(callback: types.CallbackQuery):
    print("айдишка папы калбэка:")
    print(callback.from_user.id)

    user_id = callback.from_user.id
    client_existing = Client(cookies={"user_id": str(user_id)})
    # print(len(current_images))
    images = []
    base64images = []
    users
    for image in current_images:
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
        base64images.append(base64.b64encode(myimage))
    images_idss = {}

    images_to_extract = Images()
    for image in base64images:
        images_to_extract.data.append(image)
    for image in images_to_extract.data:
        # print("============")
        # print(image[10:20])
        # print(image.decode('utf-8')[10:20])
        images_ids.append(md5(image.decode('utf-8').encode()).hexdigest())
        images_idss[md5(image.decode('utf-8').encode()).hexdigest()] = image.decode('utf-8')

    # print(images_idss)
    client = client_existing
    images_to_upload = UploadImages(data=base64images)
    response = client.post(URL + "/upload_images", json=images_to_upload.dict(), timeout=10.0)
    print(response.json())
    response = response.json()
    imges_with_bboxes = []
    for i in range(len(response["image_ids"])):
        imge = draw_rect(decode_img(images_idss[response["image_ids"][i]]), response["bboxes"][i])
        imges_with_bboxes.append(imge)
        # imge.show()
    await send_images_with_bboxes(callback.message, imges_with_bboxes, response["bboxes"],user_id)

    await callback.answer()


@router.message(Command("select"))
async def send_selected(message: Message):
    client_existing = Client(cookies={"user_id": str(message.from_user.id)})
    client = client_existing
    faces = SelectFace()

    selected = message.text.split(" ")[1:]
    # Я кривозубый крестьянин, или тут лучше сделать len(response["image_ids"]), иначе длинна всегда 2?
    for i in range(len(images_ids)):
        if selected[i] == 'x':
            print('skipped')
        else:
            faces.id[images_ids[i]] = int(selected[i]) - 1

    response = client.post(URL + "/select_face", json=faces.dict())

    tab = response.json()["table"]

    line = ''
    for row in tab[0]:
        line = line + '========'
    text = line + '\n'
    for row in tab:
        print(row)
        for el in row:
            text = text + f'{round(el, 1)}% ||'
        text = text + '\n' + line + '\n'

    await message.reply(text=text)
    # await message.reply(text=f'{tab[0]} \n {tab[1]}')


@router.message(Command("multi"))
async def send_selected(message: Message):
    client_existing = Client(cookies={"user_id": str(message.from_user.id)})
    client = client_existing
    faces = SelectFace()
    for i in range(len(images_ids)):
        fass=[]
        for j in range(len(users[message.from_user.id].selected[i])):
            if users[message.from_user.id].selected[i][j]:
                fass.append(j)
        faces.id[images_ids[i]]=fass


    selected = message.text.split(" ")[1:]

    # for i in range(len(images_ids)):
    #     if selected[i] == 'x':
    #         print('skipped')
    #     else:
    #         faces.id[images_ids[i]] = int(selected[i]) - 1
    # faces.id[images_ids[0]] = [0, 1]
    # faces.id[images_ids[1]] = [0]
    response = client.post(URL + "/select_faces", json=faces.dict())

    tab = response.json()["table"]

    line = ''
    for row in tab[0]:
        line = line + '========'
    text = line + '\n'
    for row in tab:
        print(row)
        for el in row:
            text = text + f'{round(el, 1)}% ||'
        text = text + '\n' + line + '\n'

    await message.reply(text=text)
    # await message.reply(text=f'{tab[0]} \n {tab[1]}')


@router.message()
async def send_echo(message: Message):
    await message.reply(text=f'Это не Фото!!!  |||тут самая последняя обработка|||')


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
