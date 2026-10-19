from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from config import Base, session
from marshmallow_sqlalchemy import fields

class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    name = Column(String)

class Annotation(Base):
    __tablename__ = "annotation"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    reference_id = Column(Integer, ForeignKey("reference.id"))
    text = Column(String)
    motivation = Column(String)
    language = Column(String)
    license = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Reference(Base):
    __tablename__ = "reference"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    entity_id = Column(Integer, ForeignKey("entity.id"))
    text = Column(String)
    type = Column(String)
    annotation = relationship(
        Annotation,
        backref="annotation",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)

class Entity(Base):
    __tablename__ = "entity"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    type = Column(String)
    label = Column(String)
    authority = Column(String)
    reference = relationship(
        Reference,
        backref="reference",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)

class Title(Base):
    __tablename__ = "title"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    text = Column(String)
    language = Column(String)

class Responsibility(Base):
    __tablename__ = "responsibility"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    surname = Column(String)
    name = Column(String)
    authority = Column(String)
    role = Column(String)

class PubAuthority(Base):
    __tablename__ = "pub_authority"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    name = Column(String)
    authority = Column(String)
    role = Column(String)

class PubPlace(Base):
    __tablename__ = "pub_place"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    name = Column(String)
    authority = Column(String)

class PubDate(Base):
    __tablename__ = "pub_date"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    date = Column(DateTime)

class Identifier(Base):
    __tablename__ = "identifier"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    text = Column(String)
    type = Column(String)

class License(Base):
    __tablename__ = "license"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    text = Column(String)
    link = Column(String)

class Source(Base):
    __tablename__ = "source"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    text = Column(String)

class Note(Base):
    __tablename__ = "note"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    text = Column(String)

class Abstract(Base):
    __tablename__ = "abstract"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    text = Column(String)

class CreationDate(Base):
    __tablename__ = "creation_date"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    date = Column(DateTime)

class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    type = Column(String)

class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True, autoincrement=True)
    docTitle = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    image = relationship(
        Image,
        backref="document",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True
    )
    title = relationship(
        Title,
        backref="document",
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    responsibility = relationship(
        Responsibility, 
        backref='document', 
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    pubAuthority = relationship(
        PubAuthority, 
        backref='document', 
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    pubPlace = relationship(
        PubPlace, 
        backref='document', 
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    pubDate = relationship(
        PubDate, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    identifier = relationship(
        Identifier,
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    license = relationship(
        License, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True, 
        lazy=True)
    source = relationship(
        Source, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True, 
        lazy=True)
    note = relationship(
        Note,
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    abstract = relationship(
        Abstract, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    creationDate = relationship(
        CreationDate, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    category = relationship(
        Category, 
        backref='document',
        cascade="all, delete, delete-orphan",
        single_parent=True,
        lazy=True)
    entity = relationship(
        Entity,
        backref='document',
        cascade='all, delete, delete-orphan',
        single_parent=True,
        lazy=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Document {self.id}>"

def make_schema(model, **nested_fields):
    meta = type("Meta", (), {"model": model, "load_instance": True, "sqla_session": session, "include_fk": True})
    return type(f"{model.__name__}Schema", (SQLAlchemyAutoSchema,), {"Meta": meta, **nested_fields})

def nested(schema):
    return fields.Nested(schema, many=True)

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
