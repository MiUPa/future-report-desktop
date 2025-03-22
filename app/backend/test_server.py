import requests
import sys
import time
import json

def test_api():
    """バックエンドAPIの機能をテストする"""
    base_url = "http://localhost:5000"
    
    # 接続テスト
    try:
        print("APIサーバーへの接続をテスト中...")
        response = requests.get(f"{base_url}/api/data")
        print(f"ステータスコード: {response.status_code}")
        if response.status_code == 200:
            print("データAPI接続成功！")
            data = response.json()
            print(f"返されたデータ件数: {len(data.get('salesData', []))}")
        else:
            print(f"データAPI接続失敗: {response.text}")
    except Exception as e:
        print(f"接続エラー: {e}")
        return False
    
    # サンプルCSVデータをインポート
    try:
        print("\nサンプルデータのインポートをテスト中...")
        sample_data = """日付,売上,特徴量
2024-01-01,1000,祝日
2024-01-02,900,通常営業
2024-01-03,950,通常営業"""
        
        response = requests.post(
            f"{base_url}/api/data/import",
            json={"csvContent": sample_data}
        )
        print(f"ステータスコード: {response.status_code}")
        if response.status_code == 200:
            print("データインポート成功！")
            result = response.json()
            print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"データインポート失敗: {response.text}")
    except Exception as e:
        print(f"インポートエラー: {e}")
    
    # 予測APIテスト
    try:
        print("\n予測APIをテスト中...")
        response = requests.post(
            f"{base_url}/api/predict",
            json={"period": 30}
        )
        print(f"ステータスコード: {response.status_code}")
        if response.status_code == 200:
            print("予測API成功！")
            result = response.json()
            print(f"予測総需要: {result.get('totalDemand')}")
            print(f"予測精度: {result.get('accuracy')}")
        else:
            print(f"予測API失敗: {response.text}")
    except Exception as e:
        print(f"予測エラー: {e}")
    
    return True

if __name__ == "__main__":
    print("バックエンドAPIテストを開始します...")
    # サーバーの起動を待機
    time.sleep(2)
    success = test_api()
    if success:
        print("\nテスト完了！")
    else:
        print("\nテスト失敗。サーバーが起動しているか確認してください。")
    sys.exit(0 if success else 1) 