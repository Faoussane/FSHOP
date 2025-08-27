
const slides = document.querySelectorAll('.carrousel-slide');
const dots = document.querySelectorAll('.carrousel-dot');
const container = document.querySelector('.carrousel-container');

let index = 0;

const showSlide = (i) => {
  container.style.transform = `translateX(-${i * 100}%)`;
  dots.forEach((dot, idx) => {
    dot.classList.toggle('active', idx === i);
  });
};

dots.forEach((dot, i) => {
  dot.addEventListener('click', () => {
    index = i;
    showSlide(index);
  });
});

setInterval(() => {
  index = (index + 1) % slides.length;
  showSlide(index);
}, 5000);

{% comment %} Paiement en ligne {% endcomment %}

document.getElementById('pay-btn').addEventListener('click', async () => {
  const resp = await fetch("{% url 'payments:create_checkout_session' %}", {
    method: "POST",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({})
  });
  const data = await resp.json();
  if (data.checkout_url) {
    window.location.href = data.checkout_url;
  } else {
    const p = document.getElementById('pay-error');
    p.textContent = data.error || "Une erreur est survenue.";
    p.classList.remove("hidden");
  }
});