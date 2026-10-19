const SaveDocumentModule = (function () {

  function startAutoSave(documentId) {
    const editableContent = document.getElementById("editableContent");

    let timer;
    const observer = new MutationObserver(function () {
      clearTimeout(timer);
      timer = setTimeout(() => autoSaveDocumentContent(documentId, editableContent.innerHTML), 1000);
    });

    observer.observe(editableContent, { subtree: true, characterData: true, childList: true, attributeFilter: ['data-entity'] });
  }

  function autoSaveDocumentContent(documentId, content) {
    const title = document.querySelector("h1").innerText.trim();

    fetch("/save_document", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        id: documentId,
        docTitle: title,
        content: content,
      }),
    })
      .then(function (response) {
        if (response.ok) {
          console.log("Successful autosave");
          return response.json();
        } else {
          throw new Error("Failed to autosave document");
        }
      })
      .catch(function (error) {
        console.error(error);
      });
  }

  return {
    startAutoSave,
  };
})();

export { SaveDocumentModule };