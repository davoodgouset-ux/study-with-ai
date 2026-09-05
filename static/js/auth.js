/**
 * static/js/auth.js
 * Authentication & Session Management Module
 */
const AuthApp = {
  getToken() {
    return localStorage.getItem(Config.TOKEN_KEY) || sessionStorage.getItem(Config.TOKEN_KEY) || null;
  },

  getUser() {
    const raw = localStorage.getItem(Config.USER_KEY) || sessionStorage.getItem(Config.USER_KEY);
    try { return raw ? JSON.parse(raw) : null; } catch { return null; }
  },

  checkSession() {
    const token = this.getToken();
    const user = this.getUser();

    if (token && user) {
      State.token = token;
      State.user = user;
      this.renderWorkspace(user);
    } else {
      this.showView('login');
    }
  },

  showView(viewName) {
    const loginView = document.getElementById('loginView');
    const registerView = document.getElementById('registerView');
    const workspaceView = document.getElementById('workspaceView');
    const guestControls = document.getElementById('navGuestControls');
    const userControls = document.getElementById('navUserControls');

    loginView.classList.add('hidden');
    registerView.classList.add('hidden');
    workspaceView.classList.add('hidden');

    this.hideAlert('loginAlert');
    this.hideAlert('registerAlert');

    if (viewName === 'login') {
      loginView.classList.remove('hidden');
      guestControls.classList.remove('hidden');
      userControls.classList.add('hidden');
    } else if (viewName === 'register') {
      registerView.classList.remove('hidden');
      guestControls.classList.remove('hidden');
      userControls.classList.add('hidden');
    } else if (viewName === 'workspace') {
      workspaceView.classList.remove('hidden');
      guestControls.classList.add('hidden');
      userControls.classList.remove('hidden');
    }
  },

  togglePassword(inputId, btnId) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    if (!input || !btn) return;

    if (input.type === 'password') {
      input.type = 'text';
      btn.innerHTML = EyeIcons.open;
    } else {
      input.type = 'password';
      btn.innerHTML = EyeIcons.closed;
    }
  },

  async handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const btnText = document.getElementById('loginBtnText');
    const btn = document.getElementById('loginBtn');

    this.hideAlert('loginAlert');
    btn.disabled = true;
    btnText.innerText = 'Signing in...';

    try {
      const res = await fetch(`${Config.API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid email or password.');

      State.token = data.access_token;
      State.user = data.user;

      localStorage.setItem(Config.TOKEN_KEY, data.access_token);
      localStorage.setItem(Config.USER_KEY, JSON.stringify(data.user));

      this.renderWorkspace(data.user);

    } catch (err) {
      this.showAlert('loginAlert', err.message, 'error');
    } finally {
      btn.disabled = false;
      btnText.innerText = 'Sign In →';
    }
  },

  async handleRegister(e) {
    e.preventDefault();

    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const btnText = document.getElementById('regBtnText');
    const btn = document.getElementById('regBtn');

    this.hideAlert('registerAlert');
    btn.disabled = true;
    btnText.innerText = 'Creating account...';

    try {
      const res = await fetch(`${Config.API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed.');

      document.getElementById('loginEmail').value = email;
      document.getElementById('loginPassword').value = '';
      this.showView('login');
      this.showAlert('loginAlert', `✓ Account created for ${data.name}! You can now sign in.`, 'success');

    } catch (err) {
      this.showAlert('registerAlert', err.message, 'error');
    } finally {
      btn.disabled = false;
      btnText.innerText = 'Create Account →';
    }
  },

  handleLogout() {
    State.token = null;
    State.user = null;
    State.documents = [];
    State.activeDocId = null;
    State.activeDoc = null;
    State.flashcardsDeck = [];

    localStorage.removeItem(Config.TOKEN_KEY);
    localStorage.removeItem(Config.USER_KEY);
    sessionStorage.removeItem(Config.TOKEN_KEY);
    sessionStorage.removeItem(Config.USER_KEY);

    this.showView('login');
    this.showAlert('loginAlert', 'You have been signed out.', 'success');
  },

  renderWorkspace(user) {
    document.getElementById('navUserName').innerText = `👤 ${user.name || 'Student'}`;
    this.showView('workspace');
    DocApp.loadDocuments();
  },

  showAlert(alertId, message, type = 'error') {
    const el = document.getElementById(alertId);
    if (!el) return;
    el.className = `alert-box alert-${type}`;
    el.innerText = message;
    el.classList.remove('hidden');
  },

  hideAlert(alertId) {
    const el = document.getElementById(alertId);
    if (el) el.classList.add('hidden');
  }
};
