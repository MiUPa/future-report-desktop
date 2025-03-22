from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        print(f"GETリクエスト受信: {self.path}")
        
        if self.path == '/api/test':
            self._set_headers()
            response = {'message': 'テストAPI成功', 'status': 'ok'}
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/api/data':
            self._set_headers()
            response = {
                'success': True,
                'salesData': [
                    {'date': '2024-01-01', 'sales': 1000, 'features': '祝日'},
                    {'date': '2024-01-02', 'sales': 900, 'features': '通常営業'},
                    {'date': '2024-01-03', 'sales': 950, 'features': '通常営業'}
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        print(f"POSTリクエスト受信: {self.path}")
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/api/data/import':
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"受信データ: {data}")
                
                self._set_headers()
                response = {
                    'success': True,
                    'message': 'データが正常にインポートされました',
                    'data': [
                        {'date': '2024-01-01', 'sales': 1000, 'features': '祝日'},
                        {'date': '2024-01-02', 'sales': 900, 'features': '通常営業'},
                        {'date': '2024-01-03', 'sales': 950, 'features': '通常営業'}
                    ]
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                print(f"エラー: {e}")
                self.send_response(400)
                self.end_headers()
        elif self.path == '/api/predict':
            self._set_headers()
            response = {
                'dates': ['2024-02-01', '2024-02-02', '2024-02-03'],
                'forecastData': [1050, 950, 1000],
                'historicalData': [1000, 900, 950],
                'totalDemand': 3000,
                'yearOverYearChange': 5.2,
                'accuracy': 92.5
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run(port=5001):
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"サーバーを起動しています (ポート {port})...")
    print(f"テストAPI: http://localhost:{port}/api/test")
    print(f"データAPI: http://localhost:{port}/api/data")
    httpd.serve_forever()

if __name__ == '__main__':
    run() 