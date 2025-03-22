import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
import json
from datetime import datetime

class LSTMForecastModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1):
        super(LSTMForecastModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM層
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        # 全結合層
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        # LSTMの初期隠れ状態を初期化
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # LSTM層に入力を渡す
        out, _ = self.lstm(x, (h0, c0))
        
        # 最後のタイムステップの出力のみを使用
        out = self.fc(out[:, -1, :])
        return out

class DemandForecaster:
    def __init__(self, model_path=None, config=None):
        """需要予測器の初期化"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # デフォルト設定
        self.config = {
            'model_type': 'lstm',
            'hidden_layers': 2,
            'hidden_units': 64,
            'sequence_length': 7,  # 何日分のデータを見て予測するか
            'learning_rate': 0.001,
            'batch_size': 32
        }
        
        # 設定を更新（指定された場合）
        if config:
            self.config.update(config)
        
        # モデルの作成
        self.model = LSTMForecastModel(
            input_size=1,
            hidden_size=self.config['hidden_units'],
            num_layers=self.config['hidden_layers'],
            output_size=1
        ).to(self.device)
        
        # 既存のモデルを読み込む
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def prepare_data(self, sales_data, sequence_length=None):
        """時系列データを学習用にシーケンスに変換"""
        if sequence_length is None:
            sequence_length = self.config['sequence_length']
        
        # 売上データを抽出して正規化
        sales = np.array([float(row[1]) for row in sales_data]).reshape(-1, 1)
        sales_scaled = self.scaler.fit_transform(sales)
        
        X, y = [], []
        for i in range(len(sales_scaled) - sequence_length):
            X.append(sales_scaled[i:i+sequence_length])
            y.append(sales_scaled[i+sequence_length])
        
        # Numpy配列をPyTorchテンソルに変換
        X_tensor = torch.FloatTensor(np.array(X)).to(self.device)
        y_tensor = torch.FloatTensor(np.array(y)).to(self.device)
        
        return X_tensor, y_tensor
    
    def train(self, sales_data, epochs=50, batch_size=None, learning_rate=None, callback=None):
        """モデルを訓練"""
        if batch_size is None:
            batch_size = self.config['batch_size']
        if learning_rate is None:
            learning_rate = self.config['learning_rate']
        
        # データの準備
        X, y = self.prepare_data(sales_data)
        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # 損失関数と最適化器の設定
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # 訓練ループ
        self.model.train()
        epoch_losses = []
        
        for epoch in range(epochs):
            total_loss = 0
            
            for batch_X, batch_y in dataloader:
                # 勾配をリセット
                optimizer.zero_grad()
                
                # 順伝播
                outputs = self.model(batch_X)
                
                # 損失の計算
                loss = criterion(outputs, batch_y)
                total_loss += loss.item()
                
                # 逆伝播と最適化
                loss.backward()
                optimizer.step()
            
            # エポックごとの平均損失
            avg_loss = total_loss / len(dataloader)
            epoch_losses.append(avg_loss)
            
            # コールバック関数があれば呼び出し
            if callback:
                callback(epoch, epochs, avg_loss)
            
            print(f"エポック {epoch+1}/{epochs}, 損失: {avg_loss:.4f}")
        
        # 最終的な精度を評価
        accuracy = self._evaluate(X, y)
        
        return {
            'accuracy': accuracy,
            'epoch_losses': epoch_losses
        }
    
    def _evaluate(self, X, y):
        """モデルの精度を評価"""
        self.model.eval()
        with torch.no_grad():
            predictions = self.model(X)
            # スケールを元に戻す
            y_true = self.scaler.inverse_transform(y.cpu().numpy())
            y_pred = self.scaler.inverse_transform(predictions.cpu().numpy())
            
            # 平均絶対誤差率（MAPE）を計算
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            accuracy = 100 - mape  # 精度に変換（単純化）
        
        return max(0, min(100, accuracy))  # 0-100の範囲に制限
    
    def predict(self, sales_data, prediction_days=30):
        """将来の需要を予測"""
        self.model.eval()
        
        # 最新のデータを取得
        latest_sequence = np.array([float(row[1]) for row in sales_data[-self.config['sequence_length']:]])
        
        # データの正規化
        latest_sequence_scaled = self.scaler.transform(latest_sequence.reshape(-1, 1))
        
        # 予測結果
        predictions = []
        current_sequence = latest_sequence_scaled.flatten()
        
        with torch.no_grad():
            for _ in range(prediction_days):
                # 現在のシーケンスから次の値を予測
                x = torch.FloatTensor(current_sequence[-self.config['sequence_length']:].reshape(1, -1, 1)).to(self.device)
                predicted = self.model(x)
                
                # 予測値をリストに追加
                predictions.append(predicted.cpu().numpy()[0, 0])
                
                # シーケンスを更新
                current_sequence = np.append(current_sequence, predicted.cpu().numpy()[0, 0])
        
        # スケールを元に戻す
        predictions_rescaled = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1))
        
        return predictions_rescaled.flatten()
    
    def save_model(self, model_path):
        """モデルを保存"""
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        model_state = {
            'model_state_dict': self.model.state_dict(),
            'config': self.config,
            'scaler_params': {
                'scale_': self.scaler.scale_.tolist(),
                'min_': self.scaler.min_.tolist(),
                'data_min_': self.scaler.data_min_.tolist(),
                'data_max_': self.scaler.data_max_.tolist(),
                'data_range_': self.scaler.data_range_.tolist()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        torch.save(model_state, model_path)
        print(f"モデルが保存されました: {model_path}")
    
    def load_model(self, model_path):
        """保存されたモデルを読み込む"""
        try:
            model_state = torch.load(model_path, map_location=self.device)
            
            # モデル設定を更新
            self.config = model_state['config']
            
            # モデル構造を再構築
            self.model = LSTMForecastModel(
                input_size=1,
                hidden_size=self.config['hidden_units'],
                num_layers=self.config['hidden_layers'],
                output_size=1
            ).to(self.device)
            
            # モデルパラメータを読み込み
            self.model.load_state_dict(model_state['model_state_dict'])
            
            # スケーラーパラメータを復元
            scaler_params = model_state['scaler_params']
            self.scaler.scale_ = np.array(scaler_params['scale_'])
            self.scaler.min_ = np.array(scaler_params['min_'])
            self.scaler.data_min_ = np.array(scaler_params['data_min_'])
            self.scaler.data_max_ = np.array(scaler_params['data_max_'])
            self.scaler.data_range_ = np.array(scaler_params['data_range_'])
            
            print(f"モデルが読み込まれました: {model_path}")
            return True
        except Exception as e:
            print(f"モデルの読み込みに失敗しました: {e}")
            return False 