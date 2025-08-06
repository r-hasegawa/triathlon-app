# Triathlon Sensor Data Feedback System - Backend

トライアスロン研究センサデータフィードバックシステムのバックエンドAPI

## 🏗️ アーキテクチャ

- **Framework**: FastAPI + Python 3.11+
- **Database**: SQLite (開発) → PostgreSQL/DynamoDB (本番)
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

## 🛠️ 開発

### API テスト
```bash
# ヘルスチェック
curl http://localhost:8000/health

# ログイン
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### データベースリセット
```bash
rm -rf data/
python setup_database.py
```

## 📚 API エンドポイント

### 認証 (`/auth`)
- `POST /auth/login` - ログイン
- `GET /auth/me` - ユーザー情報取得

### 管理者 (`/admin`)
- `POST /admin/upload/csv` - CSVアップロード
- `GET /admin/users` - ユーザー管理

### データ (`/data`)
- `GET /data/my-data` - センサデータ取得
- `GET /data/my-data/chart` - グラフ用データ
- `GET /data/my-data/export` - データエクスポート

## 🔧 設定

環境変数は `.env` ファイルで設定：

```env
DATABASE_URL=sqlite:///./data/triathlon.db
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000
```