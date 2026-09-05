/**
 * static/js/flashcards.js
 * Dedicated Flashcards Module (Active-Recall Generation, Interactive Flip Deck, Study Controls)
 */
const FlashcardsApp = {

  async generateFlashcards() {
    const outputArea = document.getElementById('flashcardsOutputArea');
    const btn = document.getElementById('btnRunFlashcards');
    const btnText = document.getElementById('flashcardsBtnText') || btn;

    AuthApp.hideAlert('docAlert');

    if (!State.activeDocId || !State.activeDoc) {
      AuthApp.showAlert('docAlert', '⚠️ Please select or upload a PDF textbook first.', 'error');
      return;
    }

    const token = AuthApp.getToken();
    if (!token) {
      AuthApp.showAlert('docAlert', 'Session expired. Please sign in again.', 'error');
      AuthApp.showView('login');
      return;
    }

    btn.disabled = true;
    if (btnText.innerText) btnText.innerText = 'Generating Cards...';

    outputArea.innerHTML = `
      <div class="qa-loading-box">
        <div class="spinner"></div>
        <div class="loading-text">Generating Active-Recall Flashcards from "${State.activeDoc.filename}"...</div>
        <div class="loading-sub">Gemini 3.6 Flash is extracting key concepts and generating study questions</div>
      </div>
    `;

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/${State.activeDocId}/flashcards?count=5`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to generate flashcards.');

      State.flashcardsDeck = data.flashcards || [];
      State.currentCardIdx = 0;

      if (State.flashcardsDeck.length === 0) {
        outputArea.innerHTML = `<p class="placeholder-text">No flashcards could be generated from this document.</p>`;
        return;
      }

      this.renderDeckView();

    } catch (err) {
      outputArea.innerHTML = `
        <div class="alert-box alert-error" style="margin:20px;">
          <strong>Flashcards Generation Error:</strong> ${err.message}
        </div>
      `;
    } finally {
      btn.disabled = false;
      if (btnText.innerText) btnText.innerText = 'Generate 5 Flashcards';
    }
  },

  renderDeckView() {
    const outputArea = document.getElementById('flashcardsOutputArea');
    const deck = State.flashcardsDeck;
    const idx = State.currentCardIdx;
    const card = deck[idx];

    if (!card) return;

    outputArea.innerHTML = `
      <div class="flashcards-container">
        
        <!-- Header & Controls Row -->
        <div class="deck-header-row">
          <div class="deck-progress-badge">
            🗂️ Card ${idx + 1} of ${deck.length}
          </div>
          <div class="deck-view-toggles">
            <button type="button" class="btn-toggle-view ${State.cardViewMode === 'deck' ? 'active' : ''}" onclick="FlashcardsApp.setViewMode('deck')">Single Card</button>
            <button type="button" class="btn-toggle-view ${State.cardViewMode === 'grid' ? 'active' : ''}" onclick="FlashcardsApp.setViewMode('grid')">All Cards Grid</button>
          </div>
        </div>

        ${State.cardViewMode === 'deck' ? this.getSingleCardHtml(card, idx, deck.length) : this.getGridCardsHtml(deck)}

      </div>
    `;
  },

  getSingleCardHtml(card, idx, total) {
    return `
      <!-- 3D Interactive Flip Card -->
      <div class="flip-card-wrapper" onclick="FlashcardsApp.flipActiveCard(this)">
        <div class="flip-card-inner" id="activeFlipCard">
          
          <!-- Front Side: Question -->
          <div class="flip-card-front">
            <div class="card-side-tag">QUESTION</div>
            <div class="card-content-text">${card.front_question}</div>
            <div class="card-flip-prompt">💡 Click to reveal answer &rarr;</div>
          </div>

          <!-- Back Side: Answer -->
          <div class="flip-card-back">
            <div class="card-side-tag">ANSWER & CITATION</div>
            <div class="card-content-text">${card.back_answer}</div>
            <div class="card-citation-badge">📖 ${card.page_citation || 'Textbook Page'}</div>
            <div class="card-flip-prompt">↩ Click to flip back</div>
          </div>

        </div>
      </div>

      <!-- Navigation & Study Controls -->
      <div class="deck-nav-controls">
        <button type="button" class="btn-nav-card" onclick="FlashcardsApp.prevCard()" ${idx === 0 ? 'disabled' : ''}>
          &larr; Previous
        </button>
        <button type="button" class="btn-secondary" onclick="FlashcardsApp.shuffleDeck()">
          🔄 Shuffle
        </button>
        <button type="button" class="btn-nav-card" onclick="FlashcardsApp.nextCard()" ${idx === total - 1 ? 'disabled' : ''}>
          Next &rarr;
        </button>
      </div>
    `;
  },

  getGridCardsHtml(deck) {
    const cardsHtml = deck.map((c, i) => `
      <div class="grid-card-item" onclick="FlashcardsApp.selectCardFromGrid(${i})">
        <div class="grid-card-num">Card #${i + 1}</div>
        <div class="grid-card-q"><strong>Q:</strong> ${c.front_question}</div>
        <div class="grid-card-a"><strong>A:</strong> ${c.back_answer}</div>
        <div class="grid-card-meta">📖 ${c.page_citation}</div>
      </div>
    `).join('');

    return `
      <div class="flashcards-grid">
        ${cardsHtml}
      </div>
    `;
  },

  flipActiveCard(wrapperEl) {
    const inner = wrapperEl.querySelector('.flip-card-inner');
    if (inner) inner.classList.toggle('flipped');
  },

  nextCard() {
    if (State.currentCardIdx < State.flashcardsDeck.length - 1) {
      State.currentCardIdx++;
      this.renderDeckView();
    }
  },

  prevCard() {
    if (State.currentCardIdx > 0) {
      State.currentCardIdx--;
      this.renderDeckView();
    }
  },

  shuffleDeck() {
    for (let i = State.flashcardsDeck.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [State.flashcardsDeck[i], State.flashcardsDeck[j]] = [State.flashcardsDeck[j], State.flashcardsDeck[i]];
    }
    State.currentCardIdx = 0;
    this.renderDeckView();
  },

  setViewMode(mode) {
    State.cardViewMode = mode;
    this.renderDeckView();
  },

  selectCardFromGrid(idx) {
    State.currentCardIdx = idx;
    State.cardViewMode = 'deck';
    this.renderDeckView();
  }
};
