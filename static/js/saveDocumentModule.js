const SaveDocumentModule = (function () {

  function startAutoSave(documentId) {
    const editableContent = document.getElementById("editableContent");

    // Save once the content has been still for a second
    // ponytail: edits made less than 1s before closing the tab are lost, flush on pagehide if that matters
    let timer;
    const observer = new MutationObserver(function () {
      clearTimeout(timer);
      timer = setTimeout(() => autoSaveDocumentContent(documentId, editableContent.innerHTML), 1000);
    });

    // Configure the observer to monitor changes in the content
    observer.observe(editableContent, { subtree: true, characterData: true, childList: true });
  }

  // Function to autosave the document content
  function autoSaveDocumentContent(documentId, content) {
    const title = document.querySelector("h1").innerText.trim();

    // Send an HTTP POST request to the backend to save the updated content
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