# Triathlon Sensor Data Feedback System

トライアスロン競技用センサーデータフィードバックシステム

## 🎯 プロジェクト概要

このシステムは、トライアスロン競技中のセンサーデータ（体表温度、カプセル体温、心拍数、WBGT値）を収集・分析し、競技者に対してリアルタイムでフィードバックを提供するWebアプリケーションです。

## ✅ 新機能：フィードバックグラフ

### 🎨 仕様書準拠の高度なグラフ機能

**✨ 主要機能:**
- **双軸グラフ**: 温度（左軸）と心拍数（右軸）の同時表示
- **競技区間背景色**: Swim（水色）/ Bike（橙色）/ Run（黄緑色）
- **時間範囲設定**: 競技開始〜終了 + オフセット機能（前後0-30分）
- **大会選択**: 複数大会参加時の選択UI
- **データ欠損対応**: 自動補完とエラーハンドリング

**📊 表示データ:**
- 体表温度（halshare センサー）
- カプセル体温（e-Celcius センサー）
- 心拍数（Garmin データ）
- WBGT環境温度

**🎛️ 利用可能場所:**
- 一般ユーザー: マイダッシュボード
- 管理者: ユーザーデータ詳細画面

## 🛠️ 技術構成

### フロントエンド
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Charts**: Chart.js + React Chart.js 2
- **State Management**: React Hooks + Custom Hooks
- **HTTP Client**: Fetch API

### バックエンド
- **Framework**: FastAPI (Python)
- **Database**: SQLAlchemy + PostgreSQL/SQLite
- **Authentication**: JWT Token
- **Data Processing**: Pandas + NumPy
- **File Upload**: Multipart Form Data

## 🚀 セットアップ・起動

### 1. バックエンド起動

```bash
cd triathlon-backend
pip install -r requirements.txt
python setup_database.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. フロントエンド起動

```bash
cd triathlon-frontend
npm install
npm run dev
```

### 3. アクセス

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 初期アカウント

**管理者**
- Username: `admin`
- Password: `admin123`

**テストユーザー**
- Username: `testuser1`
- Password: `password123`

## 📊 フィードバックグラフ使用方法

### 一般ユーザー

1. ログイン後、マイダッシュボードにアクセス
2. 「トライアスロン フィードバックグラフ」セクションで大会を選択
3. オフセット時間を調整（前後0-30分）
4. センサーデータと競技区間を確認

### 管理者

1. 管理者でログイン
2. ユーザー管理 → 対象ユーザーの詳細
3. 「📊 グラフ表示」ボタンをクリック
4. ユーザーの大会データを選択・確認

## 🔧 新規APIエンドポイント

### ユーザー用
```
GET /me/competitions                    # 参加大会一覧
GET /me/feedback-data/{competition_id}  # フィードバックデータ
GET /me/sensor-data                     # センサーデータ
GET /me/race-records/{competition_id}   # 大会記録
GET /me/data-summary                    # データサマリー
```

### 管理者用
```
GET /admin/users/{user_id}/competitions                    # ユーザー参加大会一覧
GET /admin/users/{user_id}/feedback-data/{competition_id}  # ユーザーフィードバックデータ
```

## 📂 プロジェクト構造

```
triathlon-system/
├── triathlon-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   ├── TriathlonFeedbackChart.tsx  🆕 メイングラフ
│   │   │   │   ├── TemperatureChart.tsx        ✅ 既存
│   │   │   │   └── StatisticsCard.tsx          ✅ 既存
│   │   │   └── ui/                             ✅ 基本UI
│   │   ├── hooks/
│   │   │   └── useFeedbackChart.ts             🆕 カスタムフック
│   │   ├── services/
│   │   │   ├── feedbackService.ts              🆕 API通信
│   │   │   └── userDataService.ts              🔄 拡張済み
│   │   ├── types/
│   │   │   └── feedback.ts                     🆕 型定義
│   │   ├── utils/
│   │   │   └── chartUtils.ts                   🔄 拡張済み
│   │   └── pages/
│   │       ├── UserDashboard.tsx               🔄 グラフ統合
│   │       └── DataDetail.tsx                  🔄 グラフ統合
│   └── package.json
├── triathlon-backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── feedback.py                     🆕 フィードバック
│   │   │   ├── user_data.py                    🔄 拡張済み
│   │   │   ├── admin.py                        ✅ 既存
│   │   │   └── auth.py                         ✅ 既存
│   │   ├── schemas/
│   │   │   └── feedback.py                     🆕 スキーマ
│   │   ├── models/                             ✅ 既存
│   │   └── main.py                             🔄 ルーター追加
│   └── requirements.txt
└── README.md                                   🔄 更新済み
```

## 📈 データフロー

```
1. センサーデータ収集
   ├── 体表温度（halshare CSV）
   ├── カプセル体温（e-Celcius CSV）
   ├── 心拍数（Garmin TCX）
   └── WBGT値（環境データ CSV）

2. マッピング処理
   └── ユーザーとセンサーの関連付け

3. フィードバック生成
   ├── 時系列データ統合
   ├── 競技区間識別（Swim/Bike/Run）
   └── グラフ描画

4. ユーザー表示
   ├── リアルタイムチャート
   ├── 競技区間背景色
   └── 統計情報表示
```

## 🎯 開発状況

### ✅ 完全実装済み

**🔐 認証システム**
- ログイン・ログアウト
- 管理者・一般ユーザー判定
- セッション管理

**👨‍💼 管理者機能**
- システム統計ダッシュボード
- ユーザー管理（一覧・詳細・検索）
- 大会管理（作成・削除）
- マルチセンサーデータアップロード
- **🆕 フィードbackグラフ表示**

**👤 一般ユーザー機能**
- データサマリー表示
- **🆕 トライアスロンフィードbackグラフ**
- 参加大会一覧
- センサーデータ統計

**📊 フィードバックグラフ（仕様書3.1-3.4完全準拠）**
- ✅ X軸/Y軸設定（時間 vs 温度・心拍）
- ✅ 背景色による競技区間表示
- ✅ オフセット表示機能（前後10分）
- ✅ 複数大会選択機能
- ✅ データ欠損対応

### 🔄 実装中・改善予定

**📈 高度な分析機能**
- パフォーマンス解析
- 競技区間別詳細統計
- データ品質レポート

**🔧 管理機能**
- CSVユーザー自動作成UI（仕様書1.1）
- バッチ操作機能
- データエクスポート機能

## 🧪 テスト

### フロントエンド
```bash
cd triathlon-frontend
npm test
```

### バックエンド
```bash
cd triathlon-backend
pytest
```

## 🚀 デプロイ

### 本番ビルド
```bash
# フロントエンド
cd triathlon-frontend
npm run build

# バックエンド
cd triathlon-backend
pip install -r requirements.txt
python setup_database.py
```

## 📝 ライセンス

このプロジェクトは研究目的で開発されています。

## 🤝 貢献

プロジェクトへの貢献を歓迎します。Issue の作成や Pull Request をお待ちしています。

---

**🎉 フィードバックグラフ機能が完全実装されました！**

仕様書（セクション3.1-3.4）に完全準拠した高度なトライアスロンフィードバックシステムをお楽しみください。