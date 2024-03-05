import base64
import random

import numpy as np
from httpx import Client
from backend.api.modules.interfaces.FrontendInterface import UploadImages, SelectFace, SelectFaces

client = Client()
client_existing = Client(cookies={"user_id": "554d5ec5-63cb-48d5-b7c9-601ee0501242"})
URL = "http://localhost:8000"

def test_alive():
    #client = client_existing
    response = client.post(URL+"/test_alive")
    print(response.read())
    assert response.status_code == 200
    assert "Offline" not in response.json().values()
    # assert response.json() == {"msg": "I am alive!"}


def test_upload_images_and_select_faces():
    #client = client_existing
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
    faces = SelectFaces()
    random.seed(56491)
    for i in range(len(response["image_ids"])):
        faces.id[response["image_ids"][i]] = (
            np.arange(1 + int(random.random() * (len(response["bboxes"][i])-1))).tolist())
    response = client.post(URL+"/select_faces", json=faces.model_dump())
    assert response.status_code == 200
    table_size = 0
    for bboxes in faces.id.values():
        table_size += len(bboxes)
    assert len(response.json()["table"]) == table_size
    assert len(response.json()["table"][0]) == table_size

