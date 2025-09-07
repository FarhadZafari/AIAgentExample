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

  function renderJobs(jobs = []) {
    resultsEl.innerHTML = ''; // clear old content
    if (!Array.isArray(jobs) || jobs.length === 0) {
      resultsEl.innerHTML = '<p style="color:#6b7280">No jobs found.</p>';
      return;
    }

    const frag = document.createDocumentFragment();
    jobs.forEach(job => {
      const card = document.createElement('article');
      card.className = 'job-card';
      card.innerHTML = `
        <h3>${job.title ?? 'Untitled role'}</h3>
        <p class="meta">
          ${job.location ?? ''}${job.type ? ' • ' + job.type : ''}${job.salary ? ' • ' + job.salary : ''}
        </p>
        <p>${job.summary ?? ''}</p>
        <button class="btn-outline">View job</button>
      `;
      frag.appendChild(card);
    });
    resultsEl.appendChild(frag);
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const keywords = document.getElementById('what').value.trim();
    const classification = document.getElementById('classification').value;
    const where = document.getElementById('where').value.trim();

    setLoading(true);
    try {
      const res = await fetch('/api/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords, classification, where })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json(); // { jobs: [...] }
      renderJobs(data.jobs);
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
