import base64
import random

from httpx import Client
from backend.api.modules.interfaces.FrontendInterface import UploadImages, SelectFace

client = Client()
client_existing = Client(cookies={"user_id": "554d5ec5-63cb-48d5-b7c9-601ee0501242"})
URL = "http://localhost:8000"


def test_set_cookie():
    response = client.get(URL + "/set_user_id")
    assert response.cookies == client.cookies


def test_alive():
    client = client_existing
    response = client.post(URL+"/test_alive")
    assert response.status_code == 200
    assert "Offline" not in response.json().values()
    # assert response.json() == {"msg": "I am alive!"}


def test_upload_images_and_select_faces():
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
    #Я кривозубый крестьянин, или тут лучше сделать len(response["image_ids"]), иначе длинна всегда 2?
    for i in range(len(response)):
        faces.id[response["image_ids"][i]] = (int(random.random() * (len(response["bboxes"][i])-1)))
    response = client.post(URL+"/select_faces", json=faces.dict())
    assert response.status_code == 200
    assert len(response.json()["table"]) == len(faces.id)
    assert len(response.json()["table"][0]) == len(faces.id)

