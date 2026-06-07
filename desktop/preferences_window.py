"""
preferences_window.py — HTML preferences window for summary4u desktop app.

AC-7:  change hotkey → saved to prefs.json → HotkeyManager.update_combo()
AC-20: change default Whisper model → saved to prefs.json

Opens as a second pywebview window (not the main window).
No separate "save" button — all changes are immediate (AC-7, AC-20).

Window: 600×500, fixed, non-resizable, centered.
Left sidebar: 240px navigation (通用 / 快捷键 / 模型与性能 / 输出 / API密钥).
Right content: setting items for the selected section.

Communication with main_app:
  - Window is opened by main_app via open_preferences()
  - Changes fire a pywebview JS bridge call → desktop/preferences.py
  - main_app registers the JS API via window.expose()
"""

from __future__ import annotations

import os
import threading
import webview
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desktop.main_app import Summary4uApp


# ── Window reference ───────────────────────────────────────────────────────────

_prefs_window: webview.Window | None = None


# ── HTML template ─────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<title>偏好设置</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --primary:   #0D9488;
    --primary-light: #CCFBF1;
    --bg:        #F8FAFC;
    --surface:   #FFFFFF;
    --border:    #E2E8F0;
    --text:      #1E293B;
    --muted:     #64748B;
    --danger:    #EF4444;
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    color: var(--text);
    background: var(--bg);
    height: 100vh;
    display: flex;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── Sidebar ──────────────────────────────────────────────────────── */
  aside {{
    width: 200px;
    min-width: 200px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}

  aside h2 {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    padding: 0 16px 8px;
  }}

  .nav-item {{
    padding: 8px 16px;
    cursor: pointer;
    border-radius: var(--radius-sm);
    color: var(--text);
    font-size: 13px;
    margin: 0 8px;
    transition: background 150ms;
  }}
  .nav-item:hover {{ background: var(--bg); }}
  .nav-item.active {{
    background: var(--primary-light);
    color: var(--primary);
    font-weight: 600;
  }}

  /* ── Content ──────────────────────────────────────────────────────── */
  main {{
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
  }}

  section {{ display: none; }}
  section.active {{ display: block; }}

  h3 {{
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}

  .setting-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
  }}
  .setting-row:last-child {{ border-bottom: none; }}

  .setting-label {{ font-size: 13px; color: var(--text); }}
  .setting-desc  {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}

  /* ── Form controls ───────────────────────────────────────────────── */
  select, input[type="text"], input[type="number"] {{
    height: 32px;
    padding: 0 10px;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    font-size: 13px;
    color: var(--text);
    background: var(--surface);
    outline: none;
    min-width: 140px;
  }}
  select:focus, input:focus {{
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(13,148,136,0.1);
  }}

  .hotkey-display {{
    display: flex;
    align-items: center;
    gap: 4px;
  }}
  .hotkey-key {{
    display: inline-block;
    height: 28px;
    padding: 0 8px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg);
    color: var(--text);
    line-height: 28px;
  }}
  .recording {{ border-color: var(--primary); background: var(--primary-light); color: var(--primary); }}

  /* Toggle switch */
  .toggle {{
    position: relative;
    width: 40px;
    height: 22px;
  }}
  .toggle input {{ opacity: 0; width: 0; height: 0; }}
  .toggle-slider {{
    position: absolute;
    inset: 0;
    background: #CBD5E1;
    border-radius: 11px;
    cursor: pointer;
    transition: background 200ms;
  }}
  .toggle-slider::before {{
    content: '';
    position: absolute;
    width: 16px; height: 16px;
    left: 3px; top: 3px;
    background: white;
    border-radius: 50%;
    transition: transform 200ms;
  }}
  .toggle input:checked + .toggle-slider {{ background: var(--primary); }}
  .toggle input:checked + .toggle-slider::before {{ transform: translateX(18px); }}

  /* Save feedback */
  .save-ok {{
    font-size: 12px;
    color: #10B981;
    opacity: 0;
    transition: opacity 300ms;
    margin-left: 8px;
  }}
  .save-ok.show {{ opacity: 1; }}
</style>
</head>
<body>

<!-- ── Sidebar ─────────────────────────────────────────────────────────── -->
<aside>
  <h2>偏好设置</h2>
  <div class="nav-item active" data-section="general">通用</div>
  <div class="nav-item" data-section="shortcuts">快捷键</div>
  <div class="nav-item" data-section="model">模型与性能</div>
  <div class="nav-item" data-section="output">输出</div>
  <div class="nav-item" data-section="api">API 密钥</div>
</aside>

<!-- ── Main content ───────────────────────────────────────────────────── -->
<main>

  <!-- General ──────────────────────────────────────────────────────── -->
  <section id="sec-general" class="active">
    <h3>通用</h3>

    <div class="setting-row">
      <div>
        <div class="setting-label">开机自启动</div>
        <div class="setting-desc">登录 Mac 时自动启动 summary4u</div>
      </div>
      <label class="toggle">
        <input type="checkbox" id="auto-launch"/>
        <span class="toggle-slider"></span>
      </label>
    </div>

    <div class="setting-row">
      <div>
        <div class="setting-label">主题</div>
        <div class="setting-desc">应用界面配色方案</div>
      </div>
      <select id="theme">
        <option value="system">跟随系统</option>
        <option value="light">始终浅色</option>
        <option value="dark">始终深色</option>
      </select>
    </div>

    <div class="setting-row">
      <div>
        <div class="setting-label">任务完成通知</div>
        <div class="setting-desc">总结完成时发送系统通知</div>
      </div>
      <label class="toggle">
        <input type="checkbox" id="notify-on-done" checked/>
        <span class="toggle-slider"></span>
      </label>
    </div>
  </section>

  <!-- Shortcuts ────────────────────────────────────────────────────── -->
  <section id="sec-shortcuts">
    <h3>快捷键</h3>

    <div class="setting-row">
      <div>
        <div class="setting-label">快速总结</div>
        <div class="setting-desc">全局快捷键，调出浮窗输入视频链接</div>
      </div>
      <div class="hotkey-display" id="hotkey-display">
        <span class="hotkey-key">⌘</span>
        <span>+</span>
        <span class="hotkey-key">⇧</span>
        <span>+</span>
        <span class="hotkey-key">S</span>
        <span class="save-ok" id="hotkey-saved">已保存</span>
      </div>
    </div>

    <div class="setting-row">
      <div>
        <div class="setting-label">录制新快捷键</div>
        <div class="setting-desc">点击后按下期望的组合键</div>
      </div>
      <button id="record-hotkey"
        style="height:32px;padding:0 12px;border:1px solid var(--border);border-radius:8px;background:var(--surface);cursor:pointer;font-size:13px;">
        录制…
      </button>
    </div>
  </section>

  <!-- Model & Performance ─────────────────────────────────────────── -->
  <section id="sec-model">
    <h3>模型与性能</h3>

    <div class="setting-row">
      <div>
        <div class="setting-label">默认 Whisper 模型</div>
        <div class="setting-desc">转录精度与速度的权衡：tiny / base / small / medium / large-v3</div>
      </div>
      <select id="whisper-model">
        <option value="tiny">tiny（最快）</option>
        <option value="base">base</option>
        <option value="small" selected>small（默认）</option>
        <option value="medium">medium</option>
        <option value="large-v3">large-v3（最准）</option>
      </select>
    </div>

    <div class="setting-row">
      <div>
        <div class="setting-label">默认总结模板</div>
        <div class="setting-desc">新建任务时默认使用的总结模板</div>
      </div>
      <select id="default-template">
        <option value="default课堂笔记" selected>课堂笔记</option>
        <option value="youtube_英文笔记">英文笔记</option>
        <option value="youtube_结构化提取">结构化提取</option>
        <option value="youtube_精炼提取">精炼提取</option>
        <option value="youtube_专业课笔记">专业课笔记</option>
        <option value="爆款短视频文案">短视频文案</option>
        <option value="youtube_视频总结">视频总结</option>
      </select>
    </div>

    <div class="setting-row">
      <div>
        <div class="setting-label">最大并发任务数</div>
        <div class="setting-desc">同时进行的最大总结任务数量</div>
      </div>
      <input type="number" id="max-concurrent" min="1" max="8" value="3" style="width:80px;"/>
    </div>
  </section>

  <!-- Output ────────────────────────────────────────────────────────── -->
  <section id="sec-output">
    <h3>输出</h3>

    <div class="setting-row">
      <div>
        <div class="setting-label">总结保存路径</div>
        <div class="setting-desc">相对项目根目录的保存文件夹</div>
      </div>
      <input type="text" id="output-folder" value="summaries" style="width:180px;"/>
    </div>

    <div class="setting-row">
      <div>
        <div class="setting-label">同时保存转录文本</div>
        <div class="setting-desc">在 transcriptions/ 文件夹保存原始转录内容</div>
      </div>
      <label class="toggle">
        <input type="checkbox" id="save-transcriptions" checked/>
        <span class="toggle-slider"></span>
      </label>
    </div>
  </section>

  <!-- API Keys ──────────────────────────────────────────────────────── -->
  <section id="sec-api">
    <h3>API 密钥</h3>
    <div id="api-key-status" style="font-size:13px;color:var(--muted);padding:8px 0;">
      正在检查 API 密钥配置…
    </div>
    <div id="api-key-list" style="margin-top:12px;display:flex;flex-direction:column;gap:12px;">
      <!-- Filled by JS -->
    </div>
  </section>

</main>

<script>
  // ── Navigation ──────────────────────────────────────────────────────
  document.querySelectorAll('.nav-item').forEach(function(el) {{
    el.addEventListener('click', function() {{
      document.querySelectorAll('.nav-item').forEach(function(x) {{ x.classList.remove('active'); }});
      document.querySelectorAll('section').forEach(function(x) {{ x.classList.remove('active'); }});
      el.classList.add('active');
      document.getElementById('sec-' + el.dataset.section).classList.add('active');
    }});
  }});

  // ── Load preferences from Python ───────────────────────────────────
  async function loadPrefs() {{
    const prefs = await window.pywebview.api.get_preferences();
    if (!prefs) return;

    // General
    document.getElementById('theme').value = prefs.theme || 'system';

    // Notifications
    document.getElementById('notify-on-done').checked = prefs['notify_on_done'] !== false;

    // Model
    const model = prefs.default_whisper_model || 'small';
    document.getElementById('whisper-model').value = model;
    document.getElementById('default-template').value = prefs.default_template || 'default课堂笔记';
    document.getElementById('max-concurrent').value = prefs.max_concurrent_tasks || 3;

    // Output
    document.getElementById('output-folder').value = prefs.output_folder || 'summaries';
    document.getElementById('save-transcriptions').checked = prefs.save_transcriptions !== false;

    // Shortcuts — display hotkey keys
    const hotkey = prefs.hotkey || 'cmd+shift+s';
    displayHotkey(hotkey);

    // Auto-launch (informational only — actual setting done via OS)
    document.getElementById('auto-launch').checked = prefs.auto_launch || false;
  }}

  // ── Save helpers ───────────────────────────────────────────────────
  function showSaved(el) {{
    el.classList.add('show');
    setTimeout(function() {{ el.classList.remove('show'); }}, 2000);
  }}

  async function savePref(key, value) {{
    await window.pywebview.api.set_preference(key, value);
  }}

  // ── Hotkey display ─────────────────────────────────────────────────
  function displayHotkey(hotkeyStr) {{
    const KEYS = {{
      'cmd': '⌘', 'shift': '⇧', 'alt': '⌥',
      'ctrl': '⌃', 'control': '⌃'
    }};
    const display = document.getElementById('hotkey-display');
    display.innerHTML = '';
    hotkeyStr.split('+').forEach(function(part) {{
      if (display.children.length > 0) {{
        const span = document.createElement('span');
        span.textContent = '+';
        display.appendChild(span);
      }}
      const key = document.createElement('span');
      key.className = 'hotkey-key';
      key.textContent = KEYS[part.toLowerCase()] || part.toUpperCase();
      display.appendChild(key);
    }});
    const saved = document.createElement('span');
    saved.className = 'save-ok';
    saved.id = 'hotkey-saved';
    saved.textContent = '已保存';
    display.appendChild(saved);
  }}

  // ── Event listeners ────────────────────────────────────────────────
  document.getElementById('theme').addEventListener('change', function(e) {{
    savePref('theme', e.target.value);
  }});

  document.getElementById('notify-on-done').addEventListener('change', function(e) {{
    savePref('notify_on_done', e.target.checked);
  }});

  document.getElementById('whisper-model').addEventListener('change', function(e) {{
    savePref('default_whisper_model', e.target.value);
  }});

  document.getElementById('default-template').addEventListener('change', function(e) {{
    savePref('default_template', e.target.value);
  }});

  document.getElementById('max-concurrent').addEventListener('change', function(e) {{
    savePref('max_concurrent_tasks', parseInt(e.target.value, 10));
  }});

  document.getElementById('output-folder').addEventListener('change', function(e) {{
    savePref('output_folder', e.target.value);
  }});

  document.getElementById('save-transcriptions').addEventListener('change', function(e) {{
    savePref('save_transcriptions', e.target.checked);
  }});

  // Hotkey recording
  let isRecording = false;
  const recordBtn = document.getElementById('record-hotkey');
  const hotkeyDisplay = document.getElementById('hotkey-display');

  recordBtn.addEventListener('click', function() {{
    isRecording = true;
    recordBtn.textContent = '按下组合键…';
    recordBtn.classList.add('recording');
    hotkeyDisplay.querySelectorAll('.hotkey-key').forEach(function(k) {{ k.classList.add('recording'); }});
  }});

  document.addEventListener('keydown', async function(e) {{
    if (!isRecording) return;
    e.preventDefault();
    e.stopPropagation();

    const parts = [];
    if (e.metaKey || e.ctrlKey) parts.push('cmd');
    if (e.shiftKey) parts.push('shift');
    if (e.altKey) parts.push('alt');
    const ch = e.key.toLowerCase();
    if (ch !== 'meta' && ch !== 'shift' && ch !== 'alt' && ch !== 'control') {{
      parts.push(ch.length === 1 ? ch : e.key);
    }}

    if (parts.length >= 2) {{
      const comboStr = parts.join('+');
      await savePref('hotkey', comboStr);
      displayHotkey(comboStr);
      showSaved(document.getElementById('hotkey-saved'));
    }}

    isRecording = false;
    recordBtn.textContent = '录制…';
    recordBtn.classList.remove('recording');
    hotkeyDisplay.querySelectorAll('.hotkey-key').forEach(function(k) {{ k.classList.remove('recording'); }});
  }});

  // Load on start
  loadPrefs();
</script>
</body>
</html>
"""


# ── Bridge API (exposed to JS via pywebview) ───────────────────────────────────

class PreferencesBridge:
    """
    Python-side API callable from the preferences window JS via window.pywebview.api.
    """

    def __init__(self, prefs_window_ref):
        # prefs_window_ref is a callable that returns the prefs window if open
        self._get_window = prefs_window_ref

    def get_preferences(self) -> dict:
        """Return all preferences as a dict (used by JS to populate UI on load)."""
        from desktop.preferences import Preferences
        return Preferences().get_all()

    def set_preference(self, key: str, value) -> dict:
        """
        Write a single preference. Triggers hotkey reload if key == 'hotkey'.
        Returns the updated preferences dict so JS can confirm.
        """
        from desktop.preferences import Preferences
        from desktop import hotkey as hotkey_mod

        prefs = Preferences()
        prefs.set(key, value)

        if key == "hotkey":
            # AC-7: hotkey changed → notify HotkeyManager
            # The hotkey manager singleton is accessible via the main_app's
            # bridge. We fire a callback registered at app init.
            _apply_new_hotkey(prefs.get("hotkey"))

        return prefs.get_all()

    def check_api_keys(self) -> dict:
        """Check which API keys are configured (values redacted)."""
        from desktop.preferences import Preferences
        # API keys live in config.json, not prefs.json
        import os, json
        cfg = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        result = {}
        if os.path.exists(cfg):
            try:
                with open(cfg) as f:
                    data = json.load(f)
                keys = data.get("api_keys", {})
                for provider, val in keys.items():
                    result[provider] = "已配置" if val else "未配置"
            except Exception:
                pass
        return result


# ── Window management ─────────────────────────────────────────────────────────

def open_preferences(parent_app: "Summary4uApp | None" = None) -> None:
    """
    Open (or bring to front) the preferences window.
    Called from main_app menu or ⌘, shortcut.
    """
    global _prefs_window

    if _prefs_window is not None:
        _prefs_window.show()
        _prefs_window.focus()
        return

    bridge = PreferencesBridge(lambda: _prefs_window)

    _prefs_window = webview.create_window(
        "偏好设置",
        html=HTML,
        width=600,
        height=500,
        resizable=False,
        min_size=(600, 500),
        js_api=bridge,
    )

    def _on_closed():
        global _prefs_window
        _prefs_window = None

    webview.start(lambda: None, _prefs_window,on_closed=_on_closed)


def close_preferences() -> None:
    global _prefs_window
    if _prefs_window is not None:
        _prefs_window.close()
        _prefs_window = None


def _apply_new_hotkey(combo_str: str) -> None:
    """
    Called when prefs.hotkey changes.
    Updates the global HotkeyManager singleton and registers a reload
    signal that main_app listens to.
    """
    from desktop import hotkey as hotkey_mod

    combo = hotkey_mod.parse_combo(combo_str)
    # The HotkeyManager singleton is set up in main_app.
    # We communicate via a module-level "reload" event that main_app hooks.
    cb = _hotkey_reload_callback
    if cb is not None:
        cb(combo)


# Module-level hotkey reload callback set by main_app
_hotkey_reload_callback: callable | None = None


def on_hotkey_reload(callback: callable) -> None:
    """
    main_app calls this to register the hotkey manager update function.
    preferences_window calls _apply_new_hotkey(), which in turn calls this.
    """
    global _hotkey_reload_callback
    _hotkey_reload_callback = callback
