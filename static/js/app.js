/**
 * static/js/app.js
 * Root Application Bootstrapper & Tool Tab Router
 */
const App = {
  init() {
    AuthApp.checkSession();
  },

  showView(viewName) {
    AuthApp.showView(viewName);
  },

  togglePassword(inputId, btnId) {
    AuthApp.togglePassword(inputId, btnId);
  },

  handleLogin(e) {
    AuthApp.handleLogin(e);
  },

  handleRegister(e) {
    AuthApp.handleRegister(e);
  },

  handleLogout() {
    AuthApp.handleLogout();
  },

  switchTool(toolKey) {
    const tools = ['ask', 'flashcards', 'quiz', 'summary', 'mindmap'];
    tools.forEach(t => {
      const tabBtn = document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}Btn`);
      const panel = document.getElementById(`panel${t.charAt(0).toUpperCase() + t.slice(1)}`);
      if (tabBtn) tabBtn.classList.remove('active');
      if (panel) panel.classList.add('hidden');
    });

    const activeBtn = document.getElementById(`tab${toolKey.charAt(0).toUpperCase() + toolKey.slice(1)}Btn`);
    const activePanel = document.getElementById(`panel${toolKey.charAt(0).toUpperCase() + toolKey.slice(1)}`);
    if (activeBtn) activeBtn.classList.add('active');
    if (activePanel) activePanel.classList.remove('hidden');
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();
});
