// Theme toggler with localStorage persistence
(function () {
  const KEY = 'doc.theme';
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const saved = localStorage.getItem(KEY);
  const initial = saved || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', initial);

  function setTheme(mode) {
    document.documentElement.setAttribute('data-theme', mode);
    localStorage.setItem(KEY, mode);
    btn && (btn.innerHTML = icon(mode) + label(mode));
  }

  function label(mode) { return `<span style="margin-left:8px">${mode === 'dark' ? 'Dark' : 'Light'}</span>`; }
  function icon(mode) {
    return mode === 'dark'
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zm10.48 0l1.79-1.8-1.41-1.41-1.8 1.79 1.42 1.42zM12 4V1h-0v3h0zm0 19v-3h0v3h0zM4 13H1v-0h3v0zm22 0h-3v0h3v0zM6.76 19.16l-1.42 1.42-1.79-1.8 1.41-1.41 1.8 1.79zm12.69-1.79l-1.42-1.42 1.8-1.79 1.41 1.41-1.79 1.8zM12 8a4 4 0 100 8 4 4 0 000-8z"/></svg>'
  }

  const btn = document.querySelector('[data-theme-toggle]');
  if (btn) {
    btn.innerHTML = icon(initial) + label(initial);
    btn.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme') || initial;
      setTheme(cur === 'dark' ? 'light' : 'dark');
    });
  }
})();

