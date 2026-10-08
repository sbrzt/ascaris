# ASCARIS

A lightweight web application for digital scholarly editing and semantic publishing.

Write or upload a text, mark the people, places, works, organizations, events and terms it mentions, annotate those mentions, describe the edition with bibliographic metadata, and export the result as TEI XML that is valid against `tei_all`.

ASCARIS is a single-user prototype. It has no login and is meant to run on your own machine.

## Install and run

You need [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python app.py
```

Open <http://127.0.0.1:5000>. The database is created on first start.

## How to use it

1. **Create a document.** Choose *New document*, then either type the text or upload a `.txt`, `.docx` or `.pdf` file. The editor opens.
2. **Mark entities.** Select a piece of text and press *Person*, *Place*, *Work*, *Organization*, *Event* or *Term*. The mention is highlighted and the entity appears in the panel on the left.
3. **Link mentions.** Each marking creates a new entity. When two entities are the same thing, drag one onto the other in the panel: its mentions move to the target, and its label is added to the target's labels.
4. **Describe an entity.** Click an entity in the panel to edit its labels and add an authority record, such as a VIAF or GeoNames URI. Emptying a label field and pressing *Submit* removes that label.
5. **Annotate.** Click a highlighted mention to add, edit or delete annotations on it.
6. **Add metadata.** The *Metadata* tab holds titles, responsibilities, publication details, identifiers, licence, sources, notes, abstract, creation date and category. Add a row with the plus button, fill it in, and press *Save Changes*.
7. **Add facsimiles.** The *Facsimile* tab uploads `.png`, `.jpg` and `.jpeg` images for the document.
8. **Export.** *Download › XML-TEI* gives you the TEI file.

The text is saved automatically one second after you stop typing.

## TEI export

- The text becomes one `<p>` per line, with each mention as a `<ref>` that points to its entity.
- Entities are listed in `<standOff>` (`<listPerson>`, `<listPlace>`, `<listOrg>`, `<listBibl>`, `<listEvent>`, and a `<list>` of terms), one name element per label and the authority record in `sameAs`.
- Annotations are written to `<listAnnotation>`, each pointing to its mention.
- Metadata fills the `<teiHeader>`. Rows left empty are skipped.

## Development

```sh
uv run pytest
```

The test walks the whole path through the application and validates the exported TEI against `schema/tei_all.rng` (TEI P5 4.12.0). Compiling that schema takes about 15 seconds.

Layout:

- `app.py`: routes. One generic set of create, read, update and delete routes serves entities, references, annotations and every metadata field.
- `models.py`: database models and their schemas.
- `download_tei.py`: TEI export, built on `templates/tei_template.xml`.
- `manipulate_documents.py`: text extraction from uploaded files.
- `static/js/`: the editor, one module per concern.
- `instance/docta.ttl`: the SKOS vocabulary behind the *Category* field.

Set `ASCARIS_DB` to a SQLAlchemy URL to use a database other than `instance/test2.db`. Uploaded images are stored in `static/images/`.

## Known limits

- No authentication, and the text of a document is stored and shown as HTML without sanitizing. Do not expose the application to a network you do not trust.
- Changing the database models needs a manual migration; there is no migration tooling.
- A merged entity cannot be split. Delete it and mark the mentions again.
- Edits made less than a second before closing the tab are not saved.
- Export to HTML with RDFa is planned and not yet available.

## License

GPL-3.0. See `LICENSE`. The TEI schema in `schema/` is published by the TEI Consortium under CC BY and BSD-2.
