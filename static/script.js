/* =============================================
   MEAL MAPPER — script.js
   ============================================= */

// NAVBAR scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 30);
);

// HAMBURGER menu
const hamburger = document.getElementById('hamburger');
const navLinks = document.querySelector('.nav-links');
hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => navLinks.classList.remove('open'));
});

// SCROLL REVEAL
const revealTargets = ['.about-grid', '.about-stats', '.feature-card', '.recipe-card', '.footer-top'];
revealTargets.forEach(selector => {
  document.querySelectorAll(selector).forEach(el => el.classList.add('reveal'));
});
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const delay = entry.target.dataset.delay || 0;
      setTimeout(() => entry.target.classList.add('visible'), Number(delay));
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// ACTIVE NAV LINK on scroll
const sections = document.querySelectorAll('section[id], footer[id]');
const navAnchors = document.querySelectorAll('.nav-links a');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    if (window.scrollY >= section.offsetTop - 100) current = section.getAttribute('id');
  });
  navAnchors.forEach(a => {
    a.style.color = '';
    if (a.getAttribute('href') === `#${current}`) a.style.color = 'var(--clr-accent)';
  });
});

// FEATURE CARD tilt effect
document.querySelectorAll('.feature-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const rotateX = ((e.clientY - rect.top - rect.height / 2) / (rect.height / 2)) * -6;
    const rotateY = ((e.clientX - rect.left - rect.width / 2) / (rect.width / 2)) * 6;
    card.style.transform = `translateY(-6px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    card.style.transition = 'transform 0.1s ease';
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
    card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease';
  });
});

// SMOOTH SCROLL
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', (e) => {
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});

// STAT COUNTER animation
function animateCounter(el, target, duration = 1200) {
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start += step;
    if (start >= target) { el.textContent = target + (el.dataset.suffix || ''); clearInterval(timer); }
    else el.textContent = Math.floor(start) + (el.dataset.suffix || '');
  }, 16);
}
const statObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const el = entry.target;
      const num = parseInt(el.textContent);
      el.dataset.suffix = el.textContent.replace(num, '');
      animateCounter(el, num);
      statObserver.unobserve(el);
    }
  });
}, { threshold: 0.5 });
document.querySelectorAll('.stat-num').forEach(el => statObserver.observe(el));

// GET STARTED button
document.querySelector('.nav-cta').addEventListener('click', () => {
  document.querySelector('#recipes').scrollIntoView({ behavior: 'smooth' });
});

console.log('%c🗺️ Meal Mapper Loaded!', 'color: #c8703a; font-size: 1.2rem; font-weight: bold;');
// === ADD RECIPE ===
document.getElementById('submitRecipe').addEventListener('click', async () => {
  const name        = document.getElementById('recipeName').value.trim();
  const ingredients = document.getElementById('recipeIngredients').value
                        .split('\n').map(i => i.trim()).filter(Boolean);
  const steps       = document.getElementById('recipeSteps').value
                        .split('\n').map(s => s.trim()).filter(Boolean);
  const msg         = document.getElementById('formMessage');

  if (!name || ingredients.length === 0 || steps.length === 0) {
    msg.textContent = '⚠️ Please fill in all fields!';
    msg.className = 'form-message error';
    return;
  }

  try {
    const res = await fetch('/add_recipe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, ingredients, steps })
    });
    const data = await res.json();

    if (res.ok) {
      msg.textContent = `✅ ${data.message}`;
      msg.className = 'form-message success';
      document.getElementById('recipeName').value = '';
      document.getElementById('recipeIngredients').value = '';
      document.getElementById('recipeSteps').value = '';
    } else {
      msg.textContent = `❌ ${data.error}`;
      msg.className = 'form-message error';
    }
  } catch (err) {
    msg.textContent = '❌ Could not connect to server.';
    msg.className = 'form-message error';
  }
});