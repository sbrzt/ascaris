const TabsModule = (function () {
  
    function openTab(event, tabName) {
      var i, tabcontent, tablinks;
      tablinks = document.getElementsByClassName("tab");
      tabcontent = document.getElementsByClassName("panel-content");
      for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
      }
      for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("is-active");
      }
      document.querySelector("." + tabName + "-content").style.display = "block";
      event.currentTarget.classList.add("is-active");
    }
  
    function initializeTabs() {
      var tablinks = document.querySelectorAll(".tab");
      tablinks.forEach(function (tablink) {
        tablink.addEventListener("click", function (event) {
          openTab(event, tablink.dataset.name);
        });
      });
    }

    const editorPanel = document.querySelector(".editor-panel");
    const metadataPanel = document.querySelector(".metadata-panel");
    const facsimilePanel = document.querySelector(".facsimile-panel");

    const tabs = document.querySelectorAll(".editor-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", function() {
            if (tab.classList.contains("is-active")) return;

            tabs.forEach(t => t.classList.remove("is-active"));
            tab.classList.add("is-active");

            if (tab.classList.contains("text-tab")) {
              editorPanel.style.display = "block";
              metadataPanel.style.display = "none";
              facsimilePanel.style.display = "none";
            } else if (tab.classList.contains("metadata-tab")) {
              editorPanel.style.display = "none";
              metadataPanel.style.display = "block";
              facsimilePanel.style.display = "none";
            } else if (tab.classList.contains("facsimile-tab")) {
              editorPanel.style.display = "none";
              metadataPanel.style.display = "none";
              facsimilePanel.style.display = "block";
            }
        });
    });

    const content = document.getElementById('editableContent');

    content.addEventListener('paste', function (event) {
      event.preventDefault();
    
      const plainText = (event.clipboardData || window.clipboardData).getData('text/plain');
    
      const plainTextNode = document.createTextNode(plainText);
    
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(plainTextNode);
      }
    });

    function createParagraph() {
      const newParagraph = document.createElement('br');
      return newParagraph;
    }

    editableContent.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();

        const selection = window.getSelection();
        const range = selection.getRangeAt(0);

        const newParagraph = createParagraph();

        range.insertNode(newParagraph);
        range.setStartBefore(newParagraph);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    });

    return {
      openTab,
      initializeTabs,
    };

  })();

  export { TabsModule };