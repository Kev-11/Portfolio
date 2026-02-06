(function () {
    const params = new URLSearchParams(window.location.search);
    const apiParam = params.get('api');
    if (apiParam) {
        localStorage.setItem('API_URL', apiParam);
    }

    const stored = localStorage.getItem('API_URL');
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const fallback = isLocalhost ? 'http://localhost:8000' : 'https://portfolio-back-flax-beta.vercel.app';

    window.API_URL = stored || fallback;
})();
