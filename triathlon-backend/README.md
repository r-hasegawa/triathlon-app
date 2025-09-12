# Triathlon Sensor Data Feedback System - Backend

トライアスロン研究センサデータフィードバックシステムのバックエンドAPI

## 🏗️ アーキテクチャ

- **Framework**: FastAPI + Python 3.11+
- **Database**: SQLite (開発環境)
- **Authentication**: JWT + bcrypt
- **API Documentation**: OpenAPI (Swagger)
- **Data Processing**: Pandas + NumPy

## 🚀 クイックスタート

### 1. 環境構築
```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. データベース初期化
```bash
python setup_database.py
```

### 3. サーバー起動
```bash
uvicorn app.main:app --reload
```

### 4. API確認
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📋 初期アカウント

**管理者**
- Username: `admin`
- Password: `admin123`

**テストユーザー**
- Username: `testuser1`, `testuser2`, `testuser3`
- Password: `password123`

## 📚 API エンドポイント規則

- **認証** → `/auth/*`
- **管理者専用** → `/admin/*`
- **一般ユーザー本人のデータ** → `/me/*`
- **公共の環境データ** → `/public/*`

## ✅ 実装済みエンドポイント

### 🔐 認証 (`/auth/`)
- `POST /auth/login` - ログイン（ユーザー・管理者対応）
- `GET /auth/me` - ユーザー情報取得
- `POST /auth/logout` - ログアウト

### 👨‍💼 管理者専用 (`/admin/`)

**システム管理**
- `GET /admin/stats` - システム統計情報取得
- `GET /admin/unmapped-data-summary` - 未マッピングデータサマリー

**ユーザー管理**
- `GET /admin/users` - ユーザー一覧取得
- `GET /admin/users/{user_id}` - ユーザー詳細取得

**大会管理**
- `GET /admin/competitions` - 大会一覧取得
- `POST /admin/competitions` - 大会作成
- `DELETE /admin/competitions/{competition_id}` - 大会削除

**データアップロード（実データ形式対応）**
- `POST /admin/upload/skin-temperature` - 体表温データ（halshare CSV）
- `POST /admin/upload/core-temperature` - カプセル体温データ（e-Celcius CSV）
- `POST /admin/upload/heart-rate` - 心拍データ（Garmin TCX）
- `POST /admin/upload/wbgt` - WBGT環境データ
- `POST /admin/upload/mapping` - マッピングデータ

**バッチ管理**
- `GET /admin/batches` - アップロード履歴取得
- `DELETE /admin/batches/{batch_id}` - バッチ削除

### 👤 一般ユーザー本人のデータ (`/me/`)
- `GET /me/data-summary` - 個人のセンサーデータサマリー
- `GET /me/competitions` - 自分が参加した大会一覧
- `GET /me/sensor-data` - 個人のセンサーデータ取得

### 🌍 公共の環境データ (`/public/`)
- `GET /public/competitions` - 公開大会一覧
- `GET /public/competitions/{competition_id}` - 大会詳細情報取得

## 🔄 実装中エンドポイント

### 📊 データ可視化
- `GET /me/chart-data` - チャートデータ取得（部分実装）
- `GET /admin/analytics` - 分析データ取得（開発中）

## ❌ 未実装エンドポイント

### 🎯 フィードバックグラフ（仕様書3.1-3.4）
- [ ] `GET /me/feedback-graph/{competition_id}` - 完全仕様準拠グラフデータ
- [ ] `GET /me/time-series-data` - 時間軸データ（背景色情報含む）
- [ ] `GET /me/competition-phases` - 競技フェーズ情報（Swim/Bike/Run区間）

### 🔧 管理機能
- [ ] `POST /admin/users/bulk-create` - CSVユーザー一括作成（仕様書1.1）
- [ ] `GET /admin/data-quality` - データ品質レポート
- [ ] `POST /admin/data/cleanup` - データクリーンアップ

## 🛠️ 実装済み機能詳細

### 📊 実データ形式対応

**halshare（体表温センサー）**
- CSV形式: `halshareWearerName`, `halshareId`, `datetime`, `temperature`
- バッチ処理対応
- エラーハンドリング

**e-Celcius（カプセル体温センサー）**
- CSV形式: `capsule_id`, `monitor_id`, `datetime`, `temperature`, `status`
- 1-3カプセル/モニター対応
- ステータス管理

**Garmin TCX（心拍データ）**
- TCX（XML）形式: `sensor_id`, `time`, `heart_rate`
- XMLパース処理
- 詳細エラー報告

**WBGT環境データ**
- CSV形式: 環境測定データ
- 大会全体での共有データ

**マッピングデータ**
- CSV形式: `user_id`, `skin_temp_sensor_id`, `core_temp_sensor_id`, `heart_rate_sensor_id`
- センサーとユーザーの関連付け
- データ状態自動更新

### 🔒 権限管理

| エンドポイント | 一般ユーザー | 管理者 |
|------------|---------|--------|
| `/auth/*` | ✅ | ✅ |
| `/admin/*` | ❌ | ✅ |
| `/me/*` | ✅ | ❌ |
| `/public/*` | ✅ | ✅ |

### 💾 データベース設計

**実装済みモデル**
- `User`, `AdminUser` - ユーザー管理
- `Competition`, `RaceRecord` - 大会・記録管理  
- `SkinTemperatureData`, `CoreTemperatureData`, `HeartRateData` - センサーデータ
- `UploadBatch` - バッチ管理
- `SensorMapping` - マッピング管理
- `WBGTData` - 環境データ

## 🛠️ テスト例

### 管理者ログイン
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 体表温データアップロード
```bash
TOKEN="<取得したトークン>"
curl -X POST "http://localhost:8000/admin/upload/skin-temperature" \
  -H "Authorization: Bearer $TOKEN" \
  -F "competition_id=comp_001" \
  -F "files=@sample_halshare.csv"
```

### システム統計取得
```bash
curl -X GET "http://localhost:8000/admin/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## 📁 プロジェクト構造

```
triathlon-backend/
├── app/
│   ├── main.py                    ✅ 実装済み
│   ├── database.py                ✅ 実装済み
│   ├── models/
│   │   ├── user.py               ✅ 実装済み
│   │   ├── competition.py        ✅ 実装済み
│   │   └── flexible_sensor_data.py ✅ 実装済み
│   ├── routers/
│   │   ├── auth.py               ✅ 実装済み
│   │   ├── admin.py              ✅ 実装済み
│   │   ├── user_data.py          🔄 実装中
│   │   └── competition.py        ✅ 実装済み
│   ├── schemas/
│   │   ├── user.py               ✅ 実装済み
│   │   ├── auth.py               ✅ 実装済み
│   │   └── sensor_data.py        ✅ 実装済み
│   ├── services/
│   │   └── flexible_csv_service.py ✅ 実装済み
│   └── utils/
│       ├── security.py           ✅ 実装済み
│       └── dependencies.py       ✅ 実装済み
├── data/                         ✅ 設定済み
├── uploads/csv/                  ✅ 設定済み
├── setup_database.py             ✅ 実装済み
├── requirements.txt              ✅ 最新版
└── README.md
```

## 📦 依存関係管理

**Core Framework**
- fastapi==0.116.1
- uvicorn==0.35.0
- sqlalchemy==2.0.42

**Data Processing**
- pandas==2.3.1
- numpy==2.3.2

**Authentication & Security**
- python-jose==3.5.0
- passlib==1.7.4
- bcrypt==4.3.0

**File Handling**
- python-multipart==0.0.20
- aiofiles==23.2.1

## 🎯 開発優先度

### 高優先度
1. **フィードバックグラフAPI完全実装** - 仕様書3.1-3.4準拠
2. **CSVユーザー自動作成API** - 仕様書1.1実装
3. **時間軸データ処理** - 背景色・オフセット対応

### 中優先度
1. **データ品質管理機能**
2. **パフォーマンス最適化**
3. **ログ・監視機能強化**

### 低優先度
1. **高度な分析機能**
2. **レポート生成機能**