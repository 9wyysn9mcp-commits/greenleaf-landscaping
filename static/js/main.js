// ── Nav scroll effect ──
const navbar = document.getElementById("navbar");
window.addEventListener("scroll", () => {
  navbar.classList.toggle("scrolled", window.scrollY > 40);
});

// ── Mobile hamburger ──
const hamburger = document.getElementById("hamburger");
const navLinks = document.getElementById("nav-links");
hamburger.addEventListener("click", () => {
  navLinks.classList.toggle("open");
});
navLinks.querySelectorAll("a").forEach(link => {
  link.addEventListener("click", () => navLinks.classList.remove("open"));
});

// ── Scroll reveal ──
const reveals = document.querySelectorAll(".service-card, .about-inner, .contact-inner, .gallery-card, .testimonial-card, .trust-item");
reveals.forEach(el => el.classList.add("reveal"));

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add("visible"), i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

reveals.forEach(el => observer.observe(el));

// ── Active nav link on scroll ──
const sections = document.querySelectorAll("section[id], div[id]");
const navAnchors = document.querySelectorAll(".nav-links a[href^='#']");

window.addEventListener("scroll", () => {
  let current = "";
  sections.forEach(section => {
    if (window.scrollY >= section.offsetTop - 120) current = section.id;
  });
  navAnchors.forEach(a => {
    a.style.color = a.getAttribute("href") === `#${current}` ? "white" : "";
    a.style.fontWeight = a.getAttribute("href") === `#${current}` ? "700" : "";
  });
});

// ── Quote form submission ──
const form = document.getElementById("quote-form");
const msgDiv = document.getElementById("form-message");
const submitBtn = document.getElementById("submit-btn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  msgDiv.className = "form-message hidden";

  const services = [...form.querySelectorAll(".checkboxes input:checked")].map(c => c.value);

  const payload = {
    name: form.name.value,
    email: form.email.value,
    phone: form.phone.value,
    address: form.address.value,
    services,
    message: form.message.value,
    preferred_date: form.preferred_date.value,
  };

  submitBtn.disabled = true;
  submitBtn.querySelector(".btn-text").textContent = "Sending…";

  try {
    const res = await fetch("/quote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error("Something went wrong. Please call or text us at (647) 215-4544.");
    }

    if (data.success) {
      msgDiv.textContent = "✅ " + data.message;
      msgDiv.className = "form-message success";
      form.reset();
    } else {
      throw new Error(data.error || "Something went wrong. Please call or text us at (647) 215-4544.");
    }
  } catch (err) {
    msgDiv.textContent = "❌ " + err.message;
    msgDiv.className = "form-message error";
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector(".btn-text").textContent = "Send Quote Request";
    msgDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
});
