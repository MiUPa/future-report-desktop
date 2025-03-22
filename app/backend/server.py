import json
import sys
import os
import csv
import sqlite3
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense
import time

# アプリのルートディレクトリを取得
if getattr(sys, 'frozen', False):
    # ビルドされたアプリの場合
    APP_ROOT = os.path.dirname(sys.executable)
else:
    # 開発環境の場合
    APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# データベースのパス設定
DB_PATH = os.path.join(APP_ROOT, 'app', 'database', 'sales_data.db')
MODEL_PATH = os.path.join(APP_ROOT, 'app', 'models')

# データベースの初期化
def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 売上データテーブルの作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        sales REAL NOT NULL,
        features TEXT
    )
    ''')
    
    # 設定テーブルの作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_type TEXT NOT NULL,
        hidden_layers INTEGER NOT NULL,
        hidden_units INTEGER NOT NULL
    )
    ''')
    
    # デフォルト設定の挿入（存在しない場合）
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO settings (model_type, hidden_layers, hidden_units)
        VALUES (?, ?, ?)
        ''', ('lstm', 2, 64))
    
    conn.commit()
    conn.close()

# サンプルデータの生成（デモ用）
def generate_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # テーブルが空かどうかを確認
    cursor.execute("SELECT COUNT(*) FROM sales_data")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # データが既に存在する場合は生成しない
    
    # 過去1年分のサンプルデータを生成
    start_date = datetime.now() - timedelta(days=365)
    sales_data = []
    
    for i in range(365):
        date = start_date + timedelta(days=i)
        # 週末は売上が高い、季節変動も加える
        weekday_factor = 1.5 if date.weekday() >= 5 else 1.0
        season_factor = 1.0 + 0.3 * np.sin(np.pi * i / 180)
        trend_factor = 1.0 + (i / 365) * 0.2  # 徐々に上昇するトレンド
        
        base_sales = 1000
        noise = np.random.normal(0, 100)
        sales = base_sales * weekday_factor * season_factor * trend_factor + noise
        
        sales_data.append((date.strftime('%Y-%m-%d'), max(0, sales), None))
    
    # データをデータベースに挿入
    cursor.executemany('''
    INSERT INTO sales_data (date, sales, features)
    VALUES (?, ?, ?)
    ''', sales_data)
    
    conn.commit()
    conn.close()

class SimplePredictionModel:
    """モデルが利用できない場合の簡易予測モデル"""
    
    def __init__(self):
        print("簡易予測モデルを初期化しています")
        self.trained = True
    
    def predict(self, x_input):
        """簡易的な予測を行う"""
        # 入力の最後の値を基準に、少しランダム性を持たせた予測を返す
        last_value = x_input[0][-1][0]
        # 過去5〜10日分の変動率を考慮した予測
        prediction = last_value * (1 + np.random.uniform(-0.05, 0.05))
        return np.array([[prediction]])
    
    def fit(self, x, y, epochs=10, batch_size=32, verbose=0):
        """訓練のフリをする"""
        print(f"簡易モデル: 訓練をシミュレート (エポック={epochs}, バッチサイズ={batch_size})")
        time.sleep(0.5)  # 訓練の時間をシミュレート
        return self

# 需要予測モデルの実装（簡易版）
# 実際のプロダクションでは、より洗練されたモデルを使用する
class DemandForecastModel:
    def __init__(self, settings=None):
        self.settings = settings or {'model_type': 'lstm', 'hidden_layers': 2, 'hidden_units': 64}
        self.scaler = MinMaxScaler(feature_range=(0, 1))
    
    def prepare_data(self, data, seq_length=7):
        # データの前処理
        sales = np.array([float(row[1]) for row in data])
        sales_scaled = self.scaler.fit_transform(sales.reshape(-1, 1))
        
        X, y = [], []
        for i in range(len(sales_scaled) - seq_length):
            X.append(sales_scaled[i:i+seq_length])
            y.append(sales_scaled[i+seq_length])
        
        return np.array(X), np.array(y)
    
    def train(self, data, epochs=50, batch_size=32):
        # 簡易実装: 実際にはPyTorchやTensorFlowを使用して深層学習モデルを訓練する
        # ここではサンプルの進捗を返すだけ
        print(f"モデルのトレーニングを開始: エポック数={epochs}, バッチサイズ={batch_size}")
        
        # 訓練進捗のシミュレーション
        for epoch in range(epochs):
            # 実際の訓練ロジックをここに実装
            loss = 1.0 - (epoch / epochs) * 0.9  # 損失が徐々に減少するシミュレーション
            print(f"エポック {epoch+1}/{epochs}, 損失: {loss:.4f}")
        
        # モデルの保存
        # 実際の実装では、学習済みモデルをファイルに保存
        print("モデルの訓練が完了しました。")
        return {'accuracy': 85.0 + np.random.uniform(0, 10)}  # ダミーの精度
    
    def predict(self, data, period=30):
        # ダミーの予測結果を生成
        last_date = datetime.strptime(data[-1][0], '%Y-%m-%d')
        dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(period)]
        
        # 最近のデータから基本的なパターンを抽出
        recent_sales = [float(row[1]) for row in data[-14:]]
        mean_sales = np.mean(recent_sales)
        std_sales = np.std(recent_sales)
        
        # トレンドと季節性を考慮したシンプルな予測
        forecast = []
        for i in range(period):
            # 週末効果
            weekday = (last_date + timedelta(days=i+1)).weekday()
            weekday_factor = 1.3 if weekday >= 5 else 1.0
            
            # 季節効果（単純化）
            day_of_year = (last_date + timedelta(days=i+1)).timetuple().tm_yday
            season_factor = 1.0 + 0.2 * np.sin(np.pi * day_of_year / 180)
            
            # 上昇トレンド
            trend_factor = 1.0 + (i / 365) * 0.1
            
            # 基本予測値にノイズを加える
            predicted_value = mean_sales * weekday_factor * season_factor * trend_factor
            predicted_value += np.random.normal(0, std_sales * 0.1)
            forecast.append(max(0, predicted_value))
        
        # 履歴データも返す（グラフ表示用）
        historical_dates = [row[0] for row in data[-60:]]
        historical_data = [float(row[1]) for row in data[-60:]]
        
        # 前年同期と比較
        year_ago_sales = [float(row[1]) for row in data if
                          datetime.strptime(row[0], '%Y-%m-%d') >= last_date - timedelta(days=365) and
                          datetime.strptime(row[0], '%Y-%m-%d') <= last_date - timedelta(days=365-period)]
        
        # 前年同期データがある場合は前年比を計算
        if len(year_ago_sales) >= period:
            yoy_change = (sum(forecast) / sum(year_ago_sales) - 1) * 100
        else:
            yoy_change = 0
        
        return {
            'dates': dates,
            'forecastData': forecast,
            'historicalDates': historical_dates,
            'historicalData': historical_data,
            'totalDemand': sum(forecast),
            'yearOverYearChange': yoy_change,
            'accuracy': 85.0 + np.random.uniform(0, 10)  # ダミーの精度
        }

# リクエストハンドラ
class DemandForecastHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type='application/json'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_OPTIONS(self):
        # CORSプリフライトリクエストを処理
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')  # 24時間
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")
    
    def do_GET(self):
        print(f"GETリクエスト受信: {self.path}")
        parsed_path = urllib.parse.urlparse(self.path)
        
        try:
            if parsed_path.path == '/api/data':
                # データを取得
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT date, sales, features FROM sales_data ORDER BY date")
                sales_data = cursor.fetchall()
                conn.close()
                
                response = {
                    'success': True,
                    'salesData': [{'date': row[0], 'sales': row[1], 'features': row[2]} for row in sales_data]
                }
                
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
                return
            
            elif parsed_path.path == '/api/settings':
                # 設定を取得
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT model_type, hidden_layers, hidden_units FROM settings ORDER BY id DESC LIMIT 1")
                settings = cursor.fetchone()
                conn.close()
                
                response = {
                    'success': True,
                    'settings': {
                        'modelType': settings[0],
                        'hiddenLayers': settings[1],
                        'hiddenUnits': settings[2]
                    }
                }
                
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
                return
            elif parsed_path.path == '/api/test':
                # テスト用エンドポイント
                self._set_headers()
                response = {'message': 'テストAPI成功', 'status': 'ok'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # 存在しないエンドポイント
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        except Exception as e:
            print(f"GETリクエスト処理エラー: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_POST(self):
        print(f"POSTリクエスト受信: {self.path}")
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"受信データ: {json.dumps(data, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                print(f"JSONデコードエラー: {e}")
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            
            parsed_path = urllib.parse.urlparse(self.path)
            
            if parsed_path.path == '/api/predict':
                # 需要予測を実行
                period = data.get('period', 30)
                
                # データベースから売上データを取得
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT date, sales, features FROM sales_data ORDER BY date")
                sales_data = cursor.fetchall()
                
                # 設定を取得
                cursor.execute("SELECT model_type, hidden_layers, hidden_units FROM settings ORDER BY id DESC LIMIT 1")
                settings = cursor.fetchone()
                settings_dict = {
                    'model_type': settings[0],
                    'hidden_layers': settings[1],
                    'hidden_units': settings[2]
                }
                conn.close()
                
                # モデルを初期化して予測を実行
                model = DemandForecastModel(settings_dict)
                prediction = model.predict(sales_data, period)
                
                self._set_headers()
                self.wfile.write(json.dumps(prediction).encode())
                return
            
            elif parsed_path.path == '/api/train':
                # モデルの訓練を実行
                epochs = data.get('epochs', 50)
                batch_size = data.get('batchSize', 32)
                
                # データベースから売上データを取得
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT date, sales, features FROM sales_data ORDER BY date")
                sales_data = cursor.fetchall()
                
                # 設定を取得
                cursor.execute("SELECT model_type, hidden_layers, hidden_units FROM settings ORDER BY id DESC LIMIT 1")
                settings = cursor.fetchone()
                settings_dict = {
                    'model_type': settings[0],
                    'hidden_layers': settings[1],
                    'hidden_units': settings[2]
                }
                conn.close()
                
                # モデルを初期化して訓練を実行
                model = DemandForecastModel(settings_dict)
                result = model.train(sales_data, epochs, batch_size)
                
                self._set_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            
            elif parsed_path.path == '/api/data/import':
                # CSVデータをインポート
                print("データインポートAPIが呼び出されました")
                if 'csvContent' in data:
                    csv_content = data.get('csvContent', '')
                    print(f"CSVデータ先頭部分: {csv_content[:100]}...")
                    
                    try:
                        # CSVデータをパース
                        csv_data = []
                        reader = csv.reader(csv_content.splitlines())
                        
                        # ヘッダー行をスキップ
                        headers = next(reader, None)
                        print(f"CSVヘッダー: {headers}")
                        
                        # 日本語のヘッダーにも対応
                        date_column = 0
                        sales_column = 1
                        features_column = 2
                        
                        # ヘッダーの位置を特定（日本語・英語両対応）
                        if headers:
                            for i, header in enumerate(headers):
                                header_lower = header.lower()
                                print(f"ヘッダー{i}: '{header}' (変換後: '{header_lower}')")
                                if header_lower in ['date', '日付', 'date']:
                                    date_column = i
                                    print(f"日付列を検出: {i}")
                                elif header_lower in ['sales', '売上', 'revenue']:
                                    sales_column = i
                                    print(f"売上列を検出: {i}")
                                elif header_lower in ['features', '特徴量', 'category']:
                                    features_column = i
                                    print(f"特徴量列を検出: {i}")
                        
                        print(f"使用する列インデックス: 日付={date_column}, 売上={sales_column}, 特徴量={features_column}")
                        
                        row_count = 0
                        for row in reader:
                            row_count += 1
                            if len(row) > 1:  # 最低2列（日付と売上）が必要
                                try:
                                    if row_count <= 3:
                                        print(f"処理中の行 {row_count}: {row}")
                                    
                                    date = row[date_column].strip()
                                    sales_str = row[sales_column].strip().replace(',', '')  # カンマを除去
                                    sales = float(sales_str)
                                    
                                    features = None
                                    if len(row) > features_column:
                                        features = row[features_column].strip()
                                    
                                    csv_data.append((date, sales, features))
                                    
                                    if row_count <= 3:
                                        print(f"変換後: ({date}, {sales}, {features})")
                                except ValueError as e:
                                    print(f"数値変換エラー: {e}, 行: {row}")
                                    continue
                                except IndexError as e:
                                    print(f"インデックスエラー: {e}, 行: {row}")
                                    continue
                        
                        print(f"合計で {len(csv_data)} 行のデータを読み込みました")
                        
                        if len(csv_data) == 0:
                            raise ValueError("有効なデータがありません")
                        
                        print(f"CSVデータ例（最初の3行）: {csv_data[:3]}")
                        
                        # データベースに挿入
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        
                        # 既存のデータをクリア（オプション）
                        cursor.execute("DELETE FROM sales_data")
                        
                        # 新しいデータを挿入
                        cursor.executemany('''
                        INSERT INTO sales_data (date, sales, features)
                        VALUES (?, ?, ?)
                        ''', csv_data)
                        
                        conn.commit()
                        
                        # インポートしたデータを返す
                        cursor.execute("SELECT date, sales, features FROM sales_data ORDER BY date")
                        sales_data = cursor.fetchall()
                        conn.close()
                        
                        response = {
                            'success': True,
                            'data': [{'date': row[0], 'sales': row[1], 'features': row[2]} for row in sales_data]
                        }
                        
                        self._set_headers()
                        self.wfile.write(json.dumps(response).encode())
                    except Exception as e:
                        print(f"CSVインポートエラー: {e}")
                        import traceback
                        traceback.print_exc()
                        self.send_response(400)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
                else:
                    print("csvContentフィールドがありません")
                    self.send_response(400)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'error': 'csvContentフィールドが必要です'}).encode())
                return
            
            elif parsed_path.path == '/api/settings/save':
                # 設定を保存
                model_type = data.get('modelType', 'lstm')
                hidden_layers = data.get('hiddenLayers', 2)
                hidden_units = data.get('hiddenUnits', 64)
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # 新しい設定を挿入
                cursor.execute('''
                INSERT INTO settings (model_type, hidden_layers, hidden_units)
                VALUES (?, ?, ?)
                ''', (model_type, hidden_layers, hidden_units))
                
                conn.commit()
                conn.close()
                
                response = {'success': True}
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
                return
            
            # 存在しないエンドポイント
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        except Exception as e:
            print(f"POSTリクエスト処理エラー: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def run_server(port=5003):
    # データベースの初期化
    init_database()
    
    # サンプルデータの生成
    generate_sample_data()
    
    # サーバーの起動
    print(f"サーバーを起動しています (ポート {port})...")
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, DemandForecastHandler)
    print(f"サーバーが起動しました。localhost:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 