# 需要予測デスクトップアプリ (Future Report Desktop)

深層学習を使用してローカル環境で動作する需要予測デスクトップアプリケーションです。過去の売上データから将来の需要を予測し、ビジネスの意思決定をサポートします。

## 機能

- 過去の売上データから深層学習（LSTM）を使用して将来の需要を予測
- Mac、Windowsで動作するクロスプラットフォームアプリケーション
- ローカル環境で完結（インターネット接続不要）
- 過去の売上と暦から、次の1ヶ月の需要を予測
- データを追加投入して、AIモデルに追加学習させることが可能
- カスタマイズ可能なモデル設定（レイヤー数、ユニット数など）

## インストール方法

### 事前準備

- [Node.js](https://nodejs.org/) (v14以上)
- [Python](https://www.python.org/) (v3.8以上)

### インストール手順

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/future-report-desktop.git
cd future-report-desktop
```

2. 必要なNode.jsパッケージをインストール
```bash
npm install
```

3. 必要なPythonパッケージをインストール
```bash
pip install -r requirements.txt
```

## 使い方

### アプリケーションの起動

開発モードで起動:
```bash
npm run dev
```

通常モードで起動:
```bash
npm start
```

### データのインポート

1. 「データ管理」タブを選択
2. CSVファイルを選択（フォーマット: 日付,売上,特徴量）
3. 「インポート」ボタンをクリック

### モデルの学習

1. 「モデル学習」タブを選択
2. エポック数とバッチサイズを設定
3. 「モデル学習開始」ボタンをクリック

### 需要予測の実行

1. 「需要予測」タブを選択
2. 予測期間を選択
3. 「予測実行」ボタンをクリック

## ビルド方法

### Macアプリとしてビルド
```bash
npm run build:mac
```

### Windowsアプリとしてビルド
```bash
npm run build:win
```

ビルドされたアプリケーションは `dist` ディレクトリに生成されます。

## 技術スタック

- フロントエンド: HTML/CSS/JavaScript
- バックエンド: Python
- デスクトップフレームワーク: Electron
- 深層学習フレームワーク: PyTorch
- データベース: SQLite

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 貢献

バグレポートや機能リクエストは、Issueトラッカーを使用してください。プルリクエストも歓迎します。 