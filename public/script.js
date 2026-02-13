const API = window.location.origin;

async function shortenUrl() {
    const urlInput = document.getElementById('url-input');
    const aliasInput = document.getElementById('alias-input');
    const expiresInput = document.getElementById('expires-input');
    const btn = document.getElementById('shorten-btn');
    const errorDiv = document.getElementById('error-msg');
    const resultDiv = document.getElementById('result');

    errorDiv.classList.remove('show');
    resultDiv.classList.remove('show');

    const url = urlInput.value.trim();
    if (!url) {
        showError('Please enter a URL.');
        return;
    }

    const body = { url };
    const alias = aliasInput.value.trim();
    const expires = expiresInput.value.trim();

    if (alias) body.custom_code = alias;
    if (expires !== '') body.expires_in_days = parseInt(expires);

    btn.disabled = true;
    btn.textContent = 'Shortening...';

    try {
        const res = await fetch(`${API}/api/shorten`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await res.json();

        if (!res.ok) {
            showError(data.error || 'Something went wrong.');
            return;
        }

        const link = document.getElementById('result-link');
        link.href = data.short_url;
        link.textContent = data.short_url;

        let meta = data.reused ? 'Existing link returned' : 'New link created';
        document.getElementById('result-meta').textContent = meta;

        resultDiv.classList.add('show');

    } catch (err) {
        showError('Could not connect to the API.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Shorten';
    }
}

function showError(msg) {
    const errorDiv = document.getElementById('error-msg');
    errorDiv.textContent = msg;
    errorDiv.classList.add('show');
}

async function copyUrl() {
    const link = document.getElementById('result-link').textContent;
    const btn = document.getElementById('copy-btn');

    try {
        await navigator.clipboard.writeText(link);
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    } catch {
        btn.textContent = 'Failed';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    }
}

document.getElementById('url-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') shortenUrl();
});