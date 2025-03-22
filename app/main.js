const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const axios = require('axios');
const isDev = process.env.NODE_ENV === 'development';

// Pythonバックエンドプロセス
let pythonProcess = null;
const BACKEND_URL = 'http://127.0.0.1:5003';

function createWindow() {
  // ブラウザウィンドウを作成
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // 開発モードの場合はデベロッパーツールを開く
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // HTMLファイルをロード
  mainWindow.loadFile(path.join(__dirname, 'frontend', 'index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Pythonバックエンドを開始
function startBackendServer() {
  const serverPath = isDev 
    ? path.join(__dirname, 'backend', 'server.py')
    : path.join(process.resourcesPath, 'backend', 'server.py');
  
  console.log('Starting backend server from:', serverPath);
  
  pythonProcess = spawn('python', [serverPath], {
    stdio: 'pipe',
    shell: true
  });
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend server output: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Backend server error: ${data}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Backend server exited with code ${code}`);
  });
}

// アプリの準備ができたらウィンドウを作成
app.whenReady().then(() => {
  startBackendServer();
  createWindow();
  
  app.on('activate', function () {
    // macOSでは、ドックアイコンをクリックしてウィンドウがない場合は
    // 新しいウィンドウを作成するのが一般的です
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// すべてのウィンドウが閉じられたときにアプリを終了（Windows & Linux）
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// アプリが終了するときにPythonプロセスを終了
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// バックエンドサーバーが起動するまで少し待機
const waitForBackend = () => new Promise(resolve => setTimeout(resolve, 2000));

// IPC通信の設定
ipcMain.handle('predict-demand', async (event, data) => {
  try {
    await waitForBackend();
    const response = await axios.post(`${BACKEND_URL}/api/predict`, data);
    return response.data;
  } catch (error) {
    console.error('需要予測エラー:', error);
    return { error: '需要予測中にエラーが発生しました' };
  }
});

// モデルトレーニングのIPC処理
ipcMain.handle('train-model', async (event, data) => {
  try {
    await waitForBackend();
    const response = await axios.post(`${BACKEND_URL}/api/train`, data);
    return response.data;
  } catch (error) {
    console.error('モデル学習エラー:', error);
    return { error: 'モデルの学習中にエラーが発生しました' };
  }
});

// データ保存のIPC処理
ipcMain.handle('save-data', async (event, data) => {
  try {
    await waitForBackend();
    const response = await axios.post(`${BACKEND_URL}/api/data/import`, data);
    return response.data;
  } catch (error) {
    console.error('データ保存エラー:', error);
    return { error: 'データの保存中にエラーが発生しました', success: false };
  }
});

// データ読み込みのIPC処理
ipcMain.handle('load-data', async () => {
  try {
    await waitForBackend();
    const response = await axios.get(`${BACKEND_URL}/api/data`);
    return response.data;
  } catch (error) {
    console.error('データ読み込みエラー:', error);
    return { error: 'データの読み込み中にエラーが発生しました' };
  }
});

// 設定保存のIPC処理
ipcMain.handle('save-settings', async (event, data) => {
  try {
    await waitForBackend();
    const response = await axios.post(`${BACKEND_URL}/api/settings/save`, data);
    return response.data;
  } catch (error) {
    console.error('設定保存エラー:', error);
    return { error: '設定の保存中にエラーが発生しました' };
  }
});

// 新しいIPC処理を追加
ipcMain.handle('runPrediction', async (event, params) => {
  try {
    const response = await fetch('http://localhost:5003/api/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });
    return await response.json();
  } catch (error) {
    console.error('予測実行エラー:', error);
    throw error;
  }
}); 