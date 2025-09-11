# Triathlon Sensor Data Feedback System - Backend

トライアスロン研究センサデータフィードバックシステムのバックエンドAPI

## 🏗️ アーキテクチャ

- **Framework**: FastAPI + Python 3.11+
- **Database**: SQLite (開発)
- **Authentication**: JWT + bcrypt
- **API Documentation**: OpenAPI (Swagger)

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

## 🔧 実装済みエンドポイント

### 認証 (`/auth/`)
- `POST /auth/login` - ログイン
- `GET /auth/me` - ユーザー情報取得
- `POST /auth/logout` - ログアウト

### 管理者専用 (`/admin/`)
- `GET /admin/users` - ユーザー一覧取得
- `GET /admin/competitions` - 大会一覧取得
- `POST /admin/competitions` - 大会作成
- `DELETE /admin/competitions/{competition_id}` - 大会削除
- `GET /admin/stats` - システム統計情報取得
- `GET /admin/unmapped-data-summary` - 未マッピングデータサマリー
- `POST /admin/multi-sensor/upload/skin-temperature` - 体表温データアップロード
- `POST /admin/multi-sensor/upload/core-temperature` - コア体温データアップロード
- `POST /admin/multi-sensor/upload/heart-rate` - 心拍データアップロード
- `POST /admin/multi-sensor/upload/wbgt` - WBGT環境データアップロード
- `POST /admin/multi-sensor/mapping` - マッピングデータアップロード

### 一般ユーザー本人のデータ (`/me/`)
- `GET /me/competitions` - 自分が参加した大会一覧

### 公共の環境データ (`/public/`)
- `GET /public/competitions` - 公開大会一覧
- `GET /public/competitions/{competition_id}` - 大会詳細情報取得

## 🛠️ テスト例

### 管理者ログイン
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 管理者としてシステム統計取得
```bash
TOKEN="<取得したトークン>"
curl -X GET "http://localhost:8000/admin/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### 管理者として大会一覧取得
```bash
curl -X GET "http://localhost:8000/admin/competitions" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔒 権限管理

| エンドポイント | 一般ユーザー | 管理者 |
|------------|---------|--------|
| `/auth/*` | ✅ | ✅ |
| `/admin/*` | ❌ | ✅ |
| `/me/*` | ✅ | ❌ |
| `/public/*` | ✅ | ✅ |

## 📁 プロジェクト構造

```
triathlon-backend/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── competition.py
│   │   └── flexible_sensor_data.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── competition.py
│   │   └── multi_sensor_upload.py
│   └── utils/
│       ├── security.py
│       └── dependencies.py
├── data/
├── setup_database.py
└── README.md
```