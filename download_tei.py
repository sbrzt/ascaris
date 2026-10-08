import re
from bs4 import BeautifulSoup


def read_template():
    xml_file_path = "templates/tei_template.xml"
    xml_content = ""
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
            return xml_content
    except FileNotFoundError:
        print(f"File not found: {xml_file_path}")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")


def blank_nones(value):
    if isinstance(value, dict):
        return {key: blank_nones(item) for key, item in value.items()}
    if isinstance(value, list):
        return [blank_nones(item) for item in value]
    return "" if value is None else value


def generate_tei(document):
    # fields the user has not filled yet are null in the database
    document = blank_nones(document)
    soup = BeautifulSoup(read_template(), 'xml')
    
    titleStmt = soup.find('titleStmt')
    for title in document['title']:
        tei_title = soup.new_tag('title')
        tei_title['xml:id'] = f'title-{title["id"]}'
        tei_title['xml:lang'] = title['language']
        tei_title.string = title['text']
        titleStmt.append(tei_title)
    for responsibility in document['responsibility']:
        if responsibility['role'] == 'author':
            tei_resp = soup.new_tag('author')
        elif responsibility['role'] == 'editor':
            tei_resp = soup.new_tag('editor')
        elif responsibility['role'] == 'founder':
            tei_resp = soup.new_tag('founder')
        elif responsibility['role'] == 'sponsor':
            tei_resp = soup.new_tag('sponsor')
        else:
            tei_resp = soup.new_tag('principal')
        tei_resp['xml:id'] = f'resp-{responsibility["id"]}'
        tei_resp['sameAs'] = responsibility['authority']
        tei_resp.string = f'{responsibility["surname"]}, {responsibility["name"]}'
        titleStmt.append(tei_resp)
    publicationStmt = soup.find('publicationStmt')
    for pubAuthority in document['pubAuthority']:
        if pubAuthority['role'] == 'publisher':
            tei_auth = soup.new_tag('publisher')
        elif pubAuthority['role'] == 'distributor':
            tei_auth = soup.new_tag('distributor')
        else:
            tei_auth = soup.new_tag('authority')
        tei_auth['xml:id'] = f'pubauth-{pubAuthority["id"]}'
        tei_auth['sameAs'] = pubAuthority['authority']
        tei_auth.string = pubAuthority['name']
        publicationStmt.append(tei_auth)
    for identifier in document['identifier']:
        tei_idno = soup.new_tag('idno')
        tei_idno['xml:id'] = f'ident-{identifier["id"]}'
        tei_idno['type'] = identifier['type']
        tei_idno.string = identifier['text']
        publicationStmt.append(tei_idno)
    for pubPlace in document['pubPlace']:
        tei_pubPlace = soup.new_tag('pubPlace')
        tei_pubPlace['xml:id'] = f'pubplace-{pubPlace["id"]}'
        tei_pubPlace['sameAs'] = pubPlace['authority']
        tei_pubPlace.string = pubPlace['name']
        publicationStmt.append(tei_pubPlace)
    for pubDate in document['pubDate']:
        if not pubDate["date"]:
            continue
        tei_pubDate = soup.new_tag('date')
        formatted_pubDate = pubDate["date"][:10]
        tei_pubDate['xml:id'] = f'pubdate-{pubDate["id"]}'
        tei_pubDate['when'] = formatted_pubDate
        tei_pubDate.string = formatted_pubDate
        publicationStmt.append(tei_pubDate)
    for license in document['license']:
        tei_availability = soup.new_tag('availability')
        tei_license = soup.new_tag('licence')
        tei_p = soup.new_tag('p')
        tei_license['xml:id'] = f'license-{license["id"]}'
        tei_license['target'] = license['link']
        tei_p.string = license['text']
        tei_license.append(tei_p)
        tei_availability.append(tei_license)
        publicationStmt.append(tei_availability)
    notesStmt = soup.find('notesStmt')
    for note in document['note']:
        tei_note = soup.new_tag('note')
        tei_note['xml:id'] = f'note-{note["id"]}'
        tei_note.string = note['text']
        notesStmt.append(tei_note)
    sourceDesc = soup.find('sourceDesc')
    for source in document['source']:
        tei_source = soup.new_tag('bibl')
        tei_source['xml:id'] = f'source-{source["id"]}'
        tei_source.string = source['text']
        sourceDesc.append(tei_source)
    creation = soup.find('creation')
    for creationDate in document['creationDate']:
        if not creationDate["date"]:
            continue
        tei_creationDate = soup.new_tag('date')
        formatted_creationDate = creationDate["date"][:10]
        tei_creationDate['xml:id'] = f'creationdate-{creationDate["id"]}'
        tei_creationDate['when'] = formatted_creationDate
        tei_creationDate.string = formatted_creationDate
        creation.append(tei_creationDate)
    textClass = soup.find('textClass')
    for category in document['category']:
        tei_catRef = soup.new_tag('catRef')
        tei_catRef['xml:id'] = f'category-{category["id"]}'
        tei_catRef['target'] = category['type']
        textClass.append(tei_catRef)
    profileDesc = soup.find('profileDesc')
    for abstract in document['abstract']:
        tei_abstract = soup.new_tag('abstract')
        tei_abstract['xml:id'] = f'abstract-{abstract["id"]}'
        tei_abstract.string = abstract['text']
        profileDesc.append(tei_abstract)
    
    tei_body = soup.find('body')
    clean_content = document['content'].strip()
    split_content = [chunk for chunk in clean_content.split('<br>') if chunk.strip()]
    joined_content = ''
    for i, content_chunk in enumerate(split_content):
        content_chunk = f'<p xml:id="paragraph-{i}" n="{i}">{content_chunk}</p>'
        joined_content += content_chunk
    content_soup = BeautifulSoup(joined_content, 'html.parser')
    references = content_soup.find_all('span', class_='reference')
    for reference in references:
        ref_tag = soup.new_tag('ref')
        ref_tag.string = reference.text
        for attr_name, attr_value in reference.attrs.items():
            if attr_name == 'id':
                ref_tag['xml:id'] = f'{attr_value}'
            elif attr_name == 'data-entity':
                ref_tag['target'] = f'#entity-{attr_value}'
        reference.replace_with(ref_tag)
    tei_body.append(content_soup)
    
    for entity in document['entity']:
        if entity['type'] == 'person':
            list_entity = soup.find('listPerson')
            new_entity = soup.new_tag('person')
            new_entity_label = soup.new_tag('persName')
        elif entity['type'] == 'organization':
            list_entity = soup.find('listOrg')
            new_entity = soup.new_tag('organization')
            new_entity_label = soup.new_tag('orgName')
        elif entity['type'] == 'place':
            list_entity = soup.find('listPlace')
            new_entity = soup.new_tag('place')
            new_entity_label = soup.new_tag('placeName')
        elif entity['type'] == 'work':
            list_entity = soup.find('listBibl')
            new_entity = soup.new_tag('bibl')
            new_entity_label = soup.new_tag('title')
        elif entity['type'] == 'event':
            list_entity = soup.find('listEvent')
            new_entity = soup.new_tag('event')
            new_entity_label = soup.new_tag('label')
        elif entity['type'] == 'term':
            list_entity = soup.find('list')
            new_entity = soup.new_tag('item')
            new_entity_label = soup.new_tag('term')
        new_entity['xml:id'] = f"entity-{entity['id']}"
        new_entity['sameAs'] = entity['authority']
        new_entity_label.string = entity['label']
        new_entity.append(new_entity_label)
        list_entity.append(new_entity)

    listAnnotation = soup.find('listAnnotation')
    for entity in document['entity']:
        for reference in entity['reference']:
            for annotation in reference['annotation']:
                tei_annotation = soup.new_tag('annotation')
                tei_annotation['xml:id'] = f'annotation-{annotation["id"]}'
                tei_annotation['xml:lang'] = annotation['language']
                tei_annotation['motivation'] = annotation['motivation']
                tei_annotation['target'] = f'#reference-{annotation["reference_id"]}'
                tei_annotation_note = soup.new_tag('note')
                tei_annotation_note.string = annotation['text']
                tei_annotation_license = soup.new_tag('license')
                tei_annotation_license['target'] = annotation['license']
                tei_annotation_revision = soup.new_tag('revisionDesc')
                tei_annotation_created = soup.new_tag('change')
                tei_annotation_modified = soup.new_tag('change')
                tei_annotation_created['when'] = annotation['created_at']
                tei_annotation_created['status'] = 'created'
                tei_annotation_modified['when'] = annotation['updated_at']
                tei_annotation_modified['status'] = 'modified'
                tei_annotation_revision.append(tei_annotation_created)
                tei_annotation_revision.append(tei_annotation_modified)
                tei_annotation.append(tei_annotation_revision)
                tei_annotation.append(tei_annotation_note)
                tei_annotation.append(tei_annotation_license)
                listAnnotation.append(tei_annotation)
    extent = soup.find('extent')
    text = soup.get_text()
    character_count = len(text)
    words = re.findall(r'\w+', text)
    word_count = len(words)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentence_count = len(sentences)
    tei_measure_characters = soup.new_tag('measure')
    tei_measure_characters['unit'] = 'characters'
    tei_measure_characters['quantity'] = character_count
    tei_measure_characters.string = str(character_count)
    tei_measure_words = soup.new_tag('measure')
    tei_measure_words['unit'] = 'words'
    tei_measure_words['quantity'] = word_count
    tei_measure_words.string = str(word_count)
    tei_measure_sentences = soup.new_tag('measure')
    tei_measure_sentences['unit'] = 'sentences'
    tei_measure_sentences['quantity'] = sentence_count
    tei_measure_sentences.string = str(sentence_count)

    reference_elements = tei_body.find_all('ref')
    reference_count = len(reference_elements)
    tei_measure_references = soup.new_tag('measure')
    tei_measure_references['unit'] = 'references'
    tei_measure_references['quantity'] = reference_count
    tei_measure_references.string = str(reference_count)

    annotation_elements = listAnnotation.find_all('annotation')
    annotation_count = len(annotation_elements)
    tei_measure_annotations = soup.new_tag('measure')
    tei_measure_annotations['unit'] = 'annotations'
    tei_measure_annotations['quantity'] = annotation_count
    tei_measure_annotations.string = str(annotation_count)

    extent.append(tei_measure_characters)
    extent.append(tei_measure_words)
    extent.append(tei_measure_sentences)
    extent.append(tei_measure_references)
    extent.append(tei_measure_annotations)

    # an attribute set to None is serialized without a value, which is not well-formed XML
    for tag in soup.find_all(True):
        tag.attrs = {name: value for name, value in tag.attrs.items() if value not in (None, "")}

    return soup.prettify()
