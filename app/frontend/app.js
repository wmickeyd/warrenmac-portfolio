// ==========================================
// Theme Switching (Dark & Light Mode)
// ==========================================
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const themeIcon = document.getElementById('theme-icon');

function getPreferredTheme() {
  const saved = localStorage.getItem('portfolio_theme');
  if (saved) return saved;
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('portfolio_theme', theme);
  if (themeIcon) {
    themeIcon.innerHTML = theme === 'light' ? '&#9728;' : '&#9790;'; // ☀️ sun or 🌙 moon
  }
}

if (themeToggleBtn) {
  themeToggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
  });
}

// Initialize theme on page load
applyTheme(getPreferredTheme());

// ==========================================
// Password Gate (Access Barrier)
// ==========================================
const passwordGate = document.getElementById('password-gate');
const gateForm = document.getElementById('gate-form');
const gateInput = document.getElementById('gate-password-input');
const gateError = document.getElementById('gate-error-msg');

async function checkPasswordGateStatus() {
  try {
    const res = await fetch('/api/auth/status');
    if (!res.ok) return;
    const data = await res.json();
    if (data.enabled) {
      const isUnlocked = sessionStorage.getItem('portfolio_auth') === 'unlocked';
      if (!isUnlocked && passwordGate) {
        passwordGate.classList.remove('hidden');
        if (gateInput) gateInput.focus();
      }
    }
  } catch (err) {
    console.error('Failed to verify gate status:', err);
  }
}

if (gateForm) {
  gateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const password = gateInput.value.trim();
    if (!password) return;

    gateError.innerText = 'Verifying access code...';
    try {
      const res = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      const data = await res.json();
      if (data.success) {
        sessionStorage.setItem('portfolio_auth', 'unlocked');
        passwordGate.classList.add('hidden');
        gateError.innerText = '';
      } else {
        gateError.innerText = data.message || 'Invalid passcode.';
        gateInput.value = '';
        gateInput.focus();
      }
    } catch (err) {
      gateError.innerText = 'Authentication error. Please retry.';
    }
  });
}

checkPasswordGateStatus();

// ==========================================
// Navigation Tab Switching
// ==========================================
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    tab.classList.add('active');
    const targetId = tab.getAttribute('data-tab');
    document.getElementById(targetId).classList.add('active');

    if (targetId === 'tab-telemetry') {
      fetchTelemetry();
    }
  });
});

// Chat Handling
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const sendBtn = document.getElementById('send-btn');

function appendMessage(sender, text, isBlocked = false) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender === 'user' ? 'message-user' : (isBlocked ? 'message-blocked' : 'message-bot')}`;

  const metaDiv = document.createElement('div');
  metaDiv.className = 'message-meta';
  metaDiv.innerText = sender === 'user' ? 'Visitor' : (isBlocked ? '🛡️ Guardrail Interception' : "Warren's AI Assistant");

  const bodyDiv = document.createElement('div');
  bodyDiv.className = 'message-body';
  // Render safe markdown-like breaks
  bodyDiv.innerHTML = text.replace(/\n/g, '<br>');

  msgDiv.appendChild(metaDiv);
  msgDiv.appendChild(bodyDiv);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage('user', message);
  chatInput.value = '';
  chatInput.disabled = true;
  sendBtn.disabled = true;
  sendBtn.innerText = 'Analyzing...';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    if (data.status === 'blocked') {
      appendMessage('bot', data.response, true);
    } else {
      appendMessage('bot', data.response, false);
    }
  } catch (err) {
    appendMessage('bot', 'Network Error: Failed to reach the backend guardrail service.', true);
  } finally {
    chatInput.disabled = false;
    sendBtn.disabled = false;
    sendBtn.innerText = 'Send';
    chatInput.focus();
    fetchTelemetry(); // Refresh stats after each interaction
  }
});

function sendSample(promptText) {
  chatInput.value = promptText;
  chatForm.dispatchEvent(new Event('submit'));
}

// Telemetry Polling
async function fetchTelemetry() {
  try {
    const res = await fetch('/api/security-stats');
    if (!res.ok) return;
    const stats = await res.json();

    document.getElementById('stat-total').innerText = stats.total_requests;
    document.getElementById('stat-success').innerText = stats.successful_queries;
    document.getElementById('stat-injections').innerText = stats.blocked_injections;
    document.getElementById('stat-canary').innerText = stats.canary_leaks_prevented;
    document.getElementById('stat-ratelimits').innerText = stats.rate_limits_triggered;

    const eventsList = document.getElementById('events-list');
    if (stats.recent_events && stats.recent_events.length > 0) {
      eventsList.innerHTML = stats.recent_events.map(ev => `
        <div class="event-item">
          <div>
            <span class="event-type">[${ev.type}]</span>
            <span style="color: var(--text-secondary); margin-left: 0.5rem;">${ev.details}</span>
          </div>
          <span class="event-time">${ev.timestamp.split('T')[1].replace('Z', '')} UTC</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to update telemetry:', err);
  }
}

document.getElementById('refresh-telemetry-btn').addEventListener('click', fetchTelemetry);

// Initial telemetry fetch
fetchTelemetry();
setInterval(fetchTelemetry, 15000);

