// script.js
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form.search');
  const seekBtn = document.querySelector('.btn-seek');
  const resultsEl = document.getElementById('results');

  const setLoading = (on) => {
    if (!seekBtn) return;
    seekBtn.disabled = on;
    seekBtn.textContent = on ? 'Searching…' : 'SEEK';
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      keywords: document.getElementById('what').value.trim(),
      classification: document.getElementById('classification').value,
      where: document.getElementById('where').value.trim(),
    };

    setLoading(true);
    try {
      const res = await fetch('/api/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'text/html' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const html = await res.text();
      resultsEl.innerHTML = html; // server-rendered cards
    } catch (err) {
      console.error(err);
      resultsEl.innerHTML = '<p style="color:#b91c1c">Search failed. Please try again.</p>';
    } finally {
      setLoading(false);
    }
  });

  if (seekBtn) {
    seekBtn.addEventListener('click', () => form.requestSubmit());
  }
});
