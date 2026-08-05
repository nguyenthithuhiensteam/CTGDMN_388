const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const BACKEND_URL = 'http://127.0.0.1:8000';
const HEALTH_URL = `${BACKEND_URL}/api/health`;
const APP_TITLE = 'Thư viện số CTGDMN';

let mainWindow = null;
let backendProcess = null;
let backendStartedByLauncher = false;
let shuttingDown = false;
let backendLog = '';

function getProjectRoot() {
  if (app.isPackaged) return process.resourcesPath;
  return path.resolve(__dirname, '..');
}

function getIconPath() {
  return path.join(getProjectRoot(), 'frontend', 'assets', 'logo.ico');
}

function appendLog(text) {
  backendLog += String(text || '');
  if (backendLog.length > 12000) backendLog = backendLog.slice(-12000);
}

function checkUrl(url, timeoutMs = 1200) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      res.resume();
      resolve(res.statusCode >= 200 && res.statusCode < 500);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function findPython() {
  const candidates = [
    { cmd: 'python', args: ['--version'] },
    { cmd: 'py', args: ['--version'] }
  ];
  for (const c of candidates) {
    const ok = await new Promise((resolve) => {
      const child = spawn(c.cmd, c.args, { windowsHide: true });
      child.on('error', () => resolve(false));
      child.on('close', (code) => resolve(code === 0));
    });
    if (ok) return c.cmd;
  }
  return null;
}

function runPythonOnce(pythonCmd, args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn(pythonCmd, args, { cwd, windowsHide: true });
    child.stdout.on('data', (data) => appendLog(data));
    child.stderr.on('data', (data) => appendLog(data));
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${pythonCmd} ${args.join(' ')} exited with code ${code}`));
    });
  });
}

async function ensureDependencies(pythonCmd, projectRoot) {
  const reqPath = path.join(projectRoot, 'requirements.txt');
  if (!fs.existsSync(reqPath)) return;
  await runPythonOnce(pythonCmd, ['-m', 'pip', 'install', '-r', reqPath], projectRoot);
}

async function startBackendIfNeeded() {
  const alreadyRunning = await checkUrl(HEALTH_URL, 900);
  if (alreadyRunning) {
    backendStartedByLauncher = false;
    return { reused: true };
  }

  const projectRoot = getProjectRoot();
  const pythonCmd = await findPython();
  if (!pythonCmd) {
    throw new Error('Không tìm thấy Python. Vui lòng cài Python 3.11 trở lên hoặc chạy thử run_backend.bat để kiểm tra môi trường.');
  }

  // Cài (hoặc cập nhật) thư viện Python cần thiết mỗi lần khởi động — pip sẽ tự bỏ qua
  // các gói đã có sẵn nên lần khởi động sau vẫn nhanh. Việc này đảm bảo requirements.txt
  // mới (ví dụ khi ứng dụng được cập nhật) luôn được cài đủ trước khi chạy backend.
  await runPythonOnce(pythonCmd, ['-m', 'pip', 'install', '--upgrade', 'pip'], projectRoot).catch(() => {});
  await ensureDependencies(pythonCmd, projectRoot);

  await runPythonOnce(pythonCmd, ['-m', 'backend.init_db'], projectRoot);

  backendProcess = spawn(
    pythonCmd,
    ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'],
    { cwd: projectRoot, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] }
  );
  backendStartedByLauncher = true;

  backendProcess.stdout.on('data', (data) => appendLog(data));
  backendProcess.stderr.on('data', (data) => appendLog(data));
  backendProcess.on('error', (err) => appendLog(`\nBackend process error: ${err.message}\n`));
  backendProcess.on('exit', (code, signal) => {
    appendLog(`\nBackend exited: code=${code} signal=${signal}\n`);
    backendProcess = null;
    if (!shuttingDown && mainWindow) {
      showBackendError(new Error('Backend đã dừng ngoài ý muốn. Vui lòng kiểm tra Python và run_backend.bat.'));
    }
  });

  // Lần chạy đầu tiên phải cài thư viện + nạp dữ liệu gốc từ 2 file Excel vào
  // database rỗng — trên máy chậm hoặc bị phần mềm diệt virus quét theo thời
  // gian thực, bước này có thể mất tới vài phút. Đợi đủ lâu (tối đa ~5 phút)
  // thay vì báo lỗi quá sớm trong khi backend vẫn đang khởi động bình thường.
  for (let i = 0; i < 300; i += 1) {
    if (await checkUrl(HEALTH_URL, 900)) return { reused: false };
    await delay(1000);
  }

  throw new Error('Backend khởi động quá lâu (hơn 5 phút). Vui lòng kiểm tra Python và run_backend.bat.');
}

function createWindow() {
  const iconPath = getIconPath();
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 720,
    title: APP_TITLE,
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

function loadFrontend() {
  const indexPath = path.join(getProjectRoot(), 'frontend', 'index.html');
  if (!fs.existsSync(indexPath)) {
    showBackendError(new Error(`Không tìm thấy frontend/index.html tại: ${indexPath}`));
    return;
  }
  mainWindow.loadFile(indexPath);
}

function showLoadingScreen() {
  if (!mainWindow) return;
  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!doctype html><html lang="vi"><head><meta charset="utf-8"><title>${APP_TITLE}</title>
    <style>
      body{font-family:Segoe UI,Arial,sans-serif;background:#0A1F4E;color:#fff;margin:0;height:100vh;display:flex;align-items:center;justify-content:center}
      .box{text-align:center;max-width:420px;padding:0 20px}
      .spin{width:38px;height:38px;border:3px solid rgba(255,255,255,.25);border-top-color:#3A9A3E;border-radius:50%;margin:0 auto 18px;animation:sp 0.9s linear infinite}
      @keyframes sp{to{transform:rotate(360deg)}}
      h1{font-size:16px;margin:0 0 8px}
      p{font-size:12.5px;color:rgba(255,255,255,.7);line-height:1.6;margin:0}
    </style></head><body><div class="box"><div class="spin"></div>
    <h1>Đang khởi động ứng dụng...</h1>
    <p>Lần đầu mở máy có thể mất 1–2 phút để cài đặt và nạp dữ liệu.<br>Vui lòng đợi, đừng đóng cửa sổ này.</p>
    </div></body></html>
  `)}`);
}

function showBackendError(error) {
  if (!mainWindow) createWindow();
  const message = String(error && error.message ? error.message : error);
  const safeMessage = message.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  const safeLog = backendLog.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <!doctype html><html lang="vi"><head><meta charset="utf-8"><title>${APP_TITLE}</title>
    <style>body{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fb;color:#102033;margin:0;padding:36px}.box{max-width:900px;margin:auto;background:white;border:1px solid #d9e2ef;border-radius:16px;padding:26px;box-shadow:0 16px 40px rgba(15,23,42,.12)}h1{margin:0 0 12px;color:#0f3b66}.warn{background:#fff7ed;border-left:5px solid #f59e0b;padding:14px;border-radius:10px;line-height:1.55}code,pre{background:#0f172a;color:#e2e8f0;border-radius:10px;padding:12px;display:block;white-space:pre-wrap;overflow:auto}p{line-height:1.6}.small{color:#64748b;font-size:13px}</style></head><body><div class="box"><h1>Không khởi động được backend</h1><div class="warn">${safeMessage}</div><p>Vui lòng kiểm tra Python 3.11 trở lên, các thư viện trong <code>requirements.txt</code>, hoặc chạy thử <code>run_backend.bat</code>.</p><p class="small">Nếu backend đang chạy thủ công tại http://127.0.0.1:8000, hãy đóng app rồi mở lại.</p><h3>Log backend</h3><pre>${safeLog || 'Chưa có log.'}</pre></div></body></html>
  `)}`);
}

async function boot() {
  createWindow();
  showLoadingScreen();
  try {
    await startBackendIfNeeded();
    loadFrontend();
  } catch (err) {
    showBackendError(err);
  }
}

function stopBackend() {
  shuttingDown = true;
  if (backendProcess && backendStartedByLauncher) {
    try {
      backendProcess.kill('SIGTERM');
    } catch (err) {
      appendLog(`\nCould not stop backend gracefully: ${err.message}\n`);
    }
    backendProcess = null;
  }
}

app.whenReady().then(boot);

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', stopBackend);

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) boot();
});