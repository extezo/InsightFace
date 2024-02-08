import base64
import os
import random
from hashlib import md5

from fastapi.encoders import jsonable_encoder
from httpx import Client
from backend.api.modules.interfaces.FrontendInterface import UploadImages, SelectFace
from backend.api.modules.interfaces.InsightFaceInterface import Images

client = Client()
client_existing = Client(cookies={"user_id": "57dbf943-266a-4e92-a15c-8a473f105440"})
URL = "http://localhost:8000"


def test_set_cookie():
    response = client.get(URL + "/set_user_id")
    assert response.cookies == client.cookies


def simulate_existing_user():

    return client


def test_alive():
    client = client_existing
    response = client.post(URL+"/test_alive")
    assert response.status_code == 200
    assert "Offline" not in response.json().values()
    # assert response.json() == {"msg": "I am alive!"}


def test_upload_images_and_select_facesD():
    client = client_existing
    images = []
    test_images = ["test_images/Stallone.jpg", "test_images/3faces.jpg"]
    for image_file in test_images:
        with open(image_file, "rb") as f:
            images.append(base64.b64encode(f.read()).decode("UTF-8"))
    images = UploadImages(data=images)
    response = client.post(URL+"/upload_images", json=images.dict(), timeout=10.0)
    assert response.status_code == 200
    assert len(response.json()) > 0

    response = response.json()
    faces = SelectFace()
    random.seed(131231)
    for i in range(len(response)):
        faces.id[response["image_ids"][i]] = (int(random.random() * (len(response["bboxes"][i])-1)))
    response = client.post(URL+"/select_faces", json=faces.dict())
    assert response.status_code == 200
    assert len(response.json()["table"]) == len(faces.id)
    assert len(response.json()["table"][0]) == len(faces.id)

