/**
 * static/js/summary.js
 * 1-Page Exam Cheat Sheet Module
 */
const SummaryApp = {
  async generateSummary() {
    const outputArea = document.getElementById("summaryOutputArea");
    const btn = document.getElementById("btnRunSummary");
    AuthApp.hideAlert("docAlert");
    if (!State.activeDocId || !State.activeDoc) {
      AuthApp.showAlert("docAlert", "Please select or upload a PDF textbook first.", "error");
      return;
    }
    const token = AuthApp.getToken();
    if (!token) { AuthApp.showView("login"); return; }

    btn.disabled = true;
    btn.textContent = "Generating Summary...";

    outputArea.innerHTML = `<div class="qa-loading-box"><div class="spinner"></div><div class="loading-text">Generating 1-Page Cheat Sheet from "${State.activeDoc.filename}"...</div><div class="loading-sub">Gemini 3.6 Flash is condensing key concepts, definitions, and exam traps</div></div>`;

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/${State.activeDocId}/summary`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate summary.");
      this.renderSummaryView(data);
    } catch (err) {
      outputArea.innerHTML = `<div class="alert-box alert-error" style="margin:20px;"><strong>Summary Error:</strong> ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Generate 1-Page Summary";
    }
  },

  renderSummaryView(data) {
    const outputArea = document.getElementById("summaryOutputArea");

    const takeawaysHtml = (data.key_takeaways || []).length > 0
      ? data.key_takeaways.map(t => `<li class="summary-takeaway-item"><span class="takeaway-bullet">&#10003;</span><span>${t}</span></li>`).join("")
      : `<li class="summary-takeaway-item"><span class="takeaway-bullet">&#10003;</span><span>Key concepts from your document.</span></li>`;

    const defsHtml = (data.core_definitions || []).length > 0
      ? data.core_definitions.map(d => `
          <div class="summary-def-row">
            <div class="def-term">${d.term || "Term"}</div>
            <div class="def-body">
              <span class="def-text">${d.definition || ""}</span>
              ${d.page ? `<span class="def-page">&#128218; ${d.page}</span>` : ""}
            </div>
          </div>`).join("")
      : `<div class="summary-def-row"><div class="def-term">-</div><div class="def-body"><span class="def-text">Definitions from your document.</span></div></div>`;

    const trapsHtml = (data.common_exam_traps || []).length > 0
      ? data.common_exam_traps.map(t => `<li class="summary-trap-item"><span class="trap-icon">!</span><span>${t}</span></li>`).join("")
      : `<li class="summary-trap-item"><span class="trap-icon">!</span><span>Review distinctions between similar concepts.</span></li>`;

    const citationsHtml = (data.page_citations || []).map(c => `<span class="summary-cite-chip">&#128218; ${c}</span>`).join("");
    const modelBadge = data.model_used ? `<div class="summary-model-badge">&#129302; ${data.model_used}</div>` : "";

    outputArea.innerHTML = `
      <div class="summary-sheet">
        <div class="summary-title-bar">
          <h3 class="summary-title">${data.summary_title || "1-Page Exam Cheat Sheet"}</h3>
          ${modelBadge}
        </div>
        <div class="summary-section">
          <div class="summary-section-label">Overview</div>
          <p class="summary-overview-text">${data.overview || ""}</p>
        </div>
        <div class="summary-section">
          <div class="summary-section-label">Key Takeaways</div>
          <ul class="summary-takeaways-list">${takeawaysHtml}</ul>
        </div>
        <div class="summary-section">
          <div class="summary-section-label">Core Definitions</div>
          <div class="summary-defs-list">${defsHtml}</div>
        </div>
        <div class="summary-section">
          <div class="summary-section-label">Common Exam Traps</div>
          <ul class="summary-traps-list">${trapsHtml}</ul>
        </div>
        ${citationsHtml ? `<div class="summary-citations-row">${citationsHtml}</div>` : ""}
      </div>`;
  }
};