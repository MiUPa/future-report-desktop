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
  
  window.predictionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: result.dates,
      datasets: [
        {
          label: '実績',
          data: result.historicalData,
          borderColor: '#4a6baf',
          backgroundColor: 'rgba(74, 107, 175, 0.1)',
          borderWidth: 2,
          pointRadius: 3,
          fill: true
        },
        {
          label: '予測',
          data: result.forecastData,
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
  const epochs = document.getElementById('epochs').value;
  const batchSize = document.getElementById('batch-size').value;
  
  // 値の検証
  if (epochs < 1 || batchSize < 1) {
    alert('エポック数とバッチサイズは1以上の値を指定してください。');
    return;
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
    const result = await window.api.trainModel({
      epochs: parseInt(epochs),
      batchSize: parseInt(batchSize)
    });
    
    // 学習完了時の処理
    clearInterval(progressInterval);
    document.getElementById('training-progress-bar').style.width = '100%';
    document.getElementById('training-status').textContent = '学習完了！';
    
    setTimeout(() => {
      alert(`モデルの学習が完了しました。\n精度: ${formatPercentage(result.accuracy)}`);
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
  const modelType = document.getElementById('model-type').value;
  const hiddenLayers = document.getElementById('hidden-layers').value;
  const hiddenUnits = document.getElementById('hidden-units').value;
  
  try {
    await window.api.saveSettings({
      modelType,
      hiddenLayers: parseInt(hiddenLayers),
      hiddenUnits: parseInt(hiddenUnits)
    });
    
    alert('設定が保存されました。');
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