/**
 * static/js/quiz.js
 * Dedicated Step-by-Step Practice Quiz Module
 * Features:
 * 1. Single Question at a time with selectable A/B/C/D options and Next Question navigation.
 * 2. Ability to go back to previous questions to change options before finishing.
 * 3. Results dashboard after completing all 5 questions.
 * 4. STRICT RULE: No retake allowed for exam integrity.
 */
const QuizApp = {

  async generateQuiz() {
    const outputArea = document.getElementById('quizOutputArea');
    const btn = document.getElementById('btnRunQuiz');
    const btnText = document.getElementById('quizBtnText') || btn;

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
    if (btnText.innerText) btnText.innerText = 'Generating Quiz...';

    outputArea.innerHTML = `
      <div class="qa-loading-box">
        <div class="spinner"></div>
        <div class="loading-text">Generating Practice Quiz from "${State.activeDoc.filename}"...</div>
        <div class="loading-sub">Gemini 3.6 Flash is composing test questions strictly from your textbook</div>
      </div>
    `;

    try {
      const res = await fetch(`${Config.API_BASE_URL}/documents/${State.activeDocId}/quiz?count=5`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to generate practice quiz.');

      State.quizQuestions = data.questions || [];
      State.currentQuizIdx = 0;
      State.userAnswers = {};
      State.quizSubmitted = false;

      if (State.quizQuestions.length === 0) {
        outputArea.innerHTML = `<p class="placeholder-text">No practice questions could be generated from this document.</p>`;
        return;
      }

      this.renderQuizView();

    } catch (err) {
      outputArea.innerHTML = `
        <div class="alert-box alert-error" style="margin:20px;">
          <strong>Quiz Generation Error:</strong> ${err.message}
        </div>
      `;
    } finally {
      btn.disabled = false;
      if (btnText.innerText) btnText.innerText = 'Generate Practice Quiz';
    }
  },

  renderQuizView() {
    const outputArea = document.getElementById('quizOutputArea');
    const questions = State.quizQuestions;

    if (!questions || questions.length === 0) return;

    // If quiz is completed, show comprehensive results breakdown
    if (State.quizSubmitted) {
      this.renderResultsView(outputArea, questions);
      return;
    }

    // Otherwise, show the active question step-by-step
    this.renderActiveQuestionStep(outputArea, questions);
  },

  // ---------------------------------------------------------------------------
  // 1. STEP-BY-STEP QUESTION VIEW (ONE QUESTION AT A TIME)
  // ---------------------------------------------------------------------------
  renderActiveQuestionStep(outputArea, questions) {
    const total = questions.length;
    const idx = State.currentQuizIdx;
    const q = questions[idx];
    const selectedOpt = State.userAnswers[q.id];

    // Build Question Navigator Steps
    const stepsHtml = questions.map((item, i) => {
      const isAnswered = State.userAnswers[item.id] !== undefined;
      const isCurrent = i === idx;
      let stepClass = 'quiz-step-dot';
      if (isCurrent) stepClass += ' current';
      else if (isAnswered) stepClass += ' answered';

      return `
        <button type="button" class="${stepClass}" onclick="QuizApp.goToQuestion(${i})" title="Go to Question ${i + 1}">
          Q${i + 1}
        </button>
      `;
    }).join('');

    // Build 4 selectable options
    const optionsHtml = q.options.map((optText, optIdx) => {
      const optionLetter = String.fromCharCode(65 + optIdx); // A, B, C, D
      const isSelected = selectedOpt === optIdx;

      return `
        <label class="quiz-option-item ${isSelected ? 'option-selected' : ''}" onclick="QuizApp.selectOption(${q.id}, ${optIdx})">
          <input 
            type="radio" 
            name="quiz_step_q" 
            value="${optIdx}" 
            ${isSelected ? 'checked' : ''} 
            class="quiz-radio-input"
          >
          <span class="option-letter">${optionLetter}</span>
          <span class="option-text">${optText}</span>
        </label>
      `;
    }).join('');

    // Next / Finish button label
    const isLastQuestion = idx === total - 1;
    const nextBtnHtml = isLastQuestion
      ? `<button type="button" class="btn-action btn-finish-quiz" onclick="QuizApp.submitQuiz()">
           Finish & View Results &rarr;
         </button>`
      : `<button type="button" class="btn-nav-card" onclick="QuizApp.nextQuestion()">
           Next Question &rarr;
         </button>`;

    outputArea.innerHTML = `
      <div class="quiz-step-container">
        
        <!-- Header & Step Navigation -->
        <div class="quiz-step-header">
          <div class="q-progress-badge">
            📝 Question ${idx + 1} of ${total}
          </div>
          <div class="quiz-steps-row">
            ${stepsHtml}
          </div>
        </div>

        <!-- Question Card -->
        <div class="quiz-card-item">
          <div class="quiz-card-header">
            <span class="q-num-badge">Question ${idx + 1}</span>
            <span class="q-page-tag">📖 ${q.page_citation || 'Textbook Page'}</span>
          </div>
          <div class="quiz-question-text">${q.question}</div>
          <div class="quiz-options-list">
            ${optionsHtml}
          </div>
        </div>

        <!-- Navigation Controls -->
        <div class="quiz-step-nav-bar">
          <button type="button" class="btn-secondary" onclick="QuizApp.prevQuestion()" ${idx === 0 ? 'disabled' : ''}>
            &larr; Previous Question
          </button>
          ${nextBtnHtml}
        </div>

      </div>
    `;
  },

  selectOption(questionId, optIdx) {
    if (State.quizSubmitted) return;
    State.userAnswers[questionId] = optIdx;
    this.renderQuizView();
  },

  nextQuestion() {
    if (State.currentQuizIdx < State.quizQuestions.length - 1) {
      State.currentQuizIdx++;
      this.renderQuizView();
    }
  },

  prevQuestion() {
    if (State.currentQuizIdx > 0) {
      State.currentQuizIdx--;
      this.renderQuizView();
    }
  },

  goToQuestion(idx) {
    if (idx >= 0 && idx < State.quizQuestions.length) {
      State.currentQuizIdx = idx;
      this.renderQuizView();
    }
  },

  submitQuiz() {
    const total = State.quizQuestions.length;
    const answeredCount = Object.keys(State.userAnswers).length;

    if (answeredCount < total) {
      const unanswered = total - answeredCount;
      const confirmSubmit = window.confirm(`You have ${unanswered} unanswered question(s).

Do you want to submit and view your results? (Note: Quizzes cannot be retaken once submitted)`);
      if (!confirmSubmit) return;
    }

    State.quizSubmitted = true;
    this.renderQuizView();
  },

  // ---------------------------------------------------------------------------
  // 2. FINAL RESULTS DASHBOARD (NO RETAKE ALLOWED)
  // ---------------------------------------------------------------------------
  renderResultsView(outputArea, questions) {
    let correctCount = 0;
    questions.forEach(q => {
      if (State.userAnswers[q.id] === q.correct_option_index) {
        correctCount++;
      }
    });

    const pct = Math.round((correctCount / questions.length) * 100);
    let badge = '📚 Keep reviewing the textbook material!';
    if (pct === 100) badge = '🏆 Perfect Score! Outstanding mastery!';
    else if (pct >= 80) badge = '🎉 Great Job! Solid understanding!';
    else if (pct >= 60) badge = '👍 Good Effort! Review the missed questions below.';

    const breakdownHtml = questions.map((q, qIdx) => {
      const selectedOpt = State.userAnswers[q.id];
      const isCorrect = selectedOpt === q.correct_option_index;

      const optionsHtml = q.options.map((optText, optIdx) => {
        const optionLetter = String.fromCharCode(65 + optIdx);
        const isSelected = selectedOpt === optIdx;

        let rowClass = 'quiz-option-item';
        let statusBadge = '';

        if (optIdx === q.correct_option_index) {
          rowClass += ' option-correct';
          statusBadge = '<span class="option-status-badge correct">✓ Correct Answer</span>';
        } else if (isSelected) {
          rowClass += ' option-wrong';
          statusBadge = '<span class="option-status-badge wrong">✗ Your Selection</span>';
        }

        return `
          <div class="${rowClass}">
            <span class="option-letter">${optionLetter}</span>
            <span class="option-text">${optText}</span>
            ${statusBadge}
          </div>
        `;
      }).join('');

      return `
        <div class="quiz-card-item">
          <div class="quiz-card-header">
            <span class="q-num-badge">Question ${qIdx + 1}</span>
            <span class="option-status-badge ${isCorrect ? 'correct' : 'wrong'}">
              ${isCorrect ? '✓ Correct (+1)' : '✗ Incorrect (0)'}
            </span>
          </div>
          <div class="quiz-question-text">${q.question}</div>
          <div class="quiz-options-list">
            ${optionsHtml}
          </div>
          <div class="quiz-explanation-box">
            <div class="exp-title">💡 Explanation:</div>
            <div class="exp-text">${q.explanation}</div>
            <div class="exp-citation">📖 ${q.page_citation || 'Textbook Page'}</div>
          </div>
        </div>
      `;
    }).join('');

    outputArea.innerHTML = `
      <div class="quiz-results-container">
        
        <!-- Score Banner -->
        <div class="quiz-score-banner">
          <div class="score-main">Final Result: ${correctCount} / ${questions.length} Correct (${pct}%)</div>
          <div class="score-badge">${badge}</div>
        </div>

        <!-- Questions Review Breakdown -->
        <div class="quiz-questions-deck">
          ${breakdownHtml}
        </div>

        <!-- Action Bar: Strictly New Quiz Only (No Retake Allowed) -->
        <div class="quiz-actions-bar" style="justify-content: flex-end;">
          <button type="button" class="btn-action" onclick="QuizApp.generateQuiz()">
            📝 Generate New Quiz from Textbook &rarr;
          </button>
        </div>

      </div>
    `;
  }
};
