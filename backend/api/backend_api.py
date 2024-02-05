from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.interfaces.FrontendInterface import UploadImages, SelectFace
from modules.interfaces.InsightFaceInterface import BodyExtract, Images
import httpx
import numpy as np

# Think about CPU version
URL = "http://insightface-gpu:18080"

app = FastAPI()
vectors = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/test_alive")
async def read_main():
    return {"msg": "I am alive!"}


@app.get("/test_alive/insface")
async def read_main():
    with httpx.Client() as client:
        try:
            resp = client.get(URL+"/info")
        except httpx.TimeoutException as e:
            return {"msg": "He is dead"}
    return {"msg": "He is alive too!"}


# Add images' IDs and user ID
# Merge BodyUploadImages and BodyExtract by changing schema on frontend side
@app.post("/upload_images")
async def upload_images(images: UploadImages):
    return await extract(BodyExtract(images=Images(data=images.name)))


@app.post("/select_faces")
async def select_faces(faces: SelectFace):
    faces = np.array(faces.faces)
    sim_table = np.zeros((faces.size, faces.size))
    for i in range(faces.size):
        for j in range(faces.size):
            x = np.array(vectors[i][faces[i]])
            y = np.array(vectors[j][faces[j]])
            sim_table[i, j] = (1 + np.dot(x, y)) / 2 * 100
    return sim_table.tolist()


async def extract(data):
    with httpx.Client() as client:
        global vectors
        resp = client.post(URL+"/extract", json=data.dict(), timeout=10.0)
        js = resp.json()

        bboxes = []
        vectors = []
        for i in range(0, len(js['data'])):
            bboxes.append([])
            vectors.append([])
            for j in range(0, len(js['data'][i]['faces'])):
                bboxes[i].append(js['data'][i]['faces'][j]['bbox'])
                vectors[i].append(js['data'][i]['faces'][j]['vec'])
        return bboxes
