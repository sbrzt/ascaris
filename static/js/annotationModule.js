// One modal per reference. Modals and annotation cards that the server did not render
// are cloned from the <template> elements in edit_document.html.
const group = document.querySelector('.annotation-group');
const documentId = document.querySelector('#editableContent').getAttribute('data-documentId');
const jsonHeaders = { 'Content-Type': 'application/json' };

function cloneTemplate(id) {
    return document.getElementById(id).content.firstElementChild.cloneNode(true);
}

function openAnnotations(reference) {
    const referenceId = reference.getAttribute('data-id');
    let modal = group.querySelector(`.annotation-modal[data-reference="${referenceId}"]`);
    if (!modal) {
        modal = cloneTemplate('annotation-modal-template');
        modal.setAttribute('data-reference', referenceId);
        modal.querySelector('.modal-card-title').textContent = `Annotations for ${reference.textContent}`;
        group.appendChild(modal);
    }
    modal.classList.add('is-active');
}

async function addAnnotation(modal) {
    const referenceId = modal.getAttribute('data-reference');
    const response = await fetch('/annotation', {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify({
            document_id: documentId,
            reference_id: referenceId,
            text: "",
            language: "",
            motivation: "",
            license: ""
        }),
    });
    if (!response.ok) {
        console.error('Error creating annotation');
        return;
    }
    const data = await response.json();
    const card = cloneTemplate('annotation-template');
    card.setAttribute('data-id', data.id);
    card.querySelector('.card-header-title').textContent = `Annotation ${referenceId}-${data.id}`;
    card.querySelector('.annotation-created').textContent = data.created_at;
    card.querySelector('.annotation-modified').textContent = data.updated_at;
    modal.querySelector('.modal-card-body').appendChild(card);
}

async function updateAnnotation(card) {
    const response = await fetch(`/annotation/${card.getAttribute('data-id')}`, {
        method: 'PUT',
        headers: jsonHeaders,
        body: JSON.stringify({
            text: card.querySelector('.annotation-text').value,
            language: card.querySelector('.annotation-language').value,
            motivation: card.querySelector('.annotation-motivation').value,
            license: card.querySelector('.annotation-license').value
        }),
    });
    if (!response.ok) {
        console.error('Error updating annotation');
        return;
    }
    const data = await response.json();
    card.querySelector('.annotation-modified').textContent = data.updated_at;
}

async function removeAnnotation(card) {
    const response = await fetch(`/annotation/${card.getAttribute('data-id')}`, { method: 'DELETE' });
    if (response.ok) {
        card.remove();
    } else {
        console.error('Error deleting annotation');
    }
}

function toggleAnnotation(card) {
    const content = card.querySelector('.annotation-content');
    const icon = card.querySelector('.annotation-icon');
    const wasHidden = getComputedStyle(content).display === 'none';
    content.style.display = wasHidden ? 'block' : 'none';
    icon.classList.toggle('fa-angle-up', wasHidden);
    icon.classList.toggle('fa-angle-down', !wasHidden);
}

group.addEventListener('click', function (event) {
    const modal = event.target.closest('.annotation-modal');
    if (!modal) return;
    const card = event.target.closest('.annotation');
    if (event.target.closest('.modal-background, .modal-card-head .delete')) {
        modal.classList.remove('is-active');
    } else if (event.target.closest('.add-annotation-button')) {
        addAnnotation(modal);
    } else if (event.target.closest('.delete-annotation-button')) {
        removeAnnotation(card);
    } else if (event.target.closest('.annotation-header')) {
        toggleAnnotation(card);
    }
});

group.addEventListener('submit', function (event) {
    event.preventDefault();
    updateAnnotation(event.target.closest('.annotation'));
});

document.addEventListener('keydown', function (event) {
    if (event.code === 'Escape') {
        group.querySelectorAll('.modal.is-active').forEach((modal) => modal.classList.remove('is-active'));
    }
});

export { openAnnotations };
