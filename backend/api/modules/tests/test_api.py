import base64
import random

from httpx import Client
from backend.api.modules.interfaces.FrontendInterface import UploadImages, SelectFace

URL = "http://localhost:8000"
client = Client()


def test_alive():
    response = client.get(URL+"/test_alive")
    assert response.status_code == 200
    assert response.json() == {"msg": "I am alive!"}
    response = client.get(URL + "/test_alive/insface")
    assert response.status_code == 200
    assert response.json() == {"msg": "He is alive too!"}


def test_upload_images():
    images = []
    test_images = ["test_images/Stallone.jpg", "test_images/3faces.jpg"]
    for image_file in test_images:
        with open(image_file, "rb") as f:
            images.append(base64.b64encode(f.read()).decode("UTF-8"))
    images = UploadImages(name=images)
    response = client.post(URL+"/upload_images", json=images.dict(), timeout=10.0)
    assert response.status_code == 200
    assert len(response.json()) > 0

    response = response.json()

    random.seed(131231)
    faces = []
    for i in range(len(response)):
        faces.append(int(random.random() * (len(response[i])-1)))
    response = client.post(URL+"/select_faces", json=SelectFace(faces=faces).dict())

    assert response.status_code == 200
    assert len(response.json()) == len(faces)
    assert len(response.json()[0]) == len(faces)

