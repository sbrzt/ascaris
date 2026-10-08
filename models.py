from datetime import datetime
from config import db, ma
from marshmallow_sqlalchemy import fields

class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    name = db.Column(db.String)

class Annotation(db.Model):
    __tablename__ = "annotation"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    reference_id = db.Column(db.Integer, db.ForeignKey("reference.id"))
    text = db.Column(db.String)
    motivation = db.Column(db.String)
    language = db.Column(db.String)
    license = db.Column(db.String)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Reference(db.Model):
    __tablename__ = "reference"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    entity_id = db.Column(db.Integer, db.ForeignKey("entity.id"))
    text = db.Column(db.String)
    type = db.Column(db.String)
    annotation = db.relationship(
        Annotation,
        backref="annotation",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)

class Entity(db.Model):
    __tablename__ = "entity"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    type = db.Column(db.String)
    label = db.Column(db.String)
    authority = db.Column(db.String)
    reference = db.relationship(
        Reference,
        backref="reference",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)

class Title(db.Model):
    __tablename__ = "title"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    text = db.Column(db.String)
    language = db.Column(db.String)

class Responsibility(db.Model):
    __tablename__ = "responsibility"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"))
    surname = db.Column(db.String)
    name = db.Column(db.String)
    authority = db.Column(db.String)
    role = db.Column(db.String)

class PubAuthority(db.Model):
    __tablename__ = "pub_authority"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    name = db.Column(db.String)
    authority = db.Column(db.String)
    role = db.Column(db.String)

class PubPlace(db.Model):
    __tablename__ = "pub_place"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    name = db.Column(db.String)
    authority = db.Column(db.String)

class PubDate(db.Model):
    __tablename__ = "pub_date"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    date = db.Column(db.DateTime)

class Identifier(db.Model):
    __tablename__ = "identifier"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    text = db.Column(db.String)
    type = db.Column(db.String)

class License(db.Model):
    __tablename__ = "license"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    text = db.Column(db.String)
    link = db.Column(db.String)

class Source(db.Model):
    __tablename__ = "source"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    text = db.Column(db.String)

class Note(db.Model):
    __tablename__ = "note"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    text = db.Column(db.String)

class Abstract(db.Model):
    __tablename__ = "abstract"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    text = db.Column(db.String)

class CreationDate(db.Model):
    __tablename__ = "creation_date"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    date = db.Column(db.DateTime)

class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    type = db.Column(db.String)

class Document(db.Model):
    __tablename__ = "document"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    docTitle = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.relationship(
        Image,
        backref="document",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True
    )
    title = db.relationship(
        Title,
        backref="document",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    responsibility = db.relationship(
        Responsibility, 
        backref='document', 
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    pubAuthority = db.relationship(
        PubAuthority, 
        backref='document', 
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    pubPlace = db.relationship(
        PubPlace, 
        backref='document', 
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    pubDate = db.relationship(
        PubDate, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    identifier = db.relationship(
        Identifier,
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    license = db.relationship(
        License, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True, 
        lazy=True)
    source = db.relationship(
        Source, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True, 
        lazy=True)
    note = db.relationship(
        Note,
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    abstract = db.relationship(
        Abstract, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    creationDate = db.relationship(
        CreationDate, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    category = db.relationship(
        Category, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    entity = db.relationship(
        Entity,
        backref='document',
        cascade='all, delete, delete-orphan',
        single_parent=True,
        lazy=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Document {self.id}>"

def make_schema(model, **nested_fields):
    meta = type("Meta", (), {"model": model, "load_instance": True, "sqla_session": db.session, "include_fk": True})
    return type(f"{model.__name__}Schema", (ma.SQLAlchemyAutoSchema,), {"Meta": meta, **nested_fields})

def nested(schema):
    return fields.Nested(schema, many=True)

# URL segment and Document relationship name -> model
METADATA = {
    "title": Title,
    "responsibility": Responsibility,
    "pubAuthority": PubAuthority,
    "pubPlace": PubPlace,
    "pubDate": PubDate,
    "identifier": Identifier,
    "license": License,
    "source": Source,
    "note": Note,
    "abstract": Abstract,
    "creationDate": CreationDate,
    "category": Category,
}

schemas = {name: make_schema(model) for name, model in METADATA.items()}
schemas["annotation"] = make_schema(Annotation)
schemas["reference"] = make_schema(Reference, annotation=nested(schemas["annotation"]))
schemas["entity"] = make_schema(Entity, reference=nested(schemas["reference"]))
ImageSchema = make_schema(Image)
DocumentSchema = make_schema(
    Document,
    image=nested(ImageSchema),
    **{name: nested(schema) for name, schema in schemas.items() if name not in ("reference", "annotation")})

RESOURCES = {name: (schema.Meta.model, schema()) for name, schema in schemas.items()}

entities_schema = schemas["entity"](many=True)
images_schema = ImageSchema(many=True)
document_schema = DocumentSchema()
documents_schema = DocumentSchema(many=True)
