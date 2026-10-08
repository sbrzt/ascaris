
// An entity has one label per line of its label field: one tag in the header, one input in the form
function renderLabels(block, labels) {
  block.querySelector(".accordion-header").replaceChildren(...labels.map(function (label) {
    const tag = document.createElement("span");
    tag.classList.add("tag", "is-light", "mr-1");
    tag.textContent = label;
    return tag;
  }));
  const field = block.querySelector(".entity-label");
  field.querySelectorAll(".control").forEach((control) => control.remove());
  labels.forEach(function (label) {
    const control = document.createElement("div");
    control.classList.add("control", "mb-2");
    const input = document.createElement("input");
    input.classList.add("input", "entity-label-input");
    input.type = "text";
    input.name = "entity-label";
    input.placeholder = "Enter entity's label";
    input.value = label;
    control.appendChild(input);
    field.appendChild(control);
  });
}

function createPanelBlock(entityData, entityReferences) {

  let block = document.createElement("div");
  block.classList.add(
    "box", 
    "panel-block", 
    `${entityData.type}-block`
    );
  block.setAttribute("id", `entity-${entityData.id}`);
  block.setAttribute("data-id", entityData.id);
  block.setAttribute("data-type", entityData.type);
  block.setAttribute("draggable", true);

  const entityHTML = `
    <div class="header-wrapper">
      <span class="panel-icon">
          <i class="fas fa-${entityData.type}"></i>
      </span>
      <a class="accordion-header" role="button" aria-expanded="false"></a>
      <div class="accordion-utilities">
          <span class="counter tag is-info is-light">${entityReferences.length}</span>
          <button class="button delete-button">
              <i class="fas fa-remove"></i>
          </button>
      </div>
    </div>
    <div class="accordion-content is-hidden">
      <form class="entity-form" method="PUT">
          <div class="field entity-label">
              <label class="label">Label</label>
          </div>
          <div class="field entity-authority">
              <label class="label">Authority record</label>
              <div class="control">
                  <input class="input entity-authority-input" type="text" name="entity-authority" placeholder="Enter entity's authority">
              </div>
          </div>
          <div class="field">
              <div class="control">
                  <button class="button is-link update-entity" type="submit">Submit</button>
              </div>
          </div>
      </form>
    </div>
  `;
  
  block.innerHTML = entityHTML;
  renderLabels(block, entityData.label.split("\n"));

  return block;
}

// Add a click event listener to the common ancestor of all entity accordions
const entityPanel = document.querySelector('.entity-panel')
entityPanel.addEventListener("click", function (event) {
  if (event.target.closest(".accordion-header")) {
    let header = event.target.closest(".accordion-header");
    let content = header.parentNode.nextElementSibling;
    let isExpanded = header.getAttribute("aria-expanded");
    if (isExpanded === "false") {
      header.setAttribute("aria-expanded", "true");
    } else {
      header.setAttribute("aria-expanded", "false");
    }
    content.classList.toggle("is-hidden");
  } 
  
  else if (event.target.closest(".delete-button")) {
    const block = event.target.closest(".panel-block");
    fetch(`/entity/${block.getAttribute("data-id")}`, {
      method: 'DELETE',
      headers: {
          'Content-Type': 'application/json'
      }
    })
    .then(response => {
      if (response.ok) {
          console.log('Entity and references deleted successfully');
      } else {
          console.error('Error deleting entity and references');
      }
    })
    .catch(error => {
        console.error('Error deleting entity and references', error);
    });
    block.remove();
    let references = document.querySelectorAll(".reference");
    references.forEach(function (reference) {
        if (reference.getAttribute("data-entity") === block.getAttribute("data-id")) {
          /*  
          const counter = reference.querySelector(".counter");
          counter.textContent = "";
          */
            reference.replaceWith(reference.textContent);
        }
    });
  }
});


// Dropping an entity on another one of the same type merges them:
// the references of the dragged entity are linked to the target entity
entityPanel.addEventListener("dragstart", function (event) {
  const block = event.target.closest(".panel-block");
  if (block) {
    event.dataTransfer.setData("text/plain", block.getAttribute("data-id"));
  }
});

entityPanel.addEventListener("dragover", function (event) {
  const target = event.target.closest(".panel-block");
  if (target) {
    event.preventDefault();
    target.classList.add("valid-drop-target");
  }
});

entityPanel.addEventListener("dragleave", function (event) {
  const target = event.target.closest(".panel-block");
  if (target && !target.contains(event.relatedTarget)) {
    target.classList.remove("valid-drop-target");
  }
});

entityPanel.addEventListener("drop", async function (event) {
  const target = event.target.closest(".panel-block");
  if (!target) return;
  event.preventDefault();
  target.classList.remove("valid-drop-target");
  const dragged = document.getElementById(`entity-${event.dataTransfer.getData("text/plain")}`);
  if (!dragged || dragged === target || dragged.getAttribute("data-type") !== target.getAttribute("data-type")) return;

  const draggedId = dragged.getAttribute("data-id");
  const targetId = target.getAttribute("data-id");
  const response = await fetch(`/entity/${draggedId}/merge/${targetId}`, { method: 'POST' });
  if (!response.ok) {
    console.error('Error merging entities');
    return;
  }
  const entity = await response.json();
  document.querySelectorAll(`.reference[data-entity="${draggedId}"]`).forEach(function (reference) {
    reference.setAttribute("data-entity", targetId);
  });
  renderLabels(target, entity.label.split("\n"));
  target.querySelector(".counter").textContent = entity.reference.length;
  dragged.remove();
});

// Delegated, so blocks created after page load are handled too
entityPanel.addEventListener("submit", function (event) {
    event.preventDefault();
    const form = event.target;
    const block = form.closest(".panel-block");
    const entityId = Number(block.getAttribute("data-id"));
    const entityType = block.getAttribute("data-type");
    // an emptied input removes that label
    const labels = Array.from(form.querySelectorAll(".entity-label-input"), (input) => input.value.trim()).filter(Boolean);
    const entityAuthority = form.querySelector(".entity-authority-input").value;
    const entityData = {
      label: labels.join("\n"),
      authority: entityAuthority,
      type: entityType,
    };
    // Send a PUT request to update the entity
    fetch(`/entity/${entityId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(entityData),
    })
    .then(response => {
        if (response.ok) {
            console.log('Entity updated successfully');
            renderLabels(block, labels);
          }
    })
    .catch(error => {
        console.error('Error updating entity', error);
    });
});

export { createPanelBlock };