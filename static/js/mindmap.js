/**
 * static/js/mindmap.js
 * Dedicated Visual Concept Mind Map Module (Mermaid.js Flowchart Generator)
 */
const MindmapApp = {

  initMermaid() {
    if (window.mermaid) {
      try {
        mermaid.initialize({
          startOnLoad: false,
          theme: "neutral",
          securityLevel: "loose",
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: "basis"
          }
        });
      } catch (e) {
        console.warn("[Mindmap] Mermaid init error:", e);
      }
    }
  },

  async generateMindmap() {
    const outputArea = document.getElementById("mindmapOutputArea");
    const btn = document.getElementById("btnRunMindmap");

    AuthApp.hideAlert("docAlert");

    if (!State.activeDocId || !State.activeDoc) {
      AuthApp.showAlert("docAlert", "Please select or upload a PDF textbook first.", "error");
      return;
    }

    const token = AuthApp.getToken();
    if (!token) {
      AuthApp.showAlert("docAlert", "Session expired. Please sign in again.", "error");
      AuthApp.showView("login");
      return;
    }

    btn.disabled = true;
    btn.textContent = "Generating Mind Map...";

    outputArea.innerHTML = `
      <div class="qa-loading-box">
        <div class="spinner"></div>
        <div class="loading-text">Generating Visual Concept Mind Map from "${State.activeDoc.filename}"...</div>
        <div class="loading-sub">Gemini 3.6 Flash is mapping relationships, topics, and concept hierarchies</div>
      </div>
    `;

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/${State.activeDocId}/mindmap`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate mind map.");

      await this.renderMindmapView(data);

    } catch (err) {
      outputArea.innerHTML = `
        <div class="alert-box alert-error" style="margin:20px;">
          <strong>Mind Map Error:</strong> ${err.message}
        </div>
      `;
    } finally {
      btn.disabled = false;
      btn.textContent = "Generate Mind Map";
    }
  },

  async renderMindmapView(data) {
    const outputArea = document.getElementById("mindmapOutputArea");
    this.initMermaid();

    const rootTitle = data.root_concept || State.activeDoc.filename.replace(".pdf", "");
    const modelBadge = data.model_used ? `<div class="summary-model-badge">&#129302; ${data.model_used}</div>` : "";

    // Build structured topic outline cards
    const nodesHtml = (data.nodes || []).map((n, i) => {
      const subsHtml = (n.subtopics || []).map(s => `<span class="mindmap-sub-pill">${s}</span>`).join("");
      return `
        <div class="mindmap-topic-card">
          <div class="mindmap-topic-title">
            <span class="topic-index-badge">Branch ${i + 1}</span>
            <span class="topic-name">${n.topic || "Core Topic"}</span>
          </div>
          <div class="mindmap-subtopics-wrap">
            ${subsHtml || '<span class="mindmap-sub-pill">Overview</span>'}
          </div>
        </div>
      `;
    }).join("");

    outputArea.innerHTML = `
      <div class="mindmap-sheet">
        <div class="mindmap-title-bar">
          <div class="mindmap-title-wrap">
            <span class="mindmap-icon">&#128376;</span>
            <h3 class="mindmap-title">${rootTitle}</h3>
          </div>
          ${modelBadge}
        </div>

        <!-- Flowchart Visual Canvas -->
        <div class="mindmap-canvas-card">
          <div class="canvas-header">
            <span class="canvas-label">Interactive Concept Flowchart</span>
            <span class="canvas-sub">Top-Down Concept Hierarchy</span>
          </div>
          <div id="mermaidRenderContainer" class="mermaid-diagram-wrap">
            <div class="spinner"></div>
          </div>
        </div>

        <!-- Structured Concept Outline -->
        <div class="mindmap-outline-section">
          <div class="summary-section-label">Concept Outline Breakdown</div>
          <div class="mindmap-topics-grid">
            ${nodesHtml}
          </div>
        </div>
      </div>
    `;

    // Render Mermaid SVG
    const container = document.getElementById("mermaidRenderContainer");
    if (!container) return;

    if (window.mermaid && data.mermaid_code) {
      try {
        const uniqueId = `mermaid_graph_${Date.now()}`;
        const { svg } = await mermaid.render(uniqueId, data.mermaid_code);
        container.innerHTML = svg;
      } catch (renderErr) {
        console.warn("[Mindmap] Mermaid rendering fallback:", renderErr);
        container.innerHTML = `
          <div class="mermaid-fallback-box">
            <p><strong>Hierarchical Diagram Code:</strong></p>
            <pre class="mermaid-code-pre">${data.mermaid_code}</pre>
          </div>
        `;
      }
    } else {
      container.innerHTML = `
        <div class="mermaid-fallback-box">
          <pre class="mermaid-code-pre">${data.mermaid_code || "graph TD\n  Root[Study Material]"}</pre>
        </div>
      `;
    }
  }
};