// Identity is provided by the local DSH workspace.
const identity = {user: {id: 'local'}, setup_required: false};
export async function requireIdentity() { document.querySelector('.workspace').hidden = false; return identity; }
export function getIdentity() { return identity; }
export function signOut() {}
export async function renderSecurityPage() { return '<p>账户由 DSH 管理。</p>'; }
export function mountSecurityPage() {}
export async function ensureRecentIdentity() { return false; }
