const $ = (sel) => document.querySelector(sel);

// Tabs
document.querySelectorAll('.tab').forEach((tab) => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        const key = tab.dataset.tab;
        $('#panel-url').classList.toggle('hidden', key !== 'url');
        $('#panel-file').classList.toggle('hidden', key !== 'file');
    });
});

function setStatus(text, kind = 'info') {
    const el = $('#status');
    el.classList.remove('hidden');
    if (kind === 'loading') {
        el.innerHTML = `<div class="status-line"><div class="spinner"></div><span>${text}</span></div>`;
    } else if (kind === 'error') {
        el.innerHTML = `<div class="err">❌ ${text}</div>`;
    } else if (kind === 'ok') {
        el.innerHTML = `<div class="ok">✅ ${text}</div>`;
    } else {
        el.textContent = text;
    }
}

function hideStatus() { $('#status').classList.add('hidden'); }

function renderResult(data) {
    const result = $('#result');
    const raw = $('#raw');
    result.classList.remove('hidden');

    if (!data.matched) {
        result.innerHTML = `<div class="err">未识别到匹配的歌曲。可以尝试更长的音频片段，或更换视频。</div>`;
        raw.classList.remove('hidden');
        $('#raw-json').textContent = JSON.stringify(data.raw, null, 2);
        return;
    }

    const cover = data.cover_url || '';
    const chips = [];
    if (data.genre) chips.push(`<span class="chip">🎼 ${data.genre}</span>`);
    if (data.isrc) chips.push(`<span class="chip">ISRC: ${data.isrc}</span>`);
    if (data.album) chips.push(`<span class="chip">💿 ${data.album}</span>`);

    const links = [];
    if (data.shazam_url) links.push(`<a href="${data.shazam_url}" target="_blank" rel="noopener">在 Shazam 打开</a>`);
    if (data.apple_music_url) links.push(`<a href="${data.apple_music_url}" target="_blank" rel="noopener">Apple Music</a>`);

    result.innerHTML = `
        <div class="result-hero">
            ${cover ? `<img src="${cover}" alt="cover" />` : ''}
            <div class="result-meta">
                <h2>${escapeHtml(data.title || '')}</h2>
                <div class="artist">${escapeHtml(data.artist || '')}</div>
                <div class="chips">${chips.join('')}</div>
                <div class="links">${links.join('')}</div>
            </div>
        </div>
        ${data.preview_url ? `<audio controls src="${data.preview_url}"></audio>` : ''}
    `;

    raw.classList.remove('hidden');
    $('#raw-json').textContent = JSON.stringify(data.raw, null, 2);
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

async function recognizeUrl() {
    const url = $('#url-input').value.trim();
    if (!url) return setStatus('请输入 URL', 'error');
    $('#btn-url').disabled = true;
    $('#result').classList.add('hidden');
    $('#raw').classList.add('hidden');
    setStatus('正在下载音频并识别，这可能需要 10-30 秒...', 'loading');
    try {
        const resp = await fetch('/api/recognize/url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }
        const data = await resp.json();
        hideStatus();
        renderResult(data);
    } catch (e) {
        setStatus(`识别失败：${e.message}`, 'error');
    } finally {
        $('#btn-url').disabled = false;
    }
}

async function recognizeFile() {
    const f = $('#file-input').files[0];
    if (!f) return setStatus('请选择一个音频文件', 'error');
    $('#btn-file').disabled = true;
    $('#result').classList.add('hidden');
    $('#raw').classList.add('hidden');
    setStatus(`正在上传并识别 ${f.name}...`, 'loading');
    try {
        const fd = new FormData();
        fd.append('file', f);
        const resp = await fetch('/api/recognize/file', { method: 'POST', body: fd });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }
        const data = await resp.json();
        hideStatus();
        renderResult(data);
    } catch (e) {
        setStatus(`识别失败：${e.message}`, 'error');
    } finally {
        $('#btn-file').disabled = false;
    }
}

$('#btn-url').addEventListener('click', recognizeUrl);
$('#btn-file').addEventListener('click', recognizeFile);
