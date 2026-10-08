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

    created = c.post("/document/new", data={"docTitle": "Doc", "content": "a <b>\nc"})
    assert created.status_code == 302
    assert c.get("/document/1").get_json()["content"] == "a &lt;b&gt;<br>c"
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

    # a second mention, marked as its own entity and then linked to the first
    assert c.post("/entity", json={"document_id": 1, "label": "Alighieri", "type": "person", "authority": None}).status_code == 201
    assert c.post("/reference", json={"document_id": 1, "entity_id": 2, "text": "Alighieri", "type": "person"}).status_code == 201
    assert c.post("/entity", json={"document_id": 1, "label": "Firenze", "type": "place", "authority": None}).status_code == 201
    assert c.post("/entity/3/merge/1").status_code == 400, "merged a place into a person"
    assert c.post("/entity/1/merge/1").status_code == 400
    merged = c.post("/entity/2/merge/1")
    assert merged.status_code == 200
    assert [r["text"] for r in merged.get_json()["reference"]] == ["Dante", "Alighieri"]
    assert merged.get_json()["label"] == "Dante\nAlighieri"
    assert c.get("/entity/2").status_code == 404
    assert c.get("/reference/2").get_json()["entity_id"] == 1
    assert c.get("/annotation/1").status_code == 200

    assert c.post("/title", json={"document_id": 1, "text": "Old", "language": "en"}).status_code == 201
    assert c.put("/title/1", json={"text": "Mid", "language": "en"}).status_code == 201
    assert c.put("/metadata/1", json={
        "title": [{"id": 1, "text": "New", "language": "en"}], "responsibility": [], "pubAuthority": [],
        "source": [], "pubPlace": [], "pubDate": [], "note": [], "license": [], "identifier": [],
        "creationDate": [], "category": [], "abstract": []}).status_code == 200

    assert c.post("/pubDate", json={"document_id": 1, "date": "2023-08-31T10:00:00.640000"}).status_code == 201
    # rows the user added but has not filled yet must not break the editor or the export
    for field in ("pubAuthority", "note", "pubDate", "responsibility"):
        assert c.post(f"/{field}", json={"document_id": 1}).status_code == 201

    upload = c.post("/image/1", data={"file": (io.BytesIO(b"png"), "page.png")})
    assert upload.status_code == 302
    assert c.get("/static/images/1").status_code == 200

    content = 'Hello <span class="reference person" id="reference-1" data-id="1" data-entity="1">Dante</span> <span class="reference person" id="reference-2" data-id="2" data-entity="2">Alighieri</span><br>last line'
    assert c.post("/save_document", json={"id": 1, "docTitle": "Doc", "content": content}).status_code == 201
    assert c.get("/document/1/edit").status_code == 200
    assert len(c.get("/document/1").get_json()["image"]) == 1, "autosave detached images"

    tei = c.get("/download_tei/1")
    assert tei.status_code == 200
    soup = BeautifulSoup(tei.data, "xml")
    assert soup.find("title", string=lambda s: s and "New" in s)
    # the second span still carries the stale data-entity="2"
    assert [ref["target"] for ref in soup.find_all("ref")] == ["#entity-1", "#entity-1"]
    assert soup.find("person", attrs={"xml:id": "entity-1"}), "ref target resolves to no entity"
    assert soup.find("annotation")
    assert [name.get_text(strip=True) for name in soup.find("person").find_all("persName")] == ["Dante", "Alighieri"]
    assert soup.find("date", when="2023-08-31")
    assert "last line" in soup.find("body").get_text()
    assert b"None" not in c.get("/document/1/edit").data

    assert c.delete("/document/1").status_code == 200
