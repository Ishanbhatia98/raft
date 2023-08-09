from fastapi.testclient import TestClient
from loguru import logger

from app.main import app

client = TestClient(app)


def test_file_upload():
    file_paths = [f"tests/images/jpg/{i}.jpg" for i in range(1, 5)]
    files = [("files", (open(file_path, "rb"))) for file_path in file_paths]

    response = client.post("/upload", files=files, params={"source": "jpg"})
    assert response.status_code == 200, response.json()
    actual_response = response.json()
    assert actual_response["message"] == "Files uploaded successfully"
    assert len(actual_response["file_paths"]) == 4
    # assert actual_response['content_type']=='jpg'
    print("x" * 100)
    from pprint import pprint

    pprint(actual_response)


if __name__ == "__main__":
    from app.database import *

    test_file_upload()
