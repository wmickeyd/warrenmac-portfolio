// Apply saved theme before first paint to avoid a light/dark flash.
// Loaded as a blocking external script so the CSP doesn't need 'unsafe-inline'.
(function () {
  var t = localStorage.getItem('portfolio_theme') ||
    (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  document.documentElement.setAttribute('data-theme', t);
})();
