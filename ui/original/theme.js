const key = 'finfreedom.workspace.appearance';
function apply(value) {
  document.documentElement.dataset.workspaceTheme = value === 'dark' ? 'dark' : 'light';
  document.documentElement.style.colorScheme = value === 'dark' ? 'dark' : 'light';
}
let saved;
try { saved = localStorage.getItem(key); } catch (_) {}
apply(saved || 'light');
window.addEventListener('storage', event => { if (event.key === key) apply(event.newValue); });
window.addEventListener('message', event => {
  if (event.origin === location.origin && event.source === window.parent && event.data?.type === 'finfreedom-theme') apply(event.data.value);
});
