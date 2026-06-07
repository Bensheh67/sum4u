/* desktop_main.js — Main window interactions for summary4u desktop app */

(function () {
  'use strict';

  /* ── State ──────────────────────────────────────────────────────── */
  let tasks = [];        // { id, title, state, progress, message }
  let history = [];     // { path, title, type, time, size }
  let eventSource = null;

  /* ── DOM refs ───────────────────────────────────────────────────── */
  const urlForm     = document.getElementById('urlForm');
  const urlInput    = document.getElementById('urlInput');
  const submitBtn   = document.getElementById('submitBtn');
  const templateSel = document.getElementById('templateSelect');
  const dropZone    = document.getElementById('dropZone');
  const fileInput   = document.getElementById('fileInput');
  const taskList    = document.getElementById('taskList');
  const historyList  = document.getElementById('historyList');

  /* ── Utilities ──────────────────────────────────────────────────── */
  function $(sel) { return document.querySelector(sel); }
  function $$(sel) { return document.querySelectorAll(sel); }

  function relativeTime(iso) {
    const diff = (Date.now() - new Date(iso)) / 1000;
    if (diff < 60)   return '刚刚';
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
    return `${Math.floor(diff / 86400)}天前`;
  }

  function fileIcon(filename) {
    if (filename.endsWith('.md')) return '📄';
    return '🎙️';
  }

  /* ── Submit button enabled only when URL is non-empty ──────────── */
  function updateSubmitState() {
    const val = urlInput.value.trim();
    submitBtn.disabled = !val;
  }

  urlInput.addEventListener('input', updateSubmitState);

  /* ── SSE progress stream ─────────────────────────────────────────── */
  function connectSSE() {
    if (eventSource) eventSource.close();
    eventSource = new EventSource('/api/progress/stream');
    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onProgress(data);
      } catch (_) {}
    };
    eventSource.onerror = () => {
      eventSource.close();
      // Reconnect after 3s
      setTimeout(connectSSE, 3000);
    };
  }

  function onProgress(data) {
    // data: { task_id, title, state, progress, message }
    if (!data.task_id) return;

    const existing = tasks.find(t => t.id === data.task_id);
    if (existing) {
      Object.assign(existing, data);
    } else {
      tasks.push({ id: data.task_id, title: data.title || '处理中', ...data });
    }
    renderTasks();

    // Auto-advance history when task completes
    if (data.state === 'completed') {
      setTimeout(() => {
        tasks = tasks.filter(t => t.id !== data.task_id);
        renderTasks();
        loadHistory();
      }, 1500);
    }
    if (data.state === 'error') {
      setTimeout(() => {
        tasks = tasks.filter(t => t.id !== data.task_id);
        renderTasks();
      }, 5000);
    }
  }

  /* ── Render tasks ────────────────────────────────────────────────── */
  function renderTasks() {
    if (tasks.length === 0) {
      taskList.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">🎙️</div>
          <div class="empty-state__text">暂无进行中的任务</div>
        </div>`;
      return;
    }

    taskList.innerHTML = tasks.map(task => {
      const stateLabels = {
        queued: '排队中',
        downloading: '下载中',
        transcribing: '转录中',
        summarizing: '总结中',
        completed: '完成',
        error: '失败'
      };
      const label = stateLabels[task.state] || task.state || '';
      const meta = task.message || label;

      return `
      <div class="task-card" data-state="${task.state}" data-id="${task.id}">
        <div class="task-card__icon">🎙️</div>
        <div class="task-card__body">
          <div class="task-card__title" title="${escHtml(task.title || '处理中')}">${escHtml(task.title || '处理中')}</div>
          <div class="task-card__meta">${escHtml(meta)}</div>
        </div>
        <div class="task-card__progress-wrap">
          <div class="task-card__progress-bar">
            <div class="task-card__progress-fill" style="width:${task.progress || 0}%"></div>
          </div>
          <span class="task-card__pct">${task.progress != null ? task.progress + '%' : label}</span>
        </div>
      </div>`;
    }).join('');
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* ── Render history ─────────────────────────────────────────────── */
  function renderHistory() {
    if (history.length === 0) {
      historyList.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">📄</div>
          <div class="empty-state__text">暂无历史记录</div>
        </div>`;
      return;
    }

    // Show last 5 (AC-15)
    const shown = history.slice(0, 5);
    historyList.innerHTML = shown.map(item => `
      <div class="history-item" data-path="${escHtml(item.path)}">
        <div class="history-item__icon">${fileIcon(item.path)}</div>
        <div class="history-item__body">
          <div class="history-item__title">${escHtml(item.title)}</div>
          <div class="history-item__meta">${escHtml(item.source)} · ${item.time}</div>
        </div>
        <button class="history-item__action" data-action="open">打开</button>
      </div>`).join('');

    // Bind open buttons
    historyList.querySelectorAll('[data-action="open"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const path = btn.closest('.history-item').dataset.path;
        openInFinder(path);
      });
    });

    // Bind click-to-highlight (AC-16)
    historyList.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', () => {
        openInFinder(item.dataset.path);
      });
    });
  }

  function openInFinder(path) {
    // Uses macOS `open -R` to reveal in Finder (AC-16)
    window.pywebview.api.open_in_finder(path).catch(() => {
      // Fallback: try via fetch to a backend endpoint
      fetch('/api/open-in-finder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      }).catch(() => {});
    });
  }

  /* ── Load history from backend ─────────────────────────────────── */
  async function loadHistory() {
    try {
      const res = await fetch('/api/task-history');
      if (!res.ok) return;
      const data = await res.json();
      history = (data.history || []).slice(0, 50).map(item => {
        const name = item.result_path
          ? item.result_path.split('/').pop().replace('_总结.md', '').replace('.md', '')
          : item.input || '未知';
        return {
          path: item.result_path || '',
          title: name || '未知',
          source: item.type === 'video_url' ? '在线视频' : '本地文件',
          time: item.end_time ? relativeTime(item.end_time) : '最近'
        };
      });
      renderHistory();
    } catch (_) {}
  }

  /* ── Submit URL form ────────────────────────────────────────────── */
  urlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    const template = templateSel.value;
    submitBtn.disabled = true;
    submitBtn.textContent = '提交中...';

    try {
      const res = await fetch('/process-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, template })
      });
      const data = await res.json();
      if (data.task_id) {
        tasks.push({
          id: data.task_id,
          title: data.title || '处理中',
          state: 'queued',
          progress: 0,
          message: '排队中'
        });
        renderTasks();
        urlInput.value = '';
        updateSubmitState();
      } else if (data.error) {
        alert('提交失败: ' + data.error);
      }
    } catch (err) {
      alert('网络错误，请重试');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 3 14 13 2 22 11 11 22 13 2"/></svg> 开始总结`;
    }
  });

  /* ── Drop zone ──────────────────────────────────────────────────── */
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = Array.from(e.dataTransfer.files);
    if (files.length) await uploadFiles(files);
  });

  fileInput.addEventListener('change', async () => {
    const files = Array.from(fileInput.files);
    if (files.length) await uploadFiles(files);
    fileInput.value = '';
  });

  async function uploadFiles(files) {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('template', templateSel.value);
      try {
        const res = await fetch('/upload-audio', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.task_id) {
          tasks.push({ id: data.task_id, title: file.name, state: 'queued', progress: 0, message: '排队中' });
          renderTasks();
        }
      } catch (_) {}
    }
  }

  /* ── Settings button ──────────────────────────────────────────── */
  document.getElementById('settingsBtn').addEventListener('click', () => {
    window.pywebview.api.open_preferences().catch(() => {});
  });

  /* ── View all history ────────────────────────────────────────────── */
  document.getElementById('viewAllBtn').addEventListener('click', (e) => {
    e.preventDefault();
    // Open summaries folder
    window.pywebview.api.open_summaries_folder().catch(() => {});
  });

  /* ── Init ───────────────────────────────────────────────────────── */
  connectSSE();
  loadHistory();

})();