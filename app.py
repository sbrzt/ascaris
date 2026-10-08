from flask import Response, abort, render_template, request, flash, jsonify, redirect, send_from_directory, url_for
from markupsafe import escape
from marshmallow import ValidationError
from rdflib import Graph, Namespace, RDF
from werkzeug.utils import secure_filename
from download_tei import generate_tei
from manipulate_documents import allowed_file, read_docx, read_pdf, read_txt
from config import app, db
from models import (Document, Entity, Image, Reference, METADATA, RESOURCES,
                    document_schema, documents_schema, entities_schema, images_schema)
import secrets, os

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images')
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
PARENTS = {'document_id': Document, 'entity_id': Entity, 'reference_id': Reference}
RESOURCE = f"any({','.join(RESOURCES)})"

app.secret_key = secrets.token_hex(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# unfilled fields are null in the database, show them empty instead of "None"
app.jinja_env.finalize = lambda value: '' if value is None else value

with app.app_context():
    db.create_all()


@app.errorhandler(ValidationError)
def invalid_payload(error):
    return jsonify(error.messages), 400


def read_document(id):
    return document_schema.dump(db.get_or_404(Document, id))

def create_document(title, text):
    # the editor stores HTML: escape the plain text and turn line breaks into <br>
    content = '<br>'.join(str(escape(text)).splitlines())
    document = document_schema.load({'docTitle': title, 'content': content})
    db.session.add(document)
    db.session.commit()
    return redirect(url_for('edit_document', id=document.id))

def read_images(document_id=None):
    query = Image.query.filter_by(document_id=document_id) if document_id else Image.query
    return images_schema.dump(query.all())

skos = Namespace('http://www.w3.org/2004/02/skos/core#')
def get_skos_concepts():
    g = Graph()
    g.parse('instance/docta.ttl', format='turtle')
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
        if hasattr(model, column) and not db.session.get(parent, getattr(new, column) or 0):
            abort(404, f"Error: {parent.__name__} with ID = {getattr(new, column)} not found")
    db.session.add(new)
    db.session.commit()
    return schema.dump(new), 201

def update_resource(resource, id, data):
    model, schema = RESOURCES[resource]
    existing = schema.load(data, instance=db.get_or_404(model, id), partial=True)
    db.session.commit()
    return schema.dump(existing), 201


@app.route('/')
def index():
    documents = Document.query.order_by(Document.updated_at.desc())
    return render_template('index.html', documents=documents_schema.dump(documents))

@app.route('/document/<int:id>', methods=['GET'])
def get_document(id):
    return read_document(id)

@app.route('/document/<int:id>/edit', methods=['GET', 'POST'])
def edit_document(id):
    document = read_document(id)
    for field in ('pubDate', 'creationDate'):
        for item in document[field]:
            if item.get('date'):
                item['date'] = item['date'][:10]

    return render_template('edit_document.html', 
                           document=document,
                           entities=entities_schema.dump(Entity.query.filter_by(document_id=id).all()),
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


@app.route('/document/new', methods=['GET', 'POST'])
def new_document():
    if request.method == 'POST':
        return create_document(request.form['docTitle'], request.form['content'])
    return render_template('new_document.html')


@app.route('/document/upload', methods=['GET', 'POST'])
def upload_document():
    if request.method == 'POST':
        title = request.form['docTitle']
        uploaded_file = request.files['uploaded_file']
        if not title:
            flash('Please enter a title for your document.', 'error')
        elif not uploaded_file:
            flash('Please select a file to upload.', 'error')
        elif not allowed_file(uploaded_file.filename):
            flash('Invalid file format. Please upload a supported file type.', 'error')
        else:
            file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
            if file_extension == 'docx':
                content = read_docx(uploaded_file)
            elif file_extension == 'pdf':
                content = read_pdf(uploaded_file)
            elif file_extension == 'txt':
                content = read_txt(uploaded_file)
            else:
                content = None
            if content:
                return create_document(title, content)
            flash('Could not read any text from the file.', 'error')
    return render_template('new_document.html')


@app.route("/save_document", methods=["POST"])
def save_document():
    data = request.get_json()
    document = document_schema.load(
        {'docTitle': data.get('docTitle'), 'content': data.get('content')},
        instance=db.get_or_404(Document, data.get("id")), partial=True)
    db.session.commit()
    return document_schema.dump(document), 201


@app.route("/document/<int:id>", methods=['DELETE'])
def delete_document(id):
    document = db.get_or_404(Document, id)
    for image in document.image:
        remove_image_file(image)
    db.session.delete(document)
    db.session.commit()
    return f"Success: document with ID = {id} deleted"


@app.route('/metadata/<int:id>', methods=['PUT'])
def save_metadata(id):
    data = request.get_json()
    for field_group in METADATA:
        for field in data.get(field_group) or []:
            update_resource(field_group, int(field['id']), {k: v for k, v in field.items() if k != 'id'})
    return jsonify(data), 200


# CRUD for entity, reference, annotation and every metadata field
@app.route(f'/<{RESOURCE}:resource>', methods=['POST'])
def create_resource_route(resource):
    return create_resource(resource, request.get_json())

@app.route(f'/<{RESOURCE}:resource>/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def resource_route(resource, id):
    model, schema = RESOURCES[resource]
    if request.method == 'PUT':
        return update_resource(resource, id, request.get_json())
    existing = db.get_or_404(model, id)
    if request.method == 'GET':
        return schema.dump(existing)
    db.session.delete(existing)
    db.session.commit()
    return f"Success: {resource} deleted"


@app.route('/entity/<int:id>/merge/<int:target_id>', methods=['POST'])
def merge_entity(id, target_id):
    """Link all references of one entity to another entity, then delete the first."""
    entity = db.get_or_404(Entity, id)
    target = db.get_or_404(Entity, target_id)
    if entity is target or (entity.document_id, entity.type) != (target.document_id, target.type):
        abort(400, "Error: entities must be different, of the same type and in the same document")
    target.reference.extend(list(entity.reference))
    # ponytail: an entity's labels are newline-separated in Entity.label,
    # move them to their own table if a label needs fields of its own (language, type)
    labels = (target.label or '').split('\n') + (entity.label or '').split('\n')
    target.label = '\n'.join(dict.fromkeys(label for label in labels if label))
    db.session.delete(entity)
    db.session.commit()
    return RESOURCES['entity'][1].dump(target)


@app.route('/download_tei/<int:document_id>')
def download_tei(document_id):
    tei_document = generate_tei(read_document(document_id))
    response = Response(tei_document, content_type='application/xml')
    response.headers['Content-Disposition'] = f'attachment; filename=document_{document_id}.xml'
    return response


def image_path(image):
    return os.path.join(app.config['UPLOAD_FOLDER'], image.name)

def remove_image_file(image):
    if os.path.exists(image_path(image)):
        os.remove(image_path(image))

def allowed_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS

@app.route('/image/<int:document_id>', methods=['POST'])
def create_image(document_id):
    db.get_or_404(Document, document_id)
    file = request.files.get('file')
    if not file or not allowed_image(file.filename):
        flash('Please select a png, jpg or jpeg file.')
    else:
        image = Image(document_id=document_id, name=secure_filename(file.filename))
        db.session.add(image)
        db.session.flush()
        # the id keeps files with the same name apart
        image.name = f"{image.id}_{image.name}"
        file.save(image_path(image))
        db.session.commit()

    return redirect(url_for('edit_document', id=document_id))

@app.route('/static/images', methods=['GET'])
def get_images():
    return render_template('new_image.html', images=read_images())

@app.route('/static/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    image = db.get_or_404(Image, image_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], image.name)

@app.route('/static/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    image = db.get_or_404(Image, image_id)
    remove_image_file(image)
    db.session.delete(image)
    db.session.commit()
    return render_template('new_image.html', images=read_images())


if __name__ == '__main__':
    app.run(debug=True)
