// script.js
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form.search');
  const seekBtn = document.querySelector('.btn-seek');
  const resultsEl = document.getElementById('results');
  const panelEl = document.getElementById('detail-panel');

  const setLoading = (on) => {
    if (!seekBtn) return;
    seekBtn.disabled = on;
    seekBtn.textContent = on ? 'Searching…' : 'SEEK';
  };

  // ----- Details panel helpers -----
  // Find the nearest job card from a clicked/focused element
  const getCard = (el) => (el && el.closest) ? el.closest('.job-card') : null;

  // Render details into the right-hand panel from a job card's content or data-attributes
  const renderDetailsFromCard = (card) => {
    if (!panelEl || !card) return;

    const title = card.querySelector('h3')?.textContent?.trim() || 'Job';
    const meta  = card.querySelector('.meta')?.textContent?.trim() || '';
    // Prefer an explicit "excerpt" if present, else the first non-meta paragraph
    const summary = card.querySelector('.excerpt, p:not(.meta)')?.textContent?.trim() || '';

    // Allow richer content via data attributes when available
    const full = card.dataset.fullDescription?.trim() || summary || 'No summary available for this role yet.';

    panelEl.innerHTML = `
      <h4 class="title">${title}</h4>
      ${meta ? `<p class="meta">${meta}</p>` : ''}
      <div class="body">
        <p>${full}</p>
      </div>
      <div class="actions">
        <button class="btn-seek" type="button">Apply now</button>
        <button class="btn-outline" type="button">Save</button>
        <button class="btn-outline" type="button">Share</button>
      </div>
    `;
  };

  // Event delegation so it works for dynamically injected results
  const attachResultsHandlers = () => {
    if (!resultsEl) return;

    // Mouse clicks
    resultsEl.addEventListener('click', (e) => {
      const card = getCard(e.target);
      if (card) renderDetailsFromCard(card);
    });

    // Keyboard activation (Enter/Space when a card itself is focused)
    resultsEl.addEventListener('keydown', (e) => {
      const targetCard = getCard(e.target);
      if (!targetCard) return;
      if (e.key === 'Enter' || e.key === ' ') {
        // Only trigger when the focused element is the card container (not when typing in inputs)
        if (targetCard === e.target) {
          e.preventDefault();
          renderDetailsFromCard(targetCard);
        }
      }
    });
  };

  attachResultsHandlers();

  // ----- Search flow (kept from your original) -----
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

      // Inject server-rendered cards (event delegation means handlers still work)
      resultsEl.innerHTML = html;

      // Optional: clear the details panel back to placeholder after each search.
      // Comment this out if you'd rather keep the last-opened job.
      if (panelEl) {
        panelEl.innerHTML = `
          <div class="placeholder">
            <h4>No job selected</h4>
            <p>Click a job to see the full description here.</p>
          </div>
        `;
      }
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

  // ----- (Optional) If your server returns job IDs and you want live fetch per card -----
  // If your cards include data-job-id, you can replace renderDetailsFromCard with a fetch like:
  //
  // async function renderDetailsFromCard(card) {
  //   if (!panelEl || !card) return;
  //   const jobId = card.dataset.jobId;
  //   if (!jobId) { /* fallback to current behavior */ return fallback(); }
  //   panelEl.setAttribute('aria-busy', 'true');
  //   panelEl.innerHTML = '<p class="meta">Loading details…</p>';
  //   try {
  //     const res = await fetch(`/api/job/${encodeURIComponent(jobId)}`, { headers: { 'Accept': 'application/json' } });
  //     const data = await res.json();
  //     panelEl.innerHTML = /* build HTML from data */;
  //   } catch (e) {
  //     panelEl.innerHTML = '<p style="color:#b91c1c">Failed to load job details.</p>';
  //   } finally {
  //     panelEl.removeAttribute('aria-busy');
  //   }
  // }
});
