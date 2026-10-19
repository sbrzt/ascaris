from typing import Literal
from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from markupsafe import escape
from marshmallow import ValidationError
from rdflib import Graph, Namespace, RDF
from starlette.middleware.sessions import SessionMiddleware
from download_tei import generate_tei
from manipulate_documents import allowed_file, read_docx, read_pdf, read_txt
from config import Base, ROOT, engine, request_scope, session
from models import (Document, Entity, Image, Reference, METADATA, RESOURCES,
                    document_schema, documents_schema, entities_schema, images_schema)
import re, secrets, shutil, os, uvicorn

UPLOAD_FOLDER = os.path.join(ROOT, 'static', 'images')
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
PARENTS = {'document_id': Document, 'entity_id': Entity, 'reference_id': Reference}
Resource = Literal[tuple(RESOURCES)]

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(24))
templates = Jinja2Templates(directory=os.path.join(ROOT, 'templates'))
templates.env.finalize = lambda value: '' if value is None else value

Base.metadata.create_all(engine)


@app.middleware('http')
async def scoped_session(request, call_next):
    token = request_scope.set(object())
    try:
        return await call_next(request)
    finally:
        session.remove()
        request_scope.reset(token)

@app.exception_handler(ValidationError)
def invalid_payload(request, error):
    return JSONResponse(error.messages, 400)


def flash(request, message):
    request.session.setdefault('flashes', []).append(message)

@pass_context
def get_flashed_messages(context):
    return context['request'].session.pop('flashes', [])

templates.env.globals['get_flashed_messages'] = get_flashed_messages

def render(request, template, **context):
    return templates.TemplateResponse(request, template, context)

def get_or_404(model, id):
    return session.get(model, id) or abort(404, f"Error: {model.__name__} with ID = {id} not found")

def abort(status, detail):
    raise HTTPException(status, detail)


def read_document(id):
    return document_schema.dump(get_or_404(Document, id))

def create_document(request, title, text):
    content = '<br>'.join(str(escape(text)).splitlines())
    document = document_schema.load({'docTitle': title, 'content': content})
    session.add(document)
    session.commit()
    return RedirectResponse(request.url_for('edit_document', id=document.id), 303)

def read_images(document_id=None):
    query = session.query(Image).filter_by(document_id=document_id) if document_id else session.query(Image)
    return images_schema.dump(query.all())

skos = Namespace('http://www.w3.org/2004/02/skos/core#')
def get_skos_concepts():
    g = Graph()
    g.parse(os.path.join(ROOT, 'instance', 'docta.ttl'), format='turtle')
    concepts = []
    for concept in g.subjects(predicate=RDF.type, object=skos.Concept):
        concept_label = g.value(subject=concept, predicate=skos.prefLabel)
        if concept_label:
            concepts.append({"value": str(concept), "label": concept_label.value})
    return concepts


def create_resource(resource, data):
    model, schema = RESOURCES[resource]
    new = schema.load(data)
    for column, parent in PARENTS.items():
        if hasattr(model, column) and not session.get(parent, getattr(new, column) or 0):
            abort(404, f"Error: {parent.__name__} with ID = {getattr(new, column)} not found")
    session.add(new)
    session.commit()
    return JSONResponse(schema.dump(new), 201)

def update_resource(resource, id, data):
    model, schema = RESOURCES[resource]
    existing = schema.load(data, instance=get_or_404(model, id), partial=True)
    session.commit()
    return JSONResponse(schema.dump(existing), 201)


@app.get('/')
def index(request: Request):
    documents = session.query(Document).order_by(Document.updated_at.desc())
    return render(request, 'index.html', documents=documents_schema.dump(documents))

@app.get('/document/{id:int}')
def get_document(id: int):
    return read_document(id)

@app.api_route('/document/{id:int}/edit', methods=['GET', 'POST'])
def edit_document(request: Request, id: int):
    document = read_document(id)
    for field in ('pubDate', 'creationDate'):
        for item in document[field]:
            if item.get('date'):
                item['date'] = item['date'][:10]

    return render(request, 'edit_document.html',
                  document=document,
                  entities=entities_schema.dump(session.query(Entity).filter_by(document_id=id).all()),
                  existing_titles=document['title'],
                  existing_responsibilities=document['responsibility'],
                  existing_pubAuthorities=document['pubAuthority'],
                  existing_pubPlaces=document['pubPlace'],
                  existing_pubDates=document['pubDate'],
                  existing_identifiers=document['identifier'],
                  existing_licenses=document['license'],
                  existing_sources=document['source'],
                  existing_notes=document['note'],
                  existing_abstracts=document['abstract'],
                  existing_creationDates=document['creationDate'],
                  existing_categories=document['category'],
                  concepts=get_skos_concepts(),
                  images=read_images(id)
                  )


@app.get('/document/new')
@app.get('/document/upload')
def new_document_form(request: Request):
    return render(request, 'new_document.html')

@app.post('/document/new')
def new_document(request: Request, docTitle: str = Form(), content: str = Form()):
    return create_document(request, docTitle, content)


@app.post('/document/upload')
def upload_document(request: Request, docTitle: str = Form(''), uploaded_file: UploadFile | None = File(None)):
    if not docTitle:
        flash(request, 'Please enter a title for your document.')
    elif not uploaded_file or not uploaded_file.filename:
        flash(request, 'Please select a file to upload.')
    elif not allowed_file(uploaded_file.filename):
        flash(request, 'Invalid file format. Please upload a supported file type.')
    else:
        file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
        if file_extension == 'docx':
            content = read_docx(uploaded_file.file)
        elif file_extension == 'pdf':
            content = read_pdf(uploaded_file.file)
        elif file_extension == 'txt':
            content = read_txt(uploaded_file.file)
        else:
            content = None
        if content:
            return create_document(request, docTitle, content)
        flash(request, 'Could not read any text from the file.')
    return render(request, 'new_document.html')


@app.post("/save_document")
def save_document(data: dict = Body()):
    document = document_schema.load(
        {'docTitle': data.get('docTitle'), 'content': data.get('content')},
        instance=get_or_404(Document, data.get("id")), partial=True)
    session.commit()
    return JSONResponse(document_schema.dump(document), 201)


@app.delete("/document/{id:int}", response_class=PlainTextResponse)
def delete_document(id: int):
    document = get_or_404(Document, id)
    for image in document.image:
        remove_image_file(image)
    session.delete(document)
    session.commit()
    return f"Success: document with ID = {id} deleted"


@app.put('/metadata/{id:int}')
def save_metadata(id: int, data: dict = Body()):
    for field_group in METADATA:
        for field in data.get(field_group) or []:
            update_resource(field_group, int(field['id']), {k: v for k, v in field.items() if k != 'id'})
    return data


@app.post('/entity/{id:int}/merge/{target_id:int}')
def merge_entity(id: int, target_id: int):
    """Link all references of one entity to another entity, then delete the first."""
    entity = get_or_404(Entity, id)
    target = get_or_404(Entity, target_id)
    if entity is target or (entity.document_id, entity.type) != (target.document_id, target.type):
        abort(400, "Error: entities must be different, of the same type and in the same document")
    target.reference.extend(list(entity.reference))
    labels = (target.label or '').split('\n') + (entity.label or '').split('\n')
    target.label = '\n'.join(dict.fromkeys(label for label in labels if label))
    session.delete(entity)
    session.commit()
    return RESOURCES['entity'][1].dump(target)


@app.get('/download_tei/{document_id:int}')
def download_tei(document_id: int):
    tei_document = generate_tei(read_document(document_id))
    return Response(tei_document, media_type='application/xml',
                    headers={'Content-Disposition': f'attachment; filename=document_{document_id}.xml'})


def image_path(image):
    return os.path.join(UPLOAD_FOLDER, image.name)

def remove_image_file(image):
    if os.path.exists(image_path(image)):
        os.remove(image_path(image))

def allowed_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS

def secure_filename(filename):
    return re.sub(r'[^A-Za-z0-9_.-]', '', os.path.basename(filename.replace('\\', '/'))).lstrip('.')

@app.post('/image/{document_id:int}')
def create_image(request: Request, document_id: int, file: UploadFile | None = File(None)):
    get_or_404(Document, document_id)
    if not file or not allowed_image(file.filename or ''):
        flash(request, 'Please select a png, jpg or jpeg file.')
    else:
        image = Image(document_id=document_id, name=secure_filename(file.filename))
        session.add(image)
        session.flush()
        image.name = f"{image.id}_{image.name}"
        with open(image_path(image), 'wb') as target:
            shutil.copyfileobj(file.file, target)
        session.commit()

    return RedirectResponse(request.url_for('edit_document', id=document_id), 303)

@app.get('/static/images')
def get_images(request: Request):
    return render(request, 'new_image.html', images=read_images())

@app.get('/static/images/{image_id:int}')
def get_image(image_id: int):
    return FileResponse(image_path(get_or_404(Image, image_id)))

@app.delete('/static/images/{image_id:int}')
def delete_image(request: Request, image_id: int):
    image = get_or_404(Image, image_id)
    remove_image_file(image)
    session.delete(image)
    session.commit()
    return render(request, 'new_image.html', images=read_images())


# after the document, image and merge routes, so their paths are matched first
@app.post('/{resource}')
def create_resource_route(resource: Resource, data: dict = Body()):
    return create_resource(resource, data)

@app.api_route('/{resource}/{id:int}', methods=['GET', 'PUT', 'DELETE'])
def resource_route(request: Request, resource: Resource, id: int, data: dict | None = Body(None)):
    model, schema = RESOURCES[resource]
    if request.method == 'PUT':
        return update_resource(resource, id, data or {})
    existing = get_or_404(model, id)
    if request.method == 'GET':
        return schema.dump(existing)
    session.delete(existing)
    session.commit()
    return PlainTextResponse(f"Success: {resource} deleted")


app.mount('/static', StaticFiles(directory=os.path.join(ROOT, 'static')), name='static')


if __name__ == '__main__':
    uvicorn.run(app, port=5000)
