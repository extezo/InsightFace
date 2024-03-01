import random

from PIL import ImageFont
from aiogram import types
import io
from hashlib import md5
from aiogram import Router, F, Bot
from aiogram.client import bot
from aiogram.filters import Command
from aiogram.types import Message, InputFile, BufferedInputFile
from telegrambot.keyboards.keyboards import get_main_keyboard, get_upload_button,get_upload_btn
import base64
from httpx import Client
from telegrambot.api.modules.interfaces.FrontendInterface import UploadImages, SelectFace
from telegrambot.api.modules.interfaces.InsightFaceInterface import BodyExtract, Images
from PIL import Image, ImageDraw

router = Router()  # [1]
current_images = []
uid = []
client = Client()
images_ids = []

URL = "http://26.113.24.68:8000"

csb = ['nan']


@router.message(Command("start"))  # [2]
async def go_main(message: Message):
    # user_data[message.from_user.id] = 0
    # print(message.from_user.id)
    await message.answer("Приветствую, я бот для сравнения лиц! чтобы начать пришли мне фотографию(-и)")


@router.message(F.photo)
async def download_photo(message: Message, bot: Bot):
    uid.append(message.from_user.id)
    print(message.from_user.id)
    print(type(message.from_user.id))
    fp = io.BytesIO()
    # current_images.append(message.photo[-1])
    # print(len(current_images))
    # print(current_images)
    # await bot.download(
    #    message.photo[-1],
    #   destination=f"C:/Users\myzg\Desktop/frombot/{message.photo[-1].file_id}.jpg"
    # )
    print(fp.read())
    await bot.download(
        message.photo[-1],
        destination=fp
    )
    current_images.append(fp.read())

    fp.flush()
    if (csb[0] == 'nan'):
        print('first')
    else:
        await bot.delete_message(message.chat.id, csb[0].message_id)
    ans = await message.answer(
        "Нажмите отправить, когда закончите ",
        reply_markup=get_upload_btn()
    )
    csb[0] = ans




async def send_images_with_bboxes(message, imges_with_bboxes,bboxes):
    # imges_with_bboxes[0].show()
    j = 0
    for img in imges_with_bboxes:

        i = 1
        buttons = [
            [
                # types.InlineKeyboardButton(text="1", callback_data="main_beats"),
                # types.InlineKeyboardButton(text="2", callback_data="main_service")
            ]
        ]
        for button in bboxes[j]:
            buttons[0].append(types.InlineKeyboardButton(text=str(i), callback_data="main_beats"),)
            i=i+1
        j=j+1
        i = 1
        # img.show()
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        # print(buf.getvalue())

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer_photo(
            BufferedInputFile(
                buf.getvalue(),
                filename="image from buffer.jpg"
            ), reply_markup=keyboard
        )
        buf.close()


@router.callback_query(F.data.startswith("send_backend"))
async def callbacks_num(callback: types.CallbackQuery):

    client_existing = Client(cookies={"user_id": str(uid[0])})
    # print(len(current_images))
    images = []
    base64images = []
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
    print(uid[0])
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
    await send_images_with_bboxes(callback.message, imges_with_bboxes,response["bboxes"])
    # faces = SelectFace()
    # random.seed(131231)
    #
    # for i in range(len(response["image_ids"])):
    #     faces.id[response["image_ids"][i]] = (0)
    # response = client.post(URL + "/select_faces", json=faces.dict())
    # print(response.json())
    # faces = SelectFace()
    # random.seed(131231)
    # for i in range(len(response)):
    #     faces.id[response["image_ids"][i]] = (int(random.random() * (len(response["bboxes"][i]) - 1)))
    # response = client.post(URL + "/select_faces", json=faces.dict())
    # assert response.status_code == 200
    # assert len(response.json()["table"]) == len(faces.id)
    # assert len(response.json()["table"][0]) == len(faces.id)
    await callback.answer()


@router.message(Command("select"))
async def send_selected(message: Message):
    client_existing = Client(cookies={"user_id": str(uid[0])})
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

    line=''
    for row in tab[0]:
        line = line + '========'
    text= line +'\n'
    for row in tab:
        print(row)
        for el in row:
            text = text + f'{round(el,1)}% ||'
        text = text + '\n'+line+'\n'

    await message.reply(text=text)
    # await message.reply(text=f'{tab[0]} \n {tab[1]}')
@router.message(Command("multi"))
async def send_selected(message: Message):
    client_existing = Client(cookies={"user_id": str(uid[0])})
    client = client_existing
    faces = SelectFace()

    selected = message.text.split(" ")[1:]

    # for i in range(len(images_ids)):
    #     if selected[i] == 'x':
    #         print('skipped')
    #     else:
    #         faces.id[images_ids[i]] = int(selected[i]) - 1
    faces.id[images_ids[0]] = [0, 1]
    faces.id[images_ids[1]] = [0]
    response = client.post(URL + "/select_faces", json=faces.dict())

    tab = response.json()["table"]

    line=''
    for row in tab[0]:
        line = line + '========'
    text= line +'\n'
    for row in tab:
        print(row)
        for el in row:
            text = text + f'{round(el,1)}% ||'
        text = text + '\n'+line+'\n'

    await message.reply(text=text)
    # await message.reply(text=f'{tab[0]} \n {tab[1]}')


@router.message()
async def send_echo(message: Message):
    await message.reply(text=f'{message.text}   |||тут самая последняя обработка|||')


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
    i=1

    withh=5
    for bbox in bboxes:
        img1.rectangle((bbox[0], bbox[1], bbox[2], bbox[3]), outline="red", width=withh)
        img1.text((bbox[0]+withh, bbox[1]+withh), str(i), (255, 255, 255), font=font)
        i=i+1
    return img
