"""End-to-end MVP path: write, mark entity, annotate, metadata, facsimile, TEI export."""
import io
import os
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ASCARIS_DB"] = f"sqlite:///{tmp}/test.db"

from bs4 import BeautifulSoup

from app import app
from config import db

app.config["UPLOAD_FOLDER"] = tmp


def test_mvp_path():
    with app.app_context():
        db.create_all()
    c = app.test_client()

    assert c.post("/document/new", data={"docTitle": "Doc", "content": "x"}).status_code == 200
    assert c.get("/").status_code == 200

    entity = c.post("/entity", json={"document_id": 1, "label": "Dante", "type": "person", "authority": None})
    assert entity.status_code == 201
    reference = c.post("/reference", json={"document_id": 1, "entity_id": 1, "text": "Dante", "type": "person"})
    assert reference.status_code == 201
    annotation = c.post("/annotation", json={
        "document_id": 1, "reference_id": 1, "text": "poet",
        "language": "en", "motivation": "commenting", "license": ""})
    assert annotation.status_code == 201
    assert c.put("/annotation/1", json={
        "text": "the poet", "language": "en", "motivation": "commenting", "license": ""}).status_code == 201

    assert c.post("/title", json={"document_id": 1, "text": "Old", "language": "en"}).status_code == 201
    assert c.put("/title/1", json={"text": "Mid", "language": "en"}).status_code == 201
    assert c.put("/metadata/1", json={
        "title": [{"id": 1, "text": "New", "language": "en"}], "responsibility": [], "pubAuthority": [],
        "source": [], "pubPlace": [], "pubDate": [], "note": [], "license": [], "identifier": [],
        "creationDate": [], "category": [], "abstract": []}).status_code == 200

    upload = c.post("/image/1", data={"file": (io.BytesIO(b"png"), "page.png")})
    assert upload.status_code == 200
    assert c.get("/static/images/1").status_code == 200

    content = 'Hello <span class="reference person" id="reference-1" data-id="1" data-entity="1">Dante</span><br>'
    assert c.post("/save_document", json={"id": 1, "docTitle": "Doc", "content": content}).status_code == 201
    assert c.get("/document/1/edit").status_code == 200
    assert len(c.get("/document/1").get_json()["image"]) == 1, "autosave detached images"

    tei = c.get("/download_tei/1")
    assert tei.status_code == 200
    soup = BeautifulSoup(tei.data, "xml")
    assert soup.find("title", string=lambda s: s and "New" in s)
    ref = soup.find("ref")
    assert ref and ref["target"] == "#entity-1"
    assert soup.find("person", attrs={"xml:id": "entity-1"}), "ref target resolves to no entity"
    assert soup.find("annotation")

    assert c.delete("/document/1").status_code == 200
