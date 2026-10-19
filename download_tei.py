import re
from pathlib import Path
from bs4 import BeautifulSoup

TEMPLATE = Path(__file__).parent / "templates" / "tei_template.xml"

RESPONSIBILITY_TAGS = {'author': 'author', 'editor': 'editor', 'founder': 'funder', 'sponsor': 'sponsor'}
PUB_AUTHORITY_TAGS = {'publisher': 'publisher', 'distributor': 'distributor'}
ENTITY_TAGS = {
    'person': ('listPerson', 'person', 'persName'),
    'organization': ('listOrg', 'org', 'orgName'),
    'place': ('listPlace', 'place', 'placeName'),
    'work': ('listBibl', 'bibl', 'title'),
    'event': ('listEvent', 'event', 'label'),
    'term': ('list', 'item', 'term'),
}
MOTIVATIONS = {'assessing', 'bookmarking', 'classifying', 'commenting', 'describing', 'editing', 'highlighting',
               'identifying', 'linking', 'moderating', 'questioning', 'replying', 'tagging'}


def blank_nones(value):
    if isinstance(value, dict):
        return {key: blank_nones(item) for key, item in value.items()}
    if isinstance(value, list):
        return [blank_nones(item) for item in value]
    return "" if value is None else value


def generate_tei(document):
    document = blank_nones(document)
    soup = BeautifulSoup(TEMPLATE.read_text(encoding='utf-8'), 'xml')

    def add(parent, name, text=None, **attributes):
        tag = soup.new_tag(name)
        if text is not None:
            tag.string = text
        for key, value in attributes.items():
            if value != "":
                tag[key.replace('xml_', 'xml:')] = value
        parent.append(tag)
        return tag

    titleStmt = soup.find('titleStmt')
    titles = [title for title in document['title'] if title['text']]
    for title in titles:
        add(titleStmt, 'title', title['text'], xml_id=f'title-{title["id"]}', xml_lang=title['language'])
    if not titles:
        add(titleStmt, 'title', document['docTitle'])
    for responsibility in document['responsibility']:
        name = ', '.join(part for part in (responsibility['surname'], responsibility['name']) if part)
        if name:
            add(titleStmt, RESPONSIBILITY_TAGS.get(responsibility['role'], 'principal'), name,
                xml_id=f'resp-{responsibility["id"]}', sameAs=responsibility['authority'])

    publicationStmt = soup.find('publicationStmt')
    agencies = [pubAuthority for pubAuthority in document['pubAuthority'] if pubAuthority['name']]
    for pubAuthority in agencies:
        add(publicationStmt, PUB_AUTHORITY_TAGS.get(pubAuthority['role'], 'authority'), pubAuthority['name'],
            xml_id=f'pubauth-{pubAuthority["id"]}', sameAs=pubAuthority['authority'])
    placeholder = None if agencies else add(publicationStmt, 'publisher', 'Unknown')
    for identifier in document['identifier']:
        if identifier['text']:
            add(publicationStmt, 'idno', identifier['text'],
                xml_id=f'ident-{identifier["id"]}', type=identifier['type'])
    for pubPlace in document['pubPlace']:
        if pubPlace['name']:
            add(publicationStmt, 'pubPlace', pubPlace['name'],
                xml_id=f'pubplace-{pubPlace["id"]}', sameAs=pubPlace['authority'])
    for pubDate in document['pubDate']:
        if pubDate['date']:
            add(publicationStmt, 'date', pubDate['date'][:10],
                xml_id=f'pubdate-{pubDate["id"]}', when=pubDate['date'][:10])
    for license in document['license']:
        if license['text'] or license['link']:
            tei_license = add(add(publicationStmt, 'availability'), 'licence',
                              xml_id=f'license-{license["id"]}', target=license['link'])
            if license['text']:
                add(tei_license, 'p', license['text'])
    if placeholder and placeholder.find_next_sibling() is None:
        placeholder.name = 'p'
        placeholder.string = 'No publication information provided.'

    notesStmt = soup.find('notesStmt')
    for note in document['note']:
        if note['text']:
            add(notesStmt, 'note', note['text'], xml_id=f'note-{note["id"]}')
    if notesStmt.find() is None:
        notesStmt.decompose()

    sourceDesc = soup.find('sourceDesc')
    for source in document['source']:
        if source['text']:
            add(sourceDesc, 'bibl', source['text'], xml_id=f'source-{source["id"]}')
    if sourceDesc.find() is None:
        add(sourceDesc, 'p', 'No source information provided.')

    creation = soup.find('creation')
    for creationDate in document['creationDate']:
        if creationDate['date']:
            add(creation, 'date', creationDate['date'][:10],
                xml_id=f'creationdate-{creationDate["id"]}', when=creationDate['date'][:10])
    textClass = soup.find('textClass')
    for category in document['category']:
        if category['type']:
            add(textClass, 'catRef', xml_id=f'category-{category["id"]}', target=category['type'])
    profileDesc = soup.find('profileDesc')
    for abstract in document['abstract']:
        if abstract['text']:
            add(add(profileDesc, 'abstract', xml_id=f'abstract-{abstract["id"]}'), 'p', abstract['text'])

    tei_body = soup.find('body')
    lines = [line for line in document['content'].strip().split('<br>') if line.strip()] or ['']
    paragraphs = ''.join(f'<p xml:id="paragraph-{i}" n="{i}">{line}</p>' for i, line in enumerate(lines))
    content_soup = BeautifulSoup(paragraphs, 'html.parser')
    entity_of = {str(reference['id']): entity['id']
                 for entity in document['entity'] for reference in entity['reference']}
    for reference in content_soup.find_all('span', class_='reference'):
        ref_tag = soup.new_tag('ref')
        ref_tag.string = reference.text
        if reference.get('id'):
            ref_tag['xml:id'] = reference['id']
        if reference.get('data-id') in entity_of:
            ref_tag['target'] = f"#entity-{entity_of[reference['data-id']]}"
        reference.replace_with(ref_tag)
    for tag in content_soup.find_all(True):
        if tag.name not in ('p', 'ref'):
            tag.unwrap()
    tei_body.append(content_soup)

    standOff = soup.find('standOff')
    for entity in document['entity']:
        if entity['type'] not in ENTITY_TAGS:
            continue
        list_name, entity_name, label_name = ENTITY_TAGS[entity['type']]
        new_entity = add(standOff.find(list_name), entity_name,
                         xml_id=f"entity-{entity['id']}", sameAs=entity['authority'])
        labels = [label for label in entity['label'].split('\n') if label]
        for label in labels or [reference['text'] for reference in entity['reference']]:
            add(new_entity, label_name, label)

    anchored = {ref.get('xml:id') for ref in tei_body.find_all('ref')}
    listAnnotation = soup.find('listAnnotation')
    for entity in document['entity']:
        for reference in entity['reference']:
            if f'reference-{reference["id"]}' not in anchored:
                continue
            for annotation in reference['annotation']:
                tei_annotation = add(listAnnotation, 'annotation',
                                     xml_id=f'annotation-{annotation["id"]}',
                                     xml_lang=annotation['language'],
                                     motivation=annotation['motivation'] if annotation['motivation'] in MOTIVATIONS else '',
                                     target=f'#reference-{annotation["reference_id"]}')
                revision = add(tei_annotation, 'revisionDesc')
                add(revision, 'change', when=annotation['created_at'], status='created')
                add(revision, 'change', when=annotation['updated_at'], status='modified')
                if annotation['license']:
                    add(tei_annotation, 'licence', target=annotation['license'])
                if annotation['text']:
                    add(tei_annotation, 'note', annotation['text'])

    for entity_list in standOff.find_all(recursive=False):
        if entity_list.find() is None:
            entity_list.decompose()
    if standOff.find() is None:
        standOff.decompose()

    text = tei_body.get_text()
    counts = {
        'characters': len(text),
        'words': len(re.findall(r'\w+', text)),
        'sentences': len([sentence for sentence in re.split(r'(?<=[.!?])\s+', text) if sentence.strip()]),
        'references': len(tei_body.find_all('ref')),
        'annotations': len(listAnnotation.find_all('annotation')),
    }
    extent = soup.find('extent')
    for unit, count in counts.items():
        add(extent, 'measure', str(count), unit=unit, quantity=count)

    return str(soup)
