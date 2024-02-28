import json
import os
import uuid
from hashlib import md5
from typing import Annotated

from fastapi import FastAPI, Request, Cookie
from starlette.middleware.cors import CORSMiddleware

from modules.interfaces.RedisInterface import User, Image
from modules.interfaces.FrontendInterface import SelectFace, SelectFaces
from modules.interfaces.InsightFaceInterface import BodyExtract, Images
from redis.asyncio import Redis
import httpx
import numpy as np

# Think about CPU version
URL_IF = os.environ["INSIGHTFACE_URL"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])

app = FastAPI()
redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def middleware(request: Request, call_next):
    print(request.scope, flush=True)
    if "user_id" not in request.cookies:
        request, cookie = await set_cookie(request)
        response = await call_next(request)
        response.set_cookie(key="user_id", value=cookie)
        return response
    elif not await redis.get(request.cookies["user_id"]):
        await redis.set(request.cookies["user_id"], User().model_dump_json())
    response = await call_next(request)
    return response


async def set_cookie(request: Request):
    cookie = uuid.uuid4().__str__()
    await redis.set(cookie, User().model_dump_json())
    if not request.cookies:
        request.scope["headers"].append((b'cookie', f'user_id={cookie}'.encode("UTF-8")))
    else:
        for i, entry in enumerate(request.scope["headers"]):
            if b'cookie' in entry[0]:
                request.scope["headers"][i][1] += (f'user_id={cookie}'.encode("UTF-8"),)
                return request, cookie
    return request, cookie


@app.post("/test_alive")
async def test_alive(user_id: Annotated[str, Cookie()]):
    result = {"backend": "Online"}
    with httpx.Client() as client:
        try:
            client.get(URL_IF + "/info")
            result["InsightFace"] = "Online"
        except httpx.TimeoutException as e:
            result["InsightFace"] = "Offline"
        try:
            await redis.ping()
            result["REDIS"] = "Online"
        except TimeoutError:
            result["REDIS"] = "Offline"
    result["user_id"] = user_id
    return result


@app.post("/upload_images")
async def upload_images(images: Images, user_id: Annotated[str, Cookie()]):

    images_to_extract = Images()
    user = User(**json.loads(await redis.get(user_id)))
    images_ids = []
    for image in images.data:
        image_id = md5(image.encode()).hexdigest()
        images_ids.append(image_id)
        if image_id not in user.images.keys():
            images_to_extract.data.append(image)

    bboxes, vectors = await extract(BodyExtract(images=images_to_extract))
    for i in range(len(images_to_extract.data)):
        image_id = md5(images_to_extract.data[i].encode()).hexdigest()
        user.images[image_id] = Image(bboxes=bboxes[i], vectors=vectors[i])
    await redis.set(user_id, user.model_dump_json())
    bboxes = []
    for image_id in images_ids:
        bboxes.append(user.images[image_id].bboxes)
    return {"image_ids": images_ids, "bboxes": bboxes}


@app.post("/select_face")
async def select_face(faces: SelectFace, user_id: Annotated[str, Cookie()]):
    user = User(**json.loads(await redis.get(user_id)))
    vectors = []
    face_ids = []
    for image_id, face_id in faces.id.items():
        vectors.append(user.images[image_id].vectors)
        face_ids.append(face_id)
    face_ids = np.array(face_ids)
    sim_table = np.zeros((face_ids.size, face_ids.size))
    for i in range(face_ids.size):
        for j in range(face_ids.size):
            x = np.array(vectors[i][face_ids[i]])
            y = np.array(vectors[j][face_ids[j]])
            sim_table[i, j] = (1 + np.dot(x, y)) / 2 * 100
    return {"image_ids": list(faces.id.keys()), "table": sim_table.tolist()}


@app.post("/select_faces")
async def select_faces(faces: SelectFaces, user_id: Annotated[str, Cookie()]):
    user = User(**json.loads(await redis.get(user_id)))
    vectors = []
    face_ids = []
    for image_id, faces_id in faces.id.items():
        for face_id in faces_id:
            vectors.append(user.images[image_id].vectors)
            face_ids.append(face_id)
    face_ids = np.array(face_ids)
    sim_table = np.zeros((face_ids.size, face_ids.size))
    for i in range(face_ids.size):
        for j in range(face_ids.size):
            x = np.array(vectors[i][face_ids[i]])
            y = np.array(vectors[j][face_ids[j]])
            sim_table[i, j] = (1 + np.dot(x, y)) / 2 * 100
    return {"table": sim_table.tolist()}


async def extract(data):
    with httpx.Client() as client:
        resp = client.post(URL_IF + "/extract", json=data.dict(), timeout=10.0)
        js = resp.json()

        bboxes = []
        vectors = []
        for i in range(0, len(js['data'])):
            bboxes.append([])
            vectors.append([])
            for j in range(0, len(js['data'][i]['faces'])):
                bboxes[i].append(js['data'][i]['faces'][j]['bbox'])
                vectors[i].append(js['data'][i]['faces'][j]['vec'])
        return bboxes, vectors
