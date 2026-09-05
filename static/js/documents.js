/**
 * static/js/documents.js
 * Document Management Module (Upload, Select, View, Delete)
 */
const DocApp = {
  async uploadDocument() {
    const fileInput = document.getElementById('pdfFileInput');
    const uploadBtn = document.getElementById('btnUploadPdf');
    const btnText = document.getElementById('uploadBtnText');

    AuthApp.hideAlert('docAlert');

    if (!fileInput.files || fileInput.files.length === 0) {
      AuthApp.showAlert('docAlert', 'Please select a PDF file first.', 'error');
      return;
    }

    const file = fileInput.files[0];

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      AuthApp.showAlert('docAlert', 'Only PDF documents (.pdf) are supported.', 'error');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      AuthApp.showAlert('docAlert', 'File exceeds the maximum 25MB limit.', 'error');
      return;
    }

    const token = AuthApp.getToken();
    if (!token) {
      AuthApp.showAlert('docAlert', 'Session expired. Please sign in again.', 'error');
      AuthApp.showView('login');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    uploadBtn.disabled = true;
    btnText.innerText = 'Extracting & Indexing...';

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to upload PDF.');

      fileInput.value = '';
      AuthApp.showAlert('docAlert', `✓ "${data.document.filename}" uploaded successfully! Extracted ${data.total_chunks} chunks.`, 'success');

      await this.loadDocuments(data.document.id);

    } catch (err) {
      AuthApp.showAlert('docAlert', err.message, 'error');
    } finally {
      uploadBtn.disabled = false;
      btnText.innerText = '⬆️ Upload Document';
    }
  },

  async loadDocuments(selectDocId = null) {
    const select = document.getElementById('documentSelect');
    const token = AuthApp.getToken();
    if (!token) return;

    select.innerHTML = '<option value="">Loading documents...</option>';

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Failed to fetch document library.');

      const docs = await res.json();
      State.documents = docs || [];

      select.innerHTML = '';

      if (State.documents.length === 0) {
        select.innerHTML = '<option value="">No documents uploaded yet</option>';
        State.activeDocId = null;
        State.activeDoc = null;
        this.renderActiveDocDetails();
        return;
      }

      State.documents.forEach(doc => {
        const opt = document.createElement('option');
        opt.value = doc.id;
        opt.innerText = `${doc.filename} (Doc #${doc.id} - ${doc.page_count} pgs)`;
        select.appendChild(opt);
      });

      let targetId = selectDocId || State.activeDocId || State.documents[0].id;
      const targetDoc = State.documents.find(d => d.id == targetId) || State.documents[0];

      State.activeDocId = targetDoc.id;
      State.activeDoc = targetDoc;
      select.value = targetDoc.id;

      this.renderActiveDocDetails();

    } catch (err) {
      select.innerHTML = '<option value="">Error loading documents</option>';
      AuthApp.showAlert('docAlert', err.message, 'error');
    }
  },

  handleDocumentSelect(e) {
    const docId = parseInt(e.target.value);
    if (!docId) return;

    const doc = State.documents.find(d => d.id === docId);
    if (doc) {
      State.activeDocId = doc.id;
      State.activeDoc = doc;
      State.flashcardsDeck = []; // reset cached deck for new doc
      this.renderActiveDocDetails();
      AuthApp.showAlert('docAlert', `Selected active textbook: "${doc.filename}"`, 'success');
    }
  },

  renderActiveDocDetails() {
    const nameEl = document.getElementById('activeDocName');
    const metaEl = document.getElementById('activeDocMeta');
    const viewBtn = document.getElementById('btnViewPdf');
    const deleteBtn = document.getElementById('btnDeletePdf');

    if (State.activeDoc) {
      nameEl.innerText = State.activeDoc.filename;
      const sizeMb = (State.activeDoc.file_size / (1024 * 1024)).toFixed(2);
      metaEl.innerText = `Doc ID: #${State.activeDoc.id} • ${State.activeDoc.page_count} Pages • ${sizeMb} MB • FAISS Indexed`;
      viewBtn.disabled = false;
      deleteBtn.disabled = false;
    } else {
      nameEl.innerText = 'No document selected';
      metaEl.innerText = 'Upload a PDF to start studying.';
      viewBtn.disabled = true;
      deleteBtn.disabled = true;
    }
  },

  viewDocument() {
    if (!State.activeDocId) {
      AuthApp.showAlert('docAlert', 'Please select an active document first.', 'error');
      return;
    }
    const token = AuthApp.getToken();
    const url = `${Config.API_BASE_URL}/documents/${State.activeDocId}/view${token ? '?token=' + token : ''}`;
    window.open(url, '_blank');
  },

  async deleteDocument() {
    if (!State.activeDocId || !State.activeDoc) {
      AuthApp.showAlert('docAlert', 'Please select a document to delete.', 'error');
      return;
    }

    const docName = State.activeDoc.filename;
    const confirmDelete = window.confirm(`Are you sure you want to delete "${docName}"?

This will permanently delete the PDF, its extracted chunks, and its FAISS vector index.`);
    if (!confirmDelete) return;

    const token = AuthApp.getToken();
    AuthApp.hideAlert('docAlert');

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/${State.activeDocId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to delete document.');

      AuthApp.showAlert('docAlert', `✓ "${docName}" and its vector index deleted successfully.`, 'success');
      State.activeDocId = null;
      State.activeDoc = null;
      State.flashcardsDeck = [];

      await this.loadDocuments();

    } catch (err) {
      AuthApp.showAlert('docAlert', err.message, 'error');
    }
  }
};
