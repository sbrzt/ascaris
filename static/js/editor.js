import { TabsModule } from './tabsModule.js';
import { createPanelBlock } from './panelBlockModule.js';
import { EntityMarkingModule } from './entityMarkingModule.js'
import { SaveDocumentModule } from './saveDocumentModule.js';
import { InterfaceModule } from './interfaceModule.js'
import { DownloadModule } from './downloadModule.js'

const documentId = document.querySelector('#editableContent').getAttribute('data-documentId');

document.addEventListener("DOMContentLoaded", function () {
  TabsModule.initializeTabs();

  SaveDocumentModule.startAutoSave(documentId);

});
