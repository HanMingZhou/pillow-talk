const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess = null;

// 后端服务配置
const BACKEND_PORT = 8000;
const BACKEND_HOST = 'localhost';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    },
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#667eea',
    show: false
  });

  // 加载本地 HTML 文件
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // 开发模式下打开开发者工具
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// 启动后端服务
function startBackend() {
  return new Promise((resolve, reject) => {
    const backendPath = path.join(__dirname, '..', 'pillow-talk-backend');
    const venvPython = path.join(backendPath, 'venv', 'bin', 'python');
    const envFile = path.join(backendPath, '.env');
    
    console.log('Starting backend service...');
    console.log('Backend path:', backendPath);
    console.log('Python path:', venvPython);
    console.log('Env file:', envFile);

    // 检查 .env 文件是否存在
    const fs = require('fs');
    if (!fs.existsSync(envFile)) {
      reject(new Error('.env file not found at: ' + envFile));
      return;
    }

    // 从 backend 根目录启动，这样 .env 文件可以被正确加载
    // 使用 -m 参数指定模块路径
    backendProcess = spawn(venvPython, [
      '-m', 'uvicorn', 
      'src.pillow_talk.main:app',  // 从根目录指定完整模块路径
      '--host', BACKEND_HOST, 
      '--port', BACKEND_PORT.toString()
    ], {
      cwd: backendPath,  // 在 backend 根目录运行
      env: { 
        ...process.env, 
        PYTHONUNBUFFERED: '1'
      }
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
      if (data.toString().includes('Uvicorn running')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
      reject(error);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
      backendProcess = null;
    });

    // 5秒后如果还没启动成功，也认为成功（可能日志格式不同）
    setTimeout(() => {
      if (backendProcess) {
        resolve();
      }
    }, 5000);
  });
}

// 停止后端服务
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend service...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// 检查后端是否运行
async function checkBackend() {
  try {
    const response = await fetch(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

// 应用启动
app.whenReady().then(async () => {
  try {
    // 检查后端是否已经在运行
    const isRunning = await checkBackend();
    
    if (!isRunning) {
      // 启动后端服务
      await startBackend();
      console.log('Backend service started successfully');
    } else {
      console.log('Backend service is already running');
    }

    // 创建窗口
    createWindow();
  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox(
      '启动失败',
      '无法启动后端服务。请确保 Python 环境已正确配置。\n\n错误信息：' + error.message
    );
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// 应用退出
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackend();
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

// IPC 通信
ipcMain.handle('get-backend-url', () => {
  return `http://${BACKEND_HOST}:${BACKEND_PORT}`;
});

ipcMain.handle('check-backend-status', async () => {
  return await checkBackend();
});
