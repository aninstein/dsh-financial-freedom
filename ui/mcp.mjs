/** Prepare the packaged Python service before connecting the DSH MCP client. */
import { apply as connectMcp } from '@deepseek-ai/dsh-mcp-client';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { access, mkdir, readFile, readdir, rename, rm, stat, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const inject = ['tools'];
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = process.env.FINFREEDOM_DATA_DIR || join(process.env.DSH_HOME || join(homedir(), '.dsh'), 'finfreedom');
const pythonPath = dir => join(dir, process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const exists = path => access(path).then(() => true, () => false);
function run(command, args, timeout = 300000) {
  return new Promise((resolveRun, reject) => {
    let stderr = ''; const child = spawn(command, args, { stdio: ['ignore', 'ignore', 'pipe'], windowsHide: true });
    const timer = setTimeout(() => child.kill(), timeout);
    child.stderr.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-3000); });
    child.on('error', err => { clearTimeout(timer); reject(err); });
    child.on('close', code => { clearTimeout(timer); code === 0 ? resolveRun() : reject(Error(`${command} failed (${code}): ${stderr}`)); });
  });
}
async function digestSources() {
  const hash = createHash('sha256');
  async function add(path, relative) {
    const info = await stat(path);
    if (info.isDirectory()) {
      for (const entry of (await readdir(path,{withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))) if (!entry.name.startsWith('.') && entry.name !== '__pycache__' && (entry.isDirectory() || entry.name.endsWith('.py') || entry.name.endsWith('.json'))) await add(join(path,entry.name), `${relative}/${entry.name}`);
    } else { hash.update(relative); hash.update(await readFile(path)); }
  }
  await add(join(root, 'finfreedom'), 'finfreedom');
  await add(join(root, 'pyproject.toml'), 'pyproject.toml');
  return hash.digest('hex').slice(0, 16);
}
async function findPython() {
  const candidates = [process.env.FINFREEDOM_PYTHON, ...(process.platform === 'win32' ? ['python', 'python3'] : ['python3.13','python3.12','python3.11','python3'])].filter(Boolean);
  for (const candidate of candidates) {
    try { await run(candidate, ['-c', 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'], 10000); return candidate; } catch {}
  }
  throw Error('finfreedom 需要 Python 3.11 或更高版本；安装后重启 DSH，或设置 FINFREEDOM_PYTHON。');
}
export async function preparePython() {
  await mkdir(dataDir, {recursive:true, mode:0o700});
  const key = await digestSources();
  const dir = join(dataDir, `runtime-${key}`), marker = join(dir, '.ready');
  if (await exists(marker) && await exists(pythonPath(dir))) return pythonPath(dir);
  const lock = join(dataDir, `runtime-${key}.lock`);
  for (let n=0; n<300; n++) {
    try { await mkdir(lock); break; }
    catch (e) {
      if (e.code !== 'EEXIST') throw e;
      if (await exists(marker) && await exists(pythonPath(dir))) return pythonPath(dir);
      try { if (Date.now() - (await stat(lock)).mtimeMs > 600000) { await rm(lock,{recursive:true,force:true}); continue; } } catch {}
      if (n===299) throw Error('finfreedom Python 环境正在准备或安装锁未释放；请检查后重启 DSH。');
      await new Promise(resolveWait => setTimeout(resolveWait, 1000));
    }
  }
  const tmp = `${dir}.tmp-${process.pid}`;
  try {
    if (await exists(marker) && await exists(pythonPath(dir))) return pythonPath(dir);
    await rm(tmp,{recursive:true,force:true});
    const py=await findPython();
    await run(py,['-m','venv',tmp]);
    await run(pythonPath(tmp),['-m','pip','install','--disable-pip-version-check','--no-input',root]);
    await writeFile(join(tmp,'.ready'), key, {mode:0o600});
    if (await exists(dir)) await rm(dir,{recursive:true,force:true});
    await rename(tmp,dir);
    return pythonPath(dir);
  } catch (err) { await rm(tmp,{recursive:true,force:true}); throw Error(`finfreedom 初始化失败：${err.message}`); }
  finally { await rm(lock,{recursive:true,force:true}); }
}
export async function apply(ctx) {
  const python = await preparePython();
  await connectMcp(ctx, {serverName:'finfreedom', transport:'stdio', command:python,
    args:['-m','finfreedom.mcp_server'], cwd:root, env:{FINFREEDOM_DATA_DIR:dataDir, PYTHONUNBUFFERED:'1', FINFREEDOM_ENABLE_WRITES:'1'},
    toolCallTimeoutMs:60000, failOnStartupError:true,
    reconnect:{enabled:true,initialDelayMs:500,maxDelayMs:30000,maxAttempts:10}});
}
