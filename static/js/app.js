// ==================== MK SNIPER BOT - FRONTEND APPLICATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initNavbar();
    initAnimations();
    initCopyButtons();
    initToasts();
    initCharts();
    initCounters();
    initLiveTime();
    initSocketIO();
    initModals();
    initAdminSidebar();
    initTicker();
});

// ==================== PARTICLE BACKGROUND ====================
function initParticles() {
    const container = document.querySelector('.bg-animation');
    if (!container) return;

    const colors = ['#00f260', '#0575e6', '#7c3aed', '#f857a6'];
    const particleCount = 30;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 6 + 2;
        const color = colors[Math.floor(Math.random() * colors.length)];

        particle.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            left: ${Math.random() * 100}%;
            animation-duration: ${Math.random() * 20 + 15}s;
            animation-delay: ${Math.random() * 10}s;
        `;
        container.appendChild(particle);
    }
}

// ==================== NAVBAR ====================
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    const toggle = document.querySelector('.mobile-toggle');
    const links = document.querySelector('.navbar-links');

    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 50);
        });
    }

    if (toggle && links) {
        toggle.addEventListener('click', () => {
            links.classList.toggle('open');
            toggle.textContent = links.classList.contains('open') ? '✕' : '☰';
        });
    }
}

// ==================== SCROLL ANIMATIONS ====================
function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.card, .stat-card, .plan-card, .feature-card, .signal-card, .content-card').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
}

// ==================== COPY TO CLIPBOARD ====================
function initCopyButtons() {
    document.querySelectorAll('.copy-text').forEach(el => {
        el.addEventListener('click', () => {
            const text = el.getAttribute('data-copy') || el.textContent.trim();
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success');
            }).catch(() => {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showToast('Copied!', 'success');
            });
        });
    });
}

// ==================== TOAST NOTIFICATIONS ====================
let toastContainer = null;

function initToasts() {
    toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
}

function showToast(message, type = 'info', duration = 4000) {
    if (!toastContainer) initToasts();

    const icons = {
        success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Expose globally
window.showToast = showToast;

// ==================== LIVE CLOCK ====================
function initLiveTime() {
    const clockEl = document.getElementById('live-clock');
    if (!clockEl) return;

    function updateClock() {
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        clockEl.textContent = `${h}:${m}:${s}`;
    }

    updateClock();
    setInterval(updateClock, 1000);
}

// ==================== COUNTER ANIMATION ====================
function initCounters() {
    const counters = document.querySelectorAll('[data-count]');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });

    counters.forEach(counter => observer.observe(counter));
}

function animateCounter(el) {
    const target = parseInt(el.getAttribute('data-count'));
    const duration = 2000;
    const step = target / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

// ==================== MINI CHARTS ====================
function initCharts() {
    document.querySelectorAll('.mini-chart').forEach(canvas => {
        if (canvas.tagName !== 'CANVAS') return;
        const ctx = canvas.getContext('2d');
        drawMiniChart(ctx, canvas.width, canvas.height);
    });
}

function drawMiniChart(ctx, w, h) {
    const points = 60;
    const data = [];
    let val = h / 2;

    for (let i = 0; i < points; i++) {
        val += (Math.random() - 0.48) * 8;
        val = Math.max(20, Math.min(h - 20, val));
        data.push(val);
    }

    // Gradient fill
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(0, 242, 96, 0.2)');
    grad.addColorStop(1, 'rgba(0, 242, 96, 0.0)');

    ctx.clearRect(0, 0, w, h);

    // Area
    ctx.beginPath();
    ctx.moveTo(0, h);
    data.forEach((y, i) => {
        const x = (i / (points - 1)) * w;
        ctx.lineTo(x, y);
    });
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((y, i) => {
        const x = (i / (points - 1)) * w;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#00f260';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Dot at end
    const lastX = w;
    const lastY = data[data.length - 1];
    ctx.beginPath();
    ctx.arc(lastX - 2, lastY, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#00f260';
    ctx.fill();

    // Animate
    setTimeout(() => {
        drawMiniChart(ctx, w, h);
    }, 3000);
}

// ==================== SOCKET.IO INTEGRATION ====================
function initSocketIO() {
    if (typeof io === 'undefined') return;

    try {
        const socket = io();

        socket.on('connect', () => {
            console.log('🔗 WebSocket connected');
        });

        socket.on('new_signal', (data) => {
            showToast(`New signal: ${data.pair} ${data.direction}`, 'success');
            if (document.getElementById('signals-list')) {
                addSignalCard(data);
            }
        });

        socket.on('subscription_update', (data) => {
            showToast(`Subscription updated: ${data.plan}`, 'info');
            setTimeout(() => location.reload(), 2000);
        });

        socket.on('admin_broadcast', (data) => {
            showToast(data.message, 'info', 8000);
        });

        socket.on('user_activity', (data) => {
            updateActivityFeed(data);
        });

        window.appSocket = socket;
    } catch (e) {
        console.log('Socket.IO not available');
    }
}

function addSignalCard(data) {
    const container = document.getElementById('signals-list');
    if (!container) return;

    const dirClass = data.direction === 'CALL' ? 'call' : 'put';
    const dirIcon = data.direction === 'CALL' ? '🟢' : '🔴';

    const card = document.createElement('div');
    card.className = `signal-card ${dirClass} animate-slide-up`;
    card.innerHTML = `
        <div class="signal-pair">
            <h3>${data.pair}</h3>
            <span class="signal-direction ${dirClass}">${dirIcon} ${data.direction}</span>
        </div>
        <div class="signal-details">
            <div class="signal-detail">
                <span class="label">Duration</span>
                <span class="value">${data.duration || '1m'}</span>
            </div>
            <div class="signal-detail">
                <span class="label">Entry Time</span>
                <span class="value">${data.entry_time || 'Now'}</span>
            </div>
            <div class="signal-detail">
                <span class="label">Payout</span>
                <span class="value">${data.payout || 85}%</span>
            </div>
            <div class="signal-detail">
                <span class="label">Win Prob</span>
                <span class="value" style="color: var(--accent-green)">${data.accuracy || 97}%</span>
            </div>
        </div>
        <div class="signal-accuracy">
            <div class="accuracy-bar">
                <div class="accuracy-fill" style="width: ${data.accuracy || 97}%"></div>
            </div>
            <span class="accuracy-text">${data.accuracy || 97}%</span>
        </div>
    `;

    container.prepend(card);
}

function updateActivityFeed(data) {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;

    const item = document.createElement('div');
    item.className = 'activity-item animate-slide-up';
    item.style.cssText = 'padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.85rem;';
    item.innerHTML = `
        <span style="color: var(--accent-green)">●</span>
        <span>${data.message}</span>
        <span style="color: var(--text-muted); margin-left: auto; font-size: 0.75rem">${new Date().toLocaleTimeString()}</span>
    `;

    feed.prepend(item);
    if (feed.children.length > 20) feed.lastChild.remove();
}

// ==================== MODALS ====================
function initModals() {
    document.querySelectorAll('[data-modal]').forEach(trigger => {
        trigger.addEventListener('click', () => {
            const modalId = trigger.getAttribute('data-modal');
            openModal(modalId);
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal(overlay);
        });
    });

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const overlay = btn.closest('.modal-overlay');
            if (overlay) closeModal(overlay);
        });
    });
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(overlay) {
    overlay.classList.remove('active');
}

window.openModal = openModal;
window.closeModal = closeModal;

// ==================== ADMIN SIDEBAR ====================
function initAdminSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
}

// ==================== TICKER ====================
function initTicker() {
    const ticker = document.querySelector('.ticker-content');
    if (!ticker) return;

    const pairs = [
        { name: 'EUR/USD', change: '+0.12%', up: true },
        { name: 'GBP/USD', change: '-0.08%', up: false },
        { name: 'BTC/USD', change: '+2.34%', up: true },
        { name: 'Gold OTC', change: '+0.45%', up: true },
        { name: 'USD/JPY', change: '-0.15%', up: false },
        { name: 'ETH/USD', change: '+1.87%', up: true },
        { name: 'Tesla OTC', change: '+3.21%', up: true },
        { name: 'EUR/JPY', change: '-0.22%', up: false },
    ];

    // Duplicate for seamless scroll
    const html = pairs.map(p => `
        <span class="ticker-item">
            <span class="pair-name">${p.name}</span>
            <span class="${p.up ? 'up' : 'down'}">${p.change} ${p.up ? '▲' : '▼'}</span>
        </span>
    `).join('');

    ticker.innerHTML = html + html;
}

// ==================== ADMIN FUNCTIONS ====================
async function generateKey(plan) {
    try {
        const res = await fetch('/admin/api/generate-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Key generated: ${data.key}`, 'success', 8000);
            if (document.getElementById('keys-table')) location.reload();
        } else {
            showToast(data.error || 'Error generating key', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

async function activateUser(userId, plan) {
    try {
        const res = await fetch('/admin/api/activate-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, plan })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`User ${userId} activated with ${plan} plan`, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(data.error || 'Error', 'error');
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

async function deactivateUser(userId) {
    if (!confirm('Deactivate this user?')) return;
    try {
        const res = await fetch('/admin/api/deactivate-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        if (data.success) {
            showToast('User deactivated', 'info');
            setTimeout(() => location.reload(), 1500);
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

async function sendBroadcast() {
    const msg = document.getElementById('broadcast-message')?.value;
    if (!msg) {
        showToast('Please enter a message', 'warning');
        return;
    }
    try {
        const res = await fetch('/admin/api/broadcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Broadcast sent to ${data.count} users`, 'success');
            document.getElementById('broadcast-message').value = '';
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

async function deleteContent(contentId) {
    if (!confirm('Delete this content?')) return;
    try {
        const res = await fetch(`/admin/api/content/${contentId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast('Content deleted', 'info');
            setTimeout(() => location.reload(), 1000);
        }
    } catch (e) {
        showToast('Network error', 'error');
    }
}

// ==================== FORM HANDLING ====================
document.querySelectorAll('form[data-ajax]').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn?.textContent;
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Processing...';
        }

        try {
            const formData = new FormData(form);
            const res = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData
            });

            if (res.redirected) {
                window.location.href = res.url;
                return;
            }

            const data = await res.json();
            if (data.success) {
                showToast(data.message || 'Success!', 'success');
                if (data.redirect) setTimeout(() => window.location.href = data.redirect, 1500);
            } else {
                showToast(data.error || 'An error occurred', 'error');
            }
        } catch (e) {
            showToast('Network error', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        }
    });
});