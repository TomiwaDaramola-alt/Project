// ==========================================================================
// DARMHIE'S COLLECTIONS — MAIN JAVASCRIPT
// ==========================================================================

// ===== SCROLL REVEAL =====
const revealElements = document.querySelectorAll('.reveal');

const revealOnScroll = () => {
    revealElements.forEach(el => {
        const windowHeight = window.innerHeight;
        const elementTop = el.getBoundingClientRect().top;
        const revealPoint = 100;
        
        if (elementTop < windowHeight - revealPoint) {
            el.classList.add('visible');
        }
    });
};

window.addEventListener('scroll', revealOnScroll);
window.addEventListener('load', revealOnScroll);

// ===== NAV SCROLL EFFECT =====
const topNav = document.getElementById('topNav');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 50) {
        topNav.classList.add('scrolled');
    } else {
        topNav.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
});

// ===== CART DRAWER =====
function toggleCart() {
    const drawer = document.getElementById('cartDrawer');
    drawer.classList.toggle('active');
}

// ===== AI CHAT =====
function toggleChat() {
    const box = document.getElementById('chatBox');
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

function sendMessage(event) {
    if (event.key !== 'Enter') return;
    
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    
    const messages = document.getElementById('chatMessages');
    messages.innerHTML += `<div class="user-msg"><strong><i class="fa-solid fa-user" style="margin-right: 6px;"></i></strong> ${message}</div>`;
    
    fetch('/api/ai', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(r => r.json())
    .then(data => {
        messages.innerHTML += `<div class="ai-msg"><strong><i class="fa-solid fa-robot" style="margin-right: 6px; color: var(--crimson);"></i></strong> ${data.response}</div>`;
        messages.scrollTop = messages.scrollHeight;
    });
    
    input.value = '';
}

// ===== QUICK ADD TO CART =====
function quickAdd(productId) {
    fetch(`/add_to_cart/${productId}`, {
        method: 'POST',
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(() => {
        showToast('Added to bag', 'success');
        updateCartBadge();
    });
}

// ===== UPDATE CART BADGE =====
function updateCartBadge() {
    // Simple refresh for now — can be enhanced with AJAX cart count
    location.reload();
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `notification ${type}`;
    
    const icons = {
        success: '<i class="fa-solid fa-check-circle"></i>',
        error: '<i class="fa-solid fa-circle-exclamation"></i>',
        info: '<i class="fa-solid fa-circle-info"></i>'
    };
    
    toast.innerHTML = `${icons[type]} <span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// ===== STAGGER ANIMATION FOR CHILDREN =====
const staggerContainers = document.querySelectorAll('.stagger-children');

const staggerObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const children = entry.target.children;
            Array.from(children).forEach((child, i) => {
                setTimeout(() => {
                    child.classList.add('visible');
                }, i * 100);
            });
            staggerObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

staggerContainers.forEach(container => staggerObserver.observe(container));

// ===== BOTTOM NAV ACTIVE STATE =====
const currentPath = window.location.pathname;
document.querySelectorAll('.bottom-nav .nav-item').forEach(item => {
    if (item.getAttribute('href') === currentPath) {
        item.classList.add('active');
    }
});

// ===== CART QUANTITY AUTO-UPDATE =====
document.querySelectorAll('.qty-input').forEach(input => {
    input.addEventListener('change', function() {
        this.closest('form').submit();
    });
});

// ===== NEWS TICKER PAUSE ON HOVER =====
const tickerWrap = document.querySelector('.ticker-wrap');
if (tickerWrap) {
    tickerWrap.addEventListener('mouseenter', () => {
        tickerWrap.style.animationPlayState = 'paused';
    });
    tickerWrap.addEventListener('mouseleave', () => {
        tickerWrap.style.animationPlayState = 'running';
    });
}
