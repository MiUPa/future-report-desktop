const { contextBridge, ipcRenderer } = require('electron');

// レンダラープロセスにAPIを公開
contextBridge.exposeInMainWorld('api', {
  // 需要予測を実行
  predictDemand: (data) => ipcRenderer.invoke('predict-demand', data),
  
  // モデルの再トレーニング
  trainModel: (data) => ipcRenderer.invoke('train-model', data),
  
  // データの保存
  saveData: (data) => ipcRenderer.invoke('save-data', data),
  
  // データの読み込み
  loadData: () => ipcRenderer.invoke('load-data'),
  
  // 設定の保存
  saveSettings: (data) => ipcRenderer.invoke('save-settings', data)
}); 