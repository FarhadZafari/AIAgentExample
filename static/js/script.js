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

  // --- Search submit -> loads left-hand results ---
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

  // --- Delegated click on results list -> loads right-hand details ---
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
      // ✅ store jobId on the panel
      panel.dataset.jobId = id;
    } catch {
      panel.innerHTML = '<p style="color:#b91c1c">Failed to load job details.</p>';
    } finally {
      panel.removeAttribute('aria-busy');
    }
  });

  // --- Clarification modal logic ---
  function showClarifyModal(question, onSubmit) {
    const modal = document.getElementById('clarify-modal');
    document.getElementById('clarify-question').textContent = question;
    document.getElementById('clarify-answer').value = '';
    modal.style.display = 'flex';

    const submitBtn = document.getElementById('clarify-submit');
    const handler = () => {
      const answer = document.getElementById('clarify-answer').value.trim();
      modal.style.display = 'none';
      submitBtn.removeEventListener('click', handler);
      onSubmit(answer);
    };
    submitBtn.addEventListener('click', handler);
  }

  // --- Delegated click inside the details panel for Tailor CV ---
  panel.addEventListener('click', async (e) => {
    const btn = e.target.closest?.('[data-action="tailor"]');
    if (!btn) return;

    const prevText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Tailoring…';

    const payload = {
      job_id: panel.dataset.jobId || null,
      keywords: document.getElementById('what')?.value.trim() || '',
      classification: document.getElementById('classification')?.value || '',
      where: document.getElementById('where')?.value.trim() || '',
    };

    async function handleTailorCVRequest(payload) {
      try {
        const res = await fetch('/api/tailor-cv', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(payload),
        });

        let messageHtml = '';
        if (res.ok) {
          const data = await res.json();

          // Handle clarification needed
          if (data.clarification_needed) {
            showClarifyModal(data.question, async (answer) => {
              // Send answer to backend (assume /api/clarify-cv endpoint)
              const clarifyRes = await fetch('/api/clarify-cv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ job_id: payload.job_id, answer }),
              });
              if (clarifyRes.ok) {
                // After clarification, try tailoring again
                await handleTailorCVRequest({ ...payload, clarification_response: answer });
              } else {
                const errHtml = '<p style="color:#b91c1c">Clarification failed. Please try again.</p>';
                const actions = panel.querySelector('.actions');
                if (actions) {
                  actions.insertAdjacentHTML('afterend', `<div class="tailor-status">${errHtml}</div>`);
                } else {
                  panel.insertAdjacentHTML('beforeend', `<div class="tailor-status">${errHtml}</div>`);
                }
              }
            });
            return;
          }

          messageHtml = `<p style="color:#166534">${data.message || 'Success!'}</p>`;
          if (data.pdf_url) {
            window.open(data.pdf_url, "_blank");
          }
        } else {
          messageHtml = '<p style="color:#b91c1c">CV tailoring failed.</p>';
        }

        const actions = panel.querySelector('.actions');
        if (actions) {
          actions.insertAdjacentHTML('afterend', `<div class="tailor-status">${messageHtml}</div>`);
        } else {
          panel.insertAdjacentHTML('beforeend', `<div class="tailor-status">${messageHtml}</div>`);
        }
      } catch (err) {
        console.error(err);
        const actions = panel.querySelector('.actions');
        const errHtml = '<p style="color:#b91c1c">Error occurred. Please try again.</p>';
        if (actions) {
          actions.insertAdjacentHTML('afterend', `<div class="tailor-status">${errHtml}</div>`);
        } else {
          panel.insertAdjacentHTML('beforeend', `<div class="tailor-status">${errHtml}</div>`);
        }
      } finally {
        btn.disabled = false;
        btn.textContent = prevText;
      }
    }

    await handleTailorCVRequest(payload);
  });
});