/**
 * static/js/config.js
 * Central Configuration & Shared State Store
 */
const Config = {
  API_BASE_URL: window.VITE_API_URL || window.API_BASE_URL || '',
  TOKEN_KEY: 'study_with_ai_jwt',
  USER_KEY: 'study_with_ai_user'
};

const State = {
  user: null,
  token: null,
  documents: [],
  activeDocId: null,
  activeDoc: null,
  flashcardsDeck: [],
  currentCardIdx: 0,
  cardViewMode: 'deck', // 'deck' or 'grid'
  quizQuestions: [],
  currentQuizIdx: 0,
  userAnswers: {},
  quizSubmitted: false
};

const EyeIcons = {
  open: `<svg class="eye-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>`,
  closed: `<svg class="eye-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" /></svg>`
};
