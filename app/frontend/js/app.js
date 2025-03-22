document.addEventListener('DOMContentLoaded', function() {
  // タブ切り替え機能
  const menuItems = document.querySelectorAll('.menu-item');
  const tabContents = document.querySelectorAll('.tab-content');
  
  menuItems.forEach(item => {
    item.addEventListener('click', function() {
      const tabId = this.getAttribute('data-tab');
      
      // アクティブなメニューアイテムを変更
      menuItems.forEach(i => i.classList.remove('active'));
      this.classList.add('active');
      
      // タブコンテンツを切り替え
      tabContents.forEach(tab => {
        if (tab.id === tabId + '-tab') {
          tab.classList.add('active');
        } else {
          tab.classList.remove('active');
        }
      });
    });
  });
  
  // 自動設定モードの切り替え処理（モデル学習タブ）
  const autoModeToggle = document.getElementById('auto-mode');
  const manualSettings = document.getElementById('manual-settings');
  const autoModeDescription = document.querySelector('.auto-mode-description');
  
  if (autoModeToggle) {
    autoModeToggle.addEventListener('change', function() {
      if (this.checked) {
        manualSettings.style.display = 'none';
        autoModeDescription.textContent = 'オン（データサイズに応じて最適なパラメータを自動設定します）';
      } else {
        manualSettings.style.display = 'block';
        autoModeDescription.textContent = 'オフ（手動でパラメータを設定します）';
      }
    });
  }
  
  // 自動設定モードの切り替え処理（設定タブ）
  const settingsAutoModeToggle = document.getElementById('settings-auto-mode');
  const settingsManual = document.getElementById('settings-manual');
  const settingsAutoModeDescription = document.querySelector('#settings-tab .auto-mode-description');
  
  if (settingsAutoModeToggle) {
    settingsAutoModeToggle.addEventListener('change', function() {
      if (this.checked) {
        settingsManual.style.display = 'none';
        settingsAutoModeDescription.textContent = 'オン（最適なパラメータを自動設定します）';
      } else {
        settingsManual.style.display = 'block';
        settingsAutoModeDescription.textContent = 'オフ（手動でパラメータを設定します）';
      }
    });
  }
  
  // 予測実行ボタンのイベントハンドラ
  const runPredictionBtn = document.getElementById('run-prediction');
  if (runPredictionBtn) {
    runPredictionBtn.addEventListener('click', runPrediction);
  }
  
  // データインポートボタンのイベントハンドラ
  const importDataBtn = document.getElementById('import-data');
  if (importDataBtn) {
    importDataBtn.addEventListener('click', importData);
  }
  
  // モデル学習ボタンのイベントハンドラ
  const trainModelBtn = document.getElementById('train-model');
  if (trainModelBtn) {
    trainModelBtn.addEventListener('click', trainModel);
  }
  
  // 設定保存ボタンのイベントハンドラ
  const saveSettingsBtn = document.getElementById('save-settings');
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', saveSettings);
  }
  
  // ツールチップをセットアップ
  setupTooltips();
  
  // 初期データロード
  loadInitialData();
});

// 初期データをロードする関数
async function loadInitialData() {
  try {
    const data = await window.api.loadData();
    if (data && data.salesData) {
      renderDataTable(data.salesData);
    }
  } catch (error) {
    console.error('データの読み込みに失敗しました:', error);
  }
}

// 需要予測を実行する関数
async function runPrediction() {
  try {
    // UI更新 - 予測中の状態を表示
    document.getElementById('run-prediction').disabled = true;
    document.getElementById('run-prediction').textContent = '予測中...';
    
    // 予測期間を取得
    const predictionPeriod = document.getElementById('prediction-period').value;
    
    // バックエンドに予測リクエストを送信
    const result = await window.api.predictDemand({
      period: parseInt(predictionPeriod)
    });
    
    // 結果を表示
    displayPredictionResults(result);
  } catch (error) {
    console.error('予測実行に失敗しました:', error);
    alert('予測の実行中にエラーが発生しました。');
  } finally {
    // UI状態を元に戻す
    document.getElementById('run-prediction').disabled = false;
    document.getElementById('run-prediction').textContent = '予測実行';
  }
}

// 予測結果を表示する関数
function displayPredictionResults(result) {
  // メトリクスを更新
  document.getElementById('total-demand').textContent = formatNumber(result.totalDemand);
  document.getElementById('yoy-change').textContent = formatPercentage(result.yearOverYearChange);
  document.getElementById('prediction-accuracy').textContent = formatPercentage(result.accuracy);
  
  // グラフを描画
  const ctx = document.getElementById('prediction-chart').getContext('2d');
  
  if (window.predictionChart) {
    window.predictionChart.destroy(); // 既存のチャートを破棄
  }
  
  // データを分離する - 実績データと予測データを分ける
  const allDates = result.dates;
  const historicalData = result.historicalData;
  const forecastData = result.forecastData;
  
  // 実績データと予測データを別々の配列に保持
  const historicalDates = [];
  const historicalValues = [];
  const forecastDates = [];
  const forecastValues = [];
  
  // 実績データが存在する日付を特定
  const lastHistoricalDataIndex = historicalData.findIndex(value => value === null || value === undefined);
  const lastHistoricalDate = lastHistoricalDataIndex !== -1 ? lastHistoricalDataIndex - 1 : historicalData.length - 1;
  
  // 実績データと予測データを分離
  for (let i = 0; i < allDates.length; i++) {
    if (i <= lastHistoricalDate) {
      historicalDates.push(allDates[i]);
      historicalValues.push(historicalData[i]);
    } else {
      forecastDates.push(allDates[i]);
      forecastValues.push(forecastData[i]);
    }
  }
  
  window.predictionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allDates,
      datasets: [
        {
          label: '実績',
          data: historicalData.map((value, index) => index <= lastHistoricalDate ? value : null),
          borderColor: '#4a6baf',
          backgroundColor: 'rgba(74, 107, 175, 0.1)',
          borderWidth: 2,
          pointRadius: 3,
          fill: true
        },
        {
          label: '予測',
          data: forecastData.map((value, index) => index > lastHistoricalDate ? value : null),
          borderColor: '#e9792b',
          backgroundColor: 'rgba(233, 121, 43, 0.1)',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 3,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        tooltip: {
          enabled: true
        },
        legend: {
          position: 'top'
        }
      }
    }
  });
}

// データをインポートする関数
async function importData() {
  const fileInput = document.getElementById('data-file');
  const file = fileInput.files[0];
  
  if (!file) {
    alert('ファイルを選択してください。');
    return;
  }
  
  try {
    const reader = new FileReader();
    reader.onload = async function(e) {
      const csvContent = e.target.result;
      
      // バックエンドにデータを送信
      const result = await window.api.saveData({
        csvContent: csvContent
      });
      
      if (result.success) {
        alert('データが正常にインポートされました。');
        renderDataTable(result.data);
      } else {
        alert('データのインポートに失敗しました。');
      }
    };
    reader.readAsText(file);
  } catch (error) {
    console.error('データインポートに失敗しました:', error);
    alert('データのインポート中にエラーが発生しました。');
  }
}

// データテーブルをレンダリングする関数
function renderDataTable(data) {
  const tableBody = document.querySelector('#data-table tbody');
  tableBody.innerHTML = '';
  
  data.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.date}</td>
      <td>${formatNumber(row.sales)}</td>
      <td>${row.features || '-'}</td>
    `;
    tableBody.appendChild(tr);
  });
}

// モデルを学習する関数
async function trainModel() {
  // 自動設定モードかどうかを確認
  const isAutoMode = document.getElementById('auto-mode').checked;
  
  // パラメータを取得
  let params = {};
  
  if (isAutoMode) {
    // 自動モードの場合は、自動設定フラグのみ送信
    params = {
      autoMode: true
    };
  } else {
    // 手動モードの場合は、ユーザー設定値を使用
    const epochs = document.getElementById('epochs').value;
    const batchSize = document.getElementById('batch-size').value;
    const modelType = document.getElementById('model-type').value;
    const hiddenLayers = document.getElementById('hidden-layers').value;
    const hiddenUnits = document.getElementById('hidden-units').value;
    
    // 値の検証
    if (epochs < 1 || batchSize < 1 || hiddenLayers < 1 || hiddenUnits < 1) {
      alert('すべての値は1以上で指定してください。');
      return;
    }
    
    params = {
      autoMode: false,
      epochs: parseInt(epochs),
      batchSize: parseInt(batchSize),
      modelType: modelType,
      hiddenLayers: parseInt(hiddenLayers),
      hiddenUnits: parseInt(hiddenUnits)
    };
  }
  
  try {
    // UI更新 - 学習中の状態を表示
    document.getElementById('train-model').disabled = true;
    document.getElementById('train-model').textContent = '学習中...';
    document.getElementById('training-status').textContent = '学習開始...';
    
    // 学習の進捗をモニタリングするイベントリスナーを設定
    const progressInterval = setInterval(() => {
      // 実際の実装では、進捗状況をバックエンドから取得する処理が必要
      // ここではデモとして進捗バーをランダムに更新
      const currentProgress = parseInt(document.getElementById('training-progress-bar').style.width || '0');
      if (currentProgress < 100) {
        const newProgress = Math.min(currentProgress + Math.random() * 10, 99);
        document.getElementById('training-progress-bar').style.width = `${newProgress}%`;
        document.getElementById('training-status').textContent = `学習中... ${Math.round(newProgress)}%`;
      }
    }, 1000);
    
    // バックエンドにトレーニングリクエストを送信
    const result = await window.api.trainModel(params);
    
    // 学習完了時の処理
    clearInterval(progressInterval);
    document.getElementById('training-progress-bar').style.width = '100%';
    document.getElementById('training-status').textContent = '学習完了！';
    
    setTimeout(() => {
      if (isAutoMode) {
        alert(`モデルの学習が完了しました。\n精度: ${formatPercentage(result.accuracy)}\n\n自動設定値: エポック数=${result.usedParams.epochs}, バッチサイズ=${result.usedParams.batchSize}, モデルタイプ=${result.usedParams.modelType}, 隠れ層数=${result.usedParams.hiddenLayers}`);
      } else {
        alert(`モデルの学習が完了しました。\n精度: ${formatPercentage(result.accuracy)}`);
      }
    }, 500);
  } catch (error) {
    console.error('モデル学習に失敗しました:', error);
    alert('モデルの学習中にエラーが発生しました。');
    document.getElementById('training-status').textContent = 'エラーが発生しました';
  } finally {
    // UI状態を元に戻す
    document.getElementById('train-model').disabled = false;
    document.getElementById('train-model').textContent = 'モデル学習開始';
  }
}

// 設定を保存する関数
async function saveSettings() {
  // 自動設定モードかどうかを確認
  const isAutoMode = document.getElementById('settings-auto-mode').checked;
  
  let params = {};
  
  if (isAutoMode) {
    // 自動モードの場合は、自動設定フラグのみ送信
    params = {
      autoMode: true
    };
  } else {
    // 手動モードの場合は、ユーザー設定値を使用
    const modelType = document.getElementById('model-type').value;
    const hiddenLayers = document.getElementById('hidden-layers').value;
    const hiddenUnits = document.getElementById('hidden-units').value;
    
    // 値の検証
    if (hiddenLayers < 1 || hiddenUnits < 1) {
      alert('すべての値は1以上で指定してください。');
      return;
    }
    
    params = {
      autoMode: false,
      modelType: modelType,
      hiddenLayers: parseInt(hiddenLayers),
      hiddenUnits: parseInt(hiddenUnits)
    };
  }
  
  try {
    await window.api.saveSettings(params);
    
    if (isAutoMode) {
      alert('自動設定モードが有効になりました。データサイズに基づいて最適なパラメータが使用されます。');
    } else {
      alert('設定が保存されました。');
    }
  } catch (error) {
    console.error('設定の保存に失敗しました:', error);
    alert('設定の保存中にエラーが発生しました。');
  }
}

// ユーティリティ関数 - 数値のフォーマット
function formatNumber(num) {
  return new Intl.NumberFormat('ja-JP').format(num);
}

// ユーティリティ関数 - パーセンテージのフォーマット
function formatPercentage(num) {
  return new Intl.NumberFormat('ja-JP', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(num / 100);
}

// ツールチップを表示する関数
function showTooltip(element, message) {
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  tooltip.textContent = message;
  
  // 要素の位置を取得
  const rect = element.getBoundingClientRect();
  
  // ツールチップの位置を設定
  tooltip.style.top = `${rect.bottom + 5}px`;
  tooltip.style.left = `${rect.left + (rect.width / 2) - 100}px`;
  
  document.body.appendChild(tooltip);
  
  // 3秒後にツールチップを削除
  setTimeout(() => {
    if (tooltip.parentNode) {
      tooltip.parentNode.removeChild(tooltip);
    }
  }, 3000);
}

// ツールチップをセットアップする関数
function setupTooltips() {
  // 予測期間のツールチップ
  const predictionPeriod = document.getElementById('prediction-period');
  if (predictionPeriod) {
    predictionPeriod.addEventListener('mouseover', () => {
      showTooltip(predictionPeriod, '予測する将来の期間を選択します');
    });
  }
  
  // 予測実行ボタンのツールチップ
  const runPredictionBtn = document.getElementById('run-prediction');
  if (runPredictionBtn) {
    runPredictionBtn.addEventListener('mouseover', () => {
      showTooltip(runPredictionBtn, '選択した期間の需要予測を実行します');
    });
  }
  
  // データファイル選択のツールチップ
  const dataFile = document.getElementById('data-file');
  if (dataFile) {
    dataFile.addEventListener('mouseover', () => {
      showTooltip(dataFile, 'CSVファイル形式のデータをインポートします。日付,売上,特徴量(オプション)の列が必要です。');
    });
  }
  
  // インポートボタンのツールチップ
  const importDataBtn = document.getElementById('import-data');
  if (importDataBtn) {
    importDataBtn.addEventListener('mouseover', () => {
      showTooltip(importDataBtn, '選択したCSVファイルをインポートします');
    });
  }
  
  // 自動設定モードスイッチのツールチップ
  const autoMode = document.getElementById('auto-mode');
  if (autoMode) {
    autoMode.parentElement.addEventListener('mouseover', () => {
      showTooltip(autoMode.parentElement, 'オンにすると、データサイズに応じて最適なパラメータが自動的に設定されます');
    });
  }
  
  // モデル学習ボタンのツールチップ
  const trainModelBtn = document.getElementById('train-model');
  if (trainModelBtn) {
    trainModelBtn.addEventListener('mouseover', () => {
      showTooltip(trainModelBtn, '予測モデルの学習を開始します');
    });
  }
  
  // 設定の自動モードスイッチのツールチップ
  const settingsAutoMode = document.getElementById('settings-auto-mode');
  if (settingsAutoMode) {
    settingsAutoMode.parentElement.addEventListener('mouseover', () => {
      showTooltip(settingsAutoMode.parentElement, 'オンにすると、全体の設定が自動的に最適化されます');
    });
  }
  
  // 設定保存ボタンのツールチップ
  const saveSettingsBtn = document.getElementById('save-settings');
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('mouseover', () => {
      showTooltip(saveSettingsBtn, '設定を保存します');
    });
  }
} 