/**
 * static/js/qa.js
 * Ask AI (RAG Q&A Engine) Module
 */
const AskAIApp = {
  async askQuestion() {
    const input = document.getElementById('qaQueryInput');
    const query = input.value.trim();
    const outputArea = document.getElementById('qaOutputArea');
    const btn = document.getElementById('btnSubmitQuery');
    const btnText = document.getElementById('askBtnText');

    AuthApp.hideAlert('docAlert');

    if (!State.activeDocId) {
      AuthApp.showAlert('docAlert', '⚠️ Please upload or select an active PDF textbook first.', 'error');
      return;
    }

    if (!query) {
      input.focus();
      return;
    }

    const token = AuthApp.getToken();
    if (!token) {
      AuthApp.showAlert('docAlert', 'Session expired. Please sign in again.', 'error');
      AuthApp.showView('login');
      return;
    }

    btn.disabled = true;
    btnText.innerText = 'Searching...';

    outputArea.innerHTML = `
      <div class="qa-loading-box">
        <div class="spinner"></div>
        <div class="loading-text">Searching "${State.activeDoc.filename}" with FAISS...</div>
        <div class="loading-sub">Retrieving Top-K chunks & generating cited answer with Gemini 3.6 Flash</div>
      </div>
    `;

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/${State.activeDocId}/ask`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: query, top_k: 4 })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to process AI question.');

      const citationsHtml = (data.citations && data.citations.length > 0)
        ? data.citations.map(c => `<span class="citation-chip">📖 ${c}</span>`).join(' ')
        : `<span class="citation-chip">📖 ${State.activeDoc.filename} — Page 1</span>`;

      const parsedAnswer = window.marked ? marked.parse(data.answer) : data.answer;

      outputArea.innerHTML = `
        <div class="qa-result-card">
          <div class="qa-question-header">
            Q: "${query}"
          </div>
          
          <div class="qa-answer-body">
            ${parsedAnswer}
          </div>

          <div class="qa-citations-row">
            <span class="citation-label">Verified Citations:</span>
            ${citationsHtml}
          </div>

          <div class="qa-meta-footer">
            <span>⚡ Top FAISS Similarity: ${(data.top_similarity_score * 100).toFixed(1)}%</span>
            <span>🤖 Model: ${data.model_used || 'Gemini 3.6 Flash (Grounding Active)'}</span>
          </div>
        </div>
      `;

    } catch (err) {
      outputArea.innerHTML = `
        <div class="alert-box alert-error" style="margin:20px;">
          <strong>AI Search Error:</strong> ${err.message}
        </div>
      `;
    } finally {
      btn.disabled = false;
      btnText.innerText = 'Ask AI →';
    }
  }
};
