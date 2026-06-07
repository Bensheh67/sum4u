/* desktop_popover.js — Quick input popover interactions */

(function () {
  'use strict';

  /* ── DOM refs ───────────────────────────────────────────────────── */
  const popover        = document.getElementById('popover');
  const urlInput       = document.getElementById('popoverUrlInput');
  const templateSel   = document.getElementById('popoverTemplate');
  const modelSel       = document.getElementById('popoverModel');
  const submitBtn      = document.getElementById('popoverSubmit');
  const closeBtn       = document.getElementById('closeBtn');
  const cancelBtn      = document.getElementById('cancelBtn');

  /* ── State ──────────────────────────────────────────────────────── */
  let closing = false;

  /* ── Submit button enabled only when URL is non-empty (AC-8) ─────── */
  function updateSubmitState() {
    submitBtn.disabled = !urlInput.value.trim();
  }
  urlInput.addEventListener('input', updateSubmitState);

  /* ── Close with animation (AC-5/6) ─────────────────────────────── */
  function closePopover() {
    if (closing) return;
    closing = true;
    popover.classList.add('closing');
    setTimeout(() => {
      // Signal to Python side to close the popover window
      window.popoverAPI.close();
    }, 200);
  }

  /* ── Submit ─────────────────────────────────────────────────────── */
  async function handleSubmit() {
    const url = urlInput.value.trim();
    if (!url) return;

    submitBtn.disabled = true;
    submitBtn.textContent = '提交中...';

    try {
      const res = await fetch('/process-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          template: templateSel.value,
          model: modelSel.value
        })
      });
      const data = await res.json();
      if (data.error) {
        submitBtn.textContent = '✨ 开始总结';
        submitBtn.disabled = false;
        return;
      }
      // Success — close popover after 200ms (AC-5/6)
      closePopover();
    } catch (_) {
      submitBtn.textContent = '✨ 开始总结';
      submitBtn.disabled = false;
    }
  }

  /* ── Event listeners ─────────────────────────────────────────────── */
  submitBtn.addEventListener('click', handleSubmit);

  // Enter key submits (AC-12)
  urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
    // Escape closes
    if (e.key === 'Escape') {
      closePopover();
    }
  });

  closeBtn.addEventListener('click', closePopover);
  cancelBtn.addEventListener('click', closePopover);

  // Auto-paste from clipboard on focus (DESIGN_APP §3.2)
  urlInput.addEventListener('focus', async () => {
    try {
      const text = await window.popoverAPI.readClipboard();
      // Only auto-paste if input is empty and clipboard looks like a URL
      if (!urlInput.value.trim() && text && /^https?:\/\//.test(text.trim())) {
        urlInput.value = text.trim();
        updateSubmitState();
      }
    } catch (_) {}
  });

  // Initial state — focus the input
  urlInput.focus();

})();