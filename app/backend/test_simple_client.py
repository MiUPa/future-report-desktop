import requests
import json
import time

def test_connection():
    """サーバー接続テスト"""
    try:
        print("接続テスト開始...")
        response = requests.get('http://localhost:5002/api/test', timeout=10)
        print(f"接続テスト: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"接続エラー: {e}")
        return False

def test_data_api():
    """データAPI取得テスト"""
    try:
        print("データAPI取得テスト開始...")
        response = requests.get('http://localhost:5002/api/data', timeout=10)
        print(f"データAPI: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"データAPI取得エラー: {e}")
        return False

def test_import_api():
    """データインポートAPIテスト"""
    try:
        print("データインポートAPIテスト開始...")
        test_data = {
            'csvContent': "date,sales,features\n2024-01-01,1000,holiday\n2024-01-02,900,normal\n2024-01-03,950,normal"
        }
        response = requests.post(
            'http://localhost:5002/api/data/import',
            data=json.dumps(test_data),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"インポートAPI: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"インポートAPIエラー: {e}")
        return False

def test_predict_api():
    """予測APIテスト"""
    try:
        print("予測APIテスト開始...")
        predict_data = {
            'period': 30
        }
        response = requests.post(
            'http://localhost:5002/api/predict',
            data=json.dumps(predict_data),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"予測API: {response.status_code}")
        print(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"予測APIエラー: {e}")
        return False

if __name__ == "__main__":
    print("シンプルなサーバーAPIテスト開始")
    
    # サーバーが起動するまで少し待機
    time.sleep(3)
    
    # 各テストを実行
    connection_success = test_connection()
    time.sleep(1)
    
    data_success = test_data_api()
    time.sleep(1)
    
    import_success = test_import_api()
    time.sleep(1)
    
    predict_success = test_predict_api()
    
    # 結果表示
    print("\nテスト結果:")
    print(f"接続テスト: {'成功' if connection_success else '失敗'}")
    print(f"データAPI: {'成功' if data_success else '失敗'}")
    print(f"インポートAPI: {'成功' if import_success else '失敗'}")
    print(f"予測API: {'成功' if predict_success else '失敗'}")
    
    if all([connection_success, data_success, import_success, predict_success]):
        print("\n全テスト成功！サーバーは正常に動作しています。")
    else:
        print("\n一部のテストが失敗しました。サーバー設定を確認してください。") 