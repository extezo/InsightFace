from typing import List

from PIL import ImageFont
from aiogram import types
import io
from hashlib import md5
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InputFile, BufferedInputFile, InlineKeyboardMarkup

from telegrambot.keyboards.keyboards import get_upload_btn, \
    gen_select_face_keyboard, get_clear_button,get_null_inline
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

    if users[message.from_user.id].is_compare_phase:
        await bot.delete_message(message.chat.id, message.message_id)
        if (users[message.from_user.id].current_error_send_id == -1):
            print('first err')
        else:
            await bot.delete_message(message.chat.id, users[message.from_user.id].current_error_send_id)
        err = await message.answer("❌ Вы не можете отправлять фотографии до обнуления! ❌")
        users[message.from_user.id].current_error_send_id = err.message_id
    else:

        # if (users[message.from_user.id].current_send_button_id == []):
        #     print('first')
        #
        # else:
        #     print("deleting")
            # await bot.delete_message(message.chat.id, users[message.from_user.id].current_send_button_id)
        ans = await message.bot.send_message(chat_id=message.from_user.id,
                                             text="Нажмите отправить, когда закончите добавлять фото.\n⚠⚠⚠\nПосле отправки добавление фото станет невозможным ",
                                             reply_markup=get_upload_btn()
                                             )
        users[message.from_user.id].current_send_button_id.append(ans.message_id)
        if len(users[message.from_user.id].current_send_button_id)==1:
            print("ffff")
        else:
            await bot.delete_message(message.chat.id, users[message.from_user.id].current_send_button_id[-2])
            users[message.from_user.id].current_send_button_id.remove(users[message.from_user.id].current_send_button_id[-2])
        print(users[message.from_user.id].current_send_button_id)
        fp = io.BytesIO()

        await bot.download(
            message.photo[-1],
            destination=fp
        )
        fpr=fp.read()
        if fpr in users[message.from_user.id].current_images:
            print("image already exists")
        else:
         users[message.from_user.id].current_images.append(fpr)

        fp.close()




async def send_images_with_bboxes(message, imges_with_bboxes, bboxes, user_id: int, bot: Bot):


    j = 0
    await bot.send_message(chat_id=message.chat.id, text="⚠ Нажмите ОЧИСТИТЬ, чтобы обнулить сессию и начать заново\n\n⚠ Нажимайте на кнопки под фотографиями, чтобы выбрать лица, которые вы хотите сравнить",
                           reply_markup=get_clear_button())
    for img in imges_with_bboxes:

        buf = io.BytesIO()
        img.save(buf, format='JPEG')

        keyboard = gen_select_face_keyboard(j, len(imges_with_bboxes), len(bboxes[j]))
        j = j + 1
        ph = await message.answer_photo(
            BufferedInputFile(
                buf.getvalue(),
                filename="image from buffer.jpg"
            ), reply_markup=keyboard
        )

        users[user_id].sent_images_ids.append(ph.message_id)

        buf.close()


@router.callback_query(F.data.startswith("facebutton"))
async def callbacks_num(callback: types.CallbackQuery):

    if  users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])]:
        users[callback.from_user.id].selected_num=users[callback.from_user.id].selected_num-1
    else:
        users[callback.from_user.id].selected_num = users[callback.from_user.id].selected_num +1
    if(users[callback.from_user.id].selected_num >8):

        users[callback.from_user.id].selected_num = users[callback.from_user.id].selected_num - 1
        if (users[callback.from_user.id].current_error_too_many_selected == -1):
            print('first err too many')
        else:
            await callback.bot.delete_message(callback.from_user.id, users[callback.from_user.id].current_error_too_many_selected)
        err = await callback.bot.send_message(callback.from_user.id,"❌ Вы не можете выбрать более 8 лиц ❌")
        users[callback.from_user.id].current_error_too_many_selected = err.message_id
    else:
        users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])] = not \
            users[callback.from_user.id].selected[int(callback.data.split("_")[2])][int(callback.data.split("_")[3])]

        await callback.message.edit_reply_markup(
            reply_markup=gen_select_face_keyboard(int(callback.data.split("_")[2]), int(callback.data.split("_")[1]), len(
                users[callback.from_user.id].selected[int(callback.data.split("_")[2])]),
                                                  users[callback.from_user.id].selected))
    await callback.answer()


@router.callback_query(F.data.startswith("send_backend"))
async def send_backend(callback: types.CallbackQuery):
    for i in range(len(users[callback.from_user.id].current_send_button_id)):
        await callback.bot.delete_message(callback.from_user.id, users[callback.from_user.id].current_send_button_id[i])
    users[callback.from_user.id].is_compare_phase = True

    user_id = callback.from_user.id
    client_existing = Client(cookies={"user_id": str(user_id)})


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
        users[user_id].images_ids.append(md5(image.decode('utf-8').encode()).hexdigest())
        images_idss[md5(image.decode('utf-8').encode()).hexdigest()] = image.decode('utf-8')

    # print(images_idss)
    client = client_existing
    images_to_upload = UploadImages(data=users[callback.from_user.id].base64images)


    response = client.post(URL + "/upload_images", json=images_to_upload.dict(), timeout=10.0)

    response = response.json()
    bboxes=response["bboxes"]
    jj=0
    for img in images_idss:
        users[user_id].selected.append([False] * len(bboxes[jj]))
        users[user_id].current_faces.append([False] * len(bboxes[jj]))
        jj=jj+1
    imges_with_bboxes = []
    print("len of ids")
    print(len(users[user_id].images_ids))
    for i in range(len(response["image_ids"])):
        imge = draw_rect(decode_img(images_idss[response["image_ids"][i]]), response["bboxes"][i],
                         callback.from_user.id,i)
        imges_with_bboxes.append(imge)
        # imge.show()
    await send_images_with_bboxes(callback.message, imges_with_bboxes, bboxes, user_id, callback.bot)

    await callback.answer()


@router.message(F.text.lower().startswith("очистить"))
async def clear_data(message: Message):
    current_images = []

    for messid in users[message.from_user.id].sent_images_ids:
        await message.bot.edit_message_reply_markup(chat_id=message.from_user.id,message_id=messid)

    users[message.from_user.id] = TelegramUser()

    await message.bot.send_message(chat_id=message.chat.id,
                                   text="Сессия завершена, вы снова можете отправлять фотографии",
                                   reply_markup=types.ReplyKeyboardRemove())



@router.message(F.text.lower().startswith("cравнить"))
async def compare(message: Message):
    if (users[message.from_user.id].selected_num < 2):
        if (users[message.from_user.id].current_error_too_few_selected == -1):
            print('first err too many')
        else:
            await message.bot.delete_message(message.from_user.id,
                                              users[message.from_user.id].current_error_too_few_selected)
        err = await message.bot.send_message(message.from_user.id, "❌ Выберите как минимум 2 лица ❌")
        users[message.from_user.id].current_error_too_few_selected = err.message_id
    else:
        client_existing = Client(cookies={"user_id": str(message.from_user.id)})
        client = client_existing
        faces = SelectFace()
        strs_compared = []
        images_of_faces=[]
        for i in range(len(users[message.from_user.id].images_ids)):
            fass = []
            for j in range(len(users[message.from_user.id].selected[i])):
                if users[message.from_user.id].selected[i][j]:
                    fass.append(j)
                    images_of_faces.append(users[message.from_user.id].current_faces[i][j])
                    strs_compared.append(f"i:{i + 1}  f:{j + 1}")
            print("is there warn")
            faces.id[users[message.from_user.id].images_ids[i]] = fass

        response = client.post(URL + "/select_faces", json=faces.dict())

        tab = response.json()["table"]
        rep_img=table2png(tab,images_of_faces)

        buf = io.BytesIO()
        rep_img.save(buf, format='JPEG')
        await message.answer_photo(
            BufferedInputFile(
                buf.getvalue(),
                filename="table.jpg"
            )
        )
        buf.close()
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


def draw_rect(img, bboxes, id: int,im_num:int):
    img1 = ImageDraw.Draw(img)
    font = ImageFont.truetype("telegrambot/resources/arial.ttf", 50)
    i = 1

    withh = 5
    for bbox in bboxes:
        face = img.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
        users[id].current_faces[im_num][i - 1] = face
        i = i + 1
    i=1
    for bbox in bboxes:


        # face.show()
        img1.rectangle((bbox[0], bbox[1], bbox[2], bbox[3]), outline="red", width=withh)
        img1.text((bbox[0] + withh, bbox[1] + withh), str(i), (255, 255, 255), font=font)
        i = i + 1
    return img

def table2png(table:List[List[int]] = [[0,0],[0,0]],tops =[1,2]):
    cellsize=200
    fontsize=40
    item_margin=2
    image= Image.new('RGB', (cellsize*(len(table)+1),(cellsize*(len(table)+1))), (0,0,0))
    for i in range(len(table)):
        font = ImageFont.truetype("telegrambot/resources/arial.ttf", fontsize)
        sootn=tops[i].size[0]/tops[i].size[1]
        im2 = tops[i].resize((round(cellsize*sootn),cellsize))
        # im22 = ImageDraw.Draw(im2)
        # im22.text((cellsize / 4, cellsize / 4), str(tops[i]), (255, 255, 255), font=font)
        margin_left=(cellsize-im2.size[0])/2
        image.paste(im2, ((i + 1) * cellsize+round(margin_left), 0))
        image.paste(im2, (round(margin_left), (i + 1) * cellsize))
        for j in range(len(table[i])):
            if table[i][j]>80:
                col=(102, 255, 0)
            elif table[i][j]>70:
                col=(248, 243, 24)
            else:
                col = (255, 36, 0)
            font = ImageFont.truetype("telegrambot/resources/arial.ttf", fontsize)
            im = Image.new('RGB', (cellsize-(item_margin*2), cellsize-(item_margin*2)), col)
            im1 = ImageDraw.Draw(im)
            im1.text(((cellsize/2-fontsize/2)-fontsize, (cellsize/2-fontsize/2)), str(round(table[i][j],1))+"%", (0,0,0), font=font)
            image.paste(im,((j+1)*cellsize+item_margin,(i+1)*cellsize+item_margin))
    return image
