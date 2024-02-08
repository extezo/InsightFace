import json
import os
import uuid
from hashlib import md5
from typing import Union, Annotated

from fastapi import FastAPI, Response, Request, Cookie, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from modules.interfaces.RedisInterface import User, Image
from modules.interfaces.FrontendInterface import UploadImages, SelectFace
from modules.interfaces.InsightFaceInterface import BodyExtract, Images
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
import httpx
import numpy as np

# Think about CPU version
URL_IF = os.environ["INSIGHTFACE_URL"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])

app = FastAPI()
redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/set_user_id")
async def set_cookie(request: Request):
    response = JSONResponse(content="cookie check")
    if ("user_id" not in request.cookies) or (not await redis.get(request.cookies["user_id"])):
        print("Setting cookie...", flush=True)
        cookie = uuid.uuid4().__str__()
        await redis.set(cookie, User().json())
        response.set_cookie("user_id", cookie)
        print("Cookie set: " + cookie, flush=True)
    return response



@app.post("/test_alive")
async def test_alive(user_id: Annotated[str, Cookie()]):
    result = {"backend": "Online"}
    with httpx.Client() as client:
        try:
            resp = client.get(URL_IF + "/info")
            result["InsightFace"] = "Online"
        except httpx.TimeoutException as e:
            result["InsightFace"] = "Offline"
        try:
            await redis.ping()
            result["REDIS"] = "Online"
        except TimeoutError as e:
            result["REDIS"] = "Offline"
    result["cc"] = user_id
    print(result.__str__(), flush=True)
    return result


# Add images' IDs and user ID
# Merge BodyUploadImages and BodyExtract by changing schema on frontend side
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
    await redis.set(user_id, user.json())
    bboxes = []
    for image_id in images_ids:
        bboxes.append(user.images[image_id].bboxes)
    return {"image_ids": images_ids, "bboxes": bboxes}


@app.post("/select_faces")
async def select_faces(faces: SelectFace, user_id: Annotated[str, Cookie()]):
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
