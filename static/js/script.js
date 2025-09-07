// Minimal JS: server returns HTML for both list and details.
document.addEventListener('DOMContentLoaded', () => {
  const form     = document.querySelector('form.search');
  const seekBtn  = document.querySelector('.btn-seek');
  const results  = document.getElementById('results');
  const panel    = document.getElementById('detail-panel');

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
      results.innerHTML = res.ok ? await res.text() : '<p style="color:#b91c1c">Search failed.</p>';
      panel.innerHTML = `
        <div class="placeholder">
          <h4>No job selected</h4>
          <p>Click a job to see the full description here.</p>
        </div>`;
    } catch {
      results.innerHTML = '<p style="color:#b91c1c">Search failed. Please try again.</p>';
    } finally {
      setLoading(false);
    }
  });

  // Delegated click: fetch server-rendered details for the clicked job id
  results.addEventListener('click', async (e) => {
    const card = e.target.closest?.('article.job-card[data-job-id]');
    if (!card) return;
    const id = card.getAttribute('data-job-id');
    if (!id) return;
    panel.setAttribute('aria-busy', 'true');
    panel.innerHTML = '<p class="meta">Loading details…</p>';
    try {
      const res = await fetch(`/api/job/${encodeURIComponent(id)}`, { headers: { 'Accept': 'text/html' } });
      panel.innerHTML = res.ok ? await res.text() : '<p style="color:#b91c1c">Failed to load job details.</p>';
    } catch {
      panel.innerHTML = '<p style="color:#b91c1c">Failed to load job details.</p>';
    } finally {
      panel.removeAttribute('aria-busy');
    }
  });
});
