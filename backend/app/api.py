import base64

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interfaces.FrontendInterface import BodyUploadImages, BodySelectFace
from interfaces.InsightFaceInterface import BodyExtract, Images
import httpx
import numpy as np

URL = "http://insightface:18080"
#URL = "http://localhost:18081"

app = FastAPI()
vectors = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# @app.get("/upload_images_get")
# def upload_images():
#     imdata = []
#     with open("test_images/Stallone.jpg", "rb") as image_file:
#         imdata.append(base64.b64encode(image_file.read()).decode("UTF-8"))
#     images = Images(data=imdata)
#     body_extract = BodyExtract(images=images)
#     return extract(body_extract)


@app.post("/upload_images_post")
def upload_images(images: BodyUploadImages):
    for i in range(len(images.name)):
        file_content = base64.b64decode(images.name[i])
        with open("test_images/q"+str(i)+".jpg", "wb+") as f:
            f.write(file_content)
    res = extract(BodyExtract(images=Images(data=images.name)))
    print(res)
    return res


# @app.get("/select_faces_get")
# def select_faces():
#     faces = BodySelectFace(faces=[0])
#     faces = np.array(faces.faces)
#     sim_table = np.zeros((faces.size, faces.size))
#     for i in range(faces.size):
#         for j in range(faces.size):
#             x = np.array(vectors[i][faces[i]])
#             y = np.array(vectors[j][faces[j]])
#             sim_table[i, j] = (1+np.dot(x, y))/2 * 100
#     return sim_table.tolist()


@app.post("/select_faces")
def select_faces(faces: BodySelectFace):
    faces = np.array(faces.faces)
    sim_table = np.zeros((faces.size, faces.size))
    for i in range(faces.size):
        for j in range(faces.size):
            x = np.array(vectors[i][faces[i]])
            y = np.array(vectors[j][faces[j]])
            sim_table[i, j] = (1 + np.dot(x, y)) / 2 * 100
    return sim_table.tolist()


def extract(data):
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
