import { createPanelBlock } from './panelBlockModule.js';
import { openAnnotations } from './annotationModule.js';

const EntityMarkingModule = (function () {

  const buttons = [
    {
      buttonSelector: ".person-button",
      spanClass: "person",
      iconClass: "user",
      panelClass: "people-panel-blocks"
    },
    {
      buttonSelector: ".place-button",
      spanClass: "place",
      iconClass: "map-marker-alt",
      panelClass: "places-panel-blocks"
    },
    {
      buttonSelector: ".work-button",
      spanClass: "work",
      iconClass: "book",
      panelClass: "works-panel-blocks"
    },
    {
      buttonSelector: ".organization-button",
      spanClass: "organization",
      iconClass: "building",
      panelClass: "organizations-panel-blocks"
    },
    {
      buttonSelector: ".event-button",
      spanClass: "event",
      iconClass: "calendar-alt",
      panelClass: "events-panel-blocks"
    },
    {
      buttonSelector: ".term-button",
      spanClass: "term",
      iconClass: "quote-left",
      panelClass: "terms-panel-blocks"
    }
  ];

  const editableContent = document.querySelector('#editableContent');
  const documentId = editableContent.getAttribute('data-documentId');

  async function post(url, data) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error(`POST ${url} failed with status ${response.status}`);
    }
    return response.json();
  }

  async function markEntity(buttonDetails) {
    const selection = window.getSelection();
    if (selection.rangeCount === 0 || selection.toString().trim() === "") return;
    const range = selection.getRangeAt(0);
    const container = range.commonAncestorContainer;
    const element = container.nodeType === Node.ELEMENT_NODE ? container : container.parentElement;
    // Only text of the document can be marked, and references do not nest
    if (!editableContent.contains(container) || element.closest('.reference')) return;
    const selectedText = range.toString();

    const span = document.createElement("span");
    try {
      // Throws when the selection cuts through another element
      range.surroundContents(span);
    } catch (error) {
      console.error('Selection cannot be marked:', error);
      return;
    }

    try {
      const entity = await post('/entity', {
        document_id: documentId,
        label: selectedText,
        type: buttonDetails.spanClass,
        authority: null
      });
      const reference = await post('/reference', {
        document_id: documentId,
        entity_id: entity.id,
        text: selectedText,
        type: entity.type
      });

      span.classList.add("button", "reference", reference.type);
      span.contentEditable = false;
      span.setAttribute("id", `reference-${reference.id}`);
      span.setAttribute("data-id", reference.id);
      span.setAttribute("data-entity", reference.entity_id);
      const icon = document.createElement("i");
      icon.classList.add("tag-icon", "fas", `fa-${buttonDetails.iconClass}`);
      span.appendChild(icon);

      const panelContent = document.querySelector(`.${buttonDetails.panelClass}`);
      panelContent.appendChild(createPanelBlock(entity, [reference]));
    } catch (error) {
      console.error('Error marking entity:', error);
      span.replaceWith(...span.childNodes);
    }
  }

  buttons.forEach(buttonDetails => {
    const button = document.querySelector(buttonDetails.buttonSelector);
    button.addEventListener("click", () => markEntity(buttonDetails));
  });

  // Delegated, so references marked after page load open their annotations too
  editableContent.addEventListener("click", function (event) {
    const reference = event.target.closest(".reference");
    if (reference) {
      event.preventDefault();
      openAnnotations(reference);
    }
  });

})();

export { EntityMarkingModule };
