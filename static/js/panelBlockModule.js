
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
      <a class="accordion-header" role="button" aria-expanded="false">${entityReferences[0].text}</a>
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
              <div class="control">
                  <input class="input entity-label-input" type="text" value="${entityReferences[0].text}" name="entity-label" placeholder="Enter entity's label">
              </div>
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

  block.addEventListener("dragstart", (event) => {
    event.dataTransfer.setData("text/plain", block.id); // Set data to be transferred
  });
  
  return block;
}

// Add a click event listener to the common ancestor of all entity accordions
const entityPanel = document.querySelector('.entity-panel')
entityPanel.addEventListener("click", function (event) {
  if (event.target.classList.contains("accordion-header")) {
    let header = event.target;
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


// Delegated, so blocks created after page load are handled too
entityPanel.addEventListener("submit", function (event) {
    event.preventDefault();
    const form = event.target;
    const block = form.closest(".panel-block");
    const entityId = Number(block.getAttribute("data-id"));
    const entityType = block.getAttribute("data-type");
    const entityLabel = form.querySelector(".entity-label-input").value;
    const entityAuthority = form.querySelector(".entity-authority-input").value;
    const entityData = {
      label: entityLabel,
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
          }
    })
    .catch(error => {
        console.error('Error updating entity', error);
    });
});

export { createPanelBlock };