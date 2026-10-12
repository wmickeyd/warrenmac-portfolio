
// ==========================================
// Theme Switching (Dark & Light Mode)
// ==========================================
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const themeIcon = document.getElementById('theme-icon');

const SUN_ICON = '<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path stroke-linecap="round" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41"/></svg>';
const MOON_ICON = '<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>';

function getPreferredTheme() {
  const saved = localStorage.getItem('portfolio_theme');
  if (saved) return saved;
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('portfolio_theme', theme);
  if (themeIcon) {
    themeIcon.innerHTML = theme === 'light' ? SUN_ICON : MOON_ICON;
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
// Navigation: solid-on-scroll, mobile menu, scroll-spy
// ==========================================
const siteNav = document.getElementById('site-nav');
const mobileMenu = document.getElementById('mobile-menu');
const mobileMenuBtn = document.getElementById('mobile-menu-btn');

function updateNavState() {
  const menuOpen = mobileMenu && !mobileMenu.classList.contains('hidden');
  siteNav.classList.toggle('nav-solid', window.scrollY > 10 || menuOpen);
}

window.addEventListener('scroll', updateNavState, { passive: true });
updateNavState();

function setMobileMenu(open) {
  mobileMenu.classList.toggle('hidden', !open);
  mobileMenuBtn.setAttribute('aria-expanded', String(open));
  updateNavState();
}

if (mobileMenuBtn && mobileMenu) {
  mobileMenuBtn.addEventListener('click', () => {
    setMobileMenu(mobileMenu.classList.contains('hidden'));
  });
  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => setMobileMenu(false));
  });
}

const spyLinks = document.querySelectorAll('a[data-spy]');
if ('IntersectionObserver' in window && spyLinks.length) {
  const linkFor = id => document.querySelector(`a[data-spy][href="#${id}"]`);
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      spyLinks.forEach(l => l.classList.remove('active'));
      const link = linkFor(entry.target.id);
      if (link) link.classList.add('active');
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  spyLinks.forEach(l => {
    const section = document.querySelector(l.getAttribute('href'));
    if (section) observer.observe(section);
  });
}

// ==========================================
// Image fallbacks (until real photos are added to images/)
// ==========================================
function handleMissingImage(img) {
  if (img.dataset.placeholder && img.getAttribute('src') !== img.dataset.placeholder) {
    img.src = img.dataset.placeholder;
  } else if (img.dataset.fallbackText) {
    const label = document.createElement('span');
    label.className = 'font-semibold tracking-tight text-slate-400 dark:text-slate-500';
    label.textContent = img.dataset.fallbackText;
    img.replaceWith(label);
  }
}

document.querySelectorAll('img[data-placeholder], img[data-fallback-text]').forEach(img => {
  // Lazy images may already have failed before this script ran
  if (img.complete && img.naturalWidth === 0) {
    handleMissingImage(img);
  }
  img.addEventListener('error', () => handleMissingImage(img));
});

const footerYear = document.getElementById('footer-year');
if (footerYear) footerYear.textContent = new Date().getFullYear();

// ==========================================
// Chat Handling
// ==========================================
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const sendBtn = document.getElementById('send-btn');

function appendMessage(sender, text, isBlocked = false) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender === 'user' ? 'message-user' : (isBlocked ? 'message-blocked' : 'message-bot')}`;

  const metaDiv = document.createElement('div');
  metaDiv.className = 'message-meta';
  metaDiv.textContent = sender === 'user' ? 'Visitor' : (isBlocked ? '🛡️ Guardrail Interception' : "Warren's AI Assistant");

  // textContent (not innerHTML) so model output and echoed prompts can't inject markup;
  // line breaks are preserved by white-space: pre-wrap on .message-body
  const bodyDiv = document.createElement('div');
  bodyDiv.className = 'message-body';
  bodyDiv.textContent = text;

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
  chatForm.requestSubmit();
}

document.querySelectorAll('[data-prompt]').forEach(btn => {
  btn.addEventListener('click', () => sendSample(btn.dataset.prompt));
});

// ==========================================
// Telemetry Polling
// ==========================================
function renderEvent(ev) {
  const item = document.createElement('div');
  item.className = 'flex items-start justify-between gap-4 rounded-lg border-l-4 border-red-500 bg-red-50/60 px-4 py-2.5 font-mono text-xs dark:bg-red-500/5';

  const left = document.createElement('div');
  left.className = 'min-w-0 break-words';
  const type = document.createElement('span');
  type.className = 'font-semibold text-red-600 dark:text-red-400';
  type.textContent = `[${ev.type}]`;
  const details = document.createElement('span');
  details.className = 'ml-2 text-slate-600 dark:text-slate-300';
  details.textContent = ev.details;
  left.append(type, details);

  const time = document.createElement('span');
  time.className = 'shrink-0 text-slate-400';
  const ts = String(ev.timestamp || '');
  time.textContent = ts.includes('T') ? `${ts.split('T')[1].replace('Z', '')} UTC` : ts;

  item.append(left, time);
  return item;
}

async function fetchTelemetry() {
  try {
    const res = await fetch('/api/security-stats');
    if (!res.ok) return;
    const stats = await res.json();

    document.getElementById('stat-total').textContent = stats.total_requests;
    document.getElementById('stat-success').textContent = stats.successful_queries;
    document.getElementById('stat-injections').textContent = stats.blocked_injections;
    document.getElementById('stat-canary').textContent = stats.canary_leaks_prevented;
    document.getElementById('stat-ratelimits').textContent = stats.rate_limits_triggered;

    const eventsList = document.getElementById('events-list');
    if (stats.recent_events && stats.recent_events.length > 0) {
      eventsList.replaceChildren(...stats.recent_events.map(renderEvent));
    }
  } catch (err) {
    console.error('Failed to update telemetry:', err);
  }
}

document.getElementById('refresh-telemetry-btn').addEventListener('click', fetchTelemetry);

// Initial telemetry fetch
fetchTelemetry();
setInterval(fetchTelemetry, 15000);
