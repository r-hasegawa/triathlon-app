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

### API テスト例

#### ヘルスチェック
```bash
curl http://localhost:8000/health
```

#### 管理者ログイン
```bash
# ログインしてトークンを取得
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

#### 管理者として特定ユーザーのデータ取得
```bash
# トークンを変数に保存
TOKEN="<取得したトークン>"

# ユーザーのセンサー一覧を取得
curl -X GET "http://localhost:8000/admin/users/testuser1/sensors" \
  -H "Authorization: Bearer $TOKEN"

# ユーザーのデータを取得
curl -X GET "http://localhost:8000/admin/users/testuser1/data?page=0&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# フィルター付きでデータ取得
curl -X GET "http://localhost:8000/admin/users/testuser1/data?sensor_id=SENSOR_001&start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59" \
  -H "Authorization: Bearer $TOKEN"

# CSV形式でエクスポート
curl -X GET "http://localhost:8000/admin/users/testuser1/data/export?format=csv" \
  -H "Authorization: Bearer $TOKEN" \
  -o "user_data.csv"
```

#### 一般ユーザーとして自分のデータ取得
```bash
# ユーザーログイン
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser1&password=password123"

TOKEN="<取得したトークン>"

# 自分のセンサー一覧を取得
curl -X GET "http://localhost:8000/data/my-sensors" \
  -H "Authorization: Bearer $TOKEN"

# 自分のデータを取得
curl -X GET "http://localhost:8000/data/my-data?page=0&limit=100" \
  -H "Authorization: Bearer $TOKEN"
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
- `POST /auth/logout` - ログアウト

### 管理者専用 (`/admin`)

#### ユーザー管理
- `GET /admin/users` - ユーザー一覧取得
- `GET /admin/users-with-stats` - 統計付きユーザー一覧
- `POST /admin/users` - ユーザー作成
- `PUT /admin/users/{user_id}` - ユーザー更新
- `DELETE /admin/users/{user_id}` - ユーザー削除
- `POST /admin/users/{user_id}/reset-password` - パスワードリセット

#### ユーザーデータ閲覧（管理者権限）
- `GET /admin/users/{user_id}/sensors` - 特定ユーザーのセンサー一覧
- `GET /admin/users/{user_id}/data` - 特定ユーザーのデータ取得
- `GET /admin/users/{user_id}/stats` - 特定ユーザーの統計情報
- `GET /admin/users/{user_id}/data/export` - データエクスポート（CSV/JSON）

#### CSV管理
- `POST /admin/upload/csv` - CSVファイル同時アップロード
- `GET /admin/upload-history` - アップロード履歴
- `GET /admin/sensor-mappings` - センサマッピング一覧

#### ダッシュボード
- `GET /admin/dashboard-stats` - ダッシュボード統計

### 一般ユーザー用 (`/data`)
- `GET /data/my-sensors` - 自分のセンサー一覧
- `GET /data/my-data` - 自分のセンサーデータ取得
- `GET /data/my-data/stats` - 自分のデータ統計
- `GET /data/my-data/chart` - グラフ用データ（間引き済み）
- `GET /data/my-data/export` - データエクスポート（CSV/JSON）

## 🔧 設定

環境変数は `.env` ファイルで設定：

```env
DATABASE_URL=sqlite:///./data/triathlon.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads/csv
```

## 🔒 権限管理

### エンドポイントアクセス制限

| エンドポイント | 一般ユーザー | 管理者 | 説明 |
|------------|---------|--------|------|
| `/data/*` | ✅ 自分のデータのみ | ❌ | ユーザー専用エンドポイント |
| `/admin/*` | ❌ | ✅ | 管理者専用エンドポイント |
| `/admin/users/{user_id}/data` | ❌ | ✅ | 任意ユーザーのデータ閲覧 |
| `/auth/*` | ✅ | ✅ | 認証関連（共通） |

### トークン構造
```json
{
  "sub": "user_id or admin_id",
  "is_admin": true/false,
  "exp": "expiration_timestamp"
}
```

## 📁 プロジェクト構造

```
triathlon-backend/
├── app/
│   ├── main.py              # FastAPIメイン
│   ├── database.py          # DB接続設定
│   ├── models/              # SQLAlchemyモデル
│   │   ├── user.py          # ユーザー/管理者モデル
│   │   └── sensor_data.py   # センサデータモデル
│   ├── schemas/             # Pydanticスキーマ
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── sensor_data.py
│   ├── routers/             # APIルーター
│   │   ├── auth.py          # 認証API
│   │   ├── admin.py         # 管理者API（ユーザーデータ閲覧含む）
│   │   └── data.py          # 一般ユーザーAPI
│   ├── services/            # ビジネスロジック
│   │   └── csv_service.py   # CSV処理
│   ├── utils/               # ユーティリティ
│   │   ├── security.py      # JWT/パスワード処理
│   │   └── dependencies.py  # 認証依存性
│   └── repositories/        # データアクセス層
├── data/                    # SQLiteデータベース
├── uploads/csv/             # CSVアップロード先
├── requirements.txt         # Python依存関係
├── setup_database.py        # DB初期化スクリプト
└── README.md               # このファイル
```

## 🐛 トラブルシューティング

### よくあるエラーと対処法

#### 403 Forbidden エラー
```
問題: 管理者が /data/my-data にアクセスすると403エラー
原因: /data/* は一般ユーザー専用エンドポイント
解決: /admin/users/{user_id}/data を使用
```

#### トークン認証エラー
```
問題: 401 Unauthorized
原因: トークン期限切れまたは無効
解決: 再ログインしてトークンを更新
```

#### CSVアップロードエラー
```
問題: ファイルサイズ制限エラー
原因: 10MB制限を超過
解決: ファイルを分割するか、設定を変更
```

## 🚀 本番環境への移行

### PostgreSQL設定例
```python
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/triathlon_db
DATABASE_TYPE=postgresql
```

### Docker化
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### セキュリティ強化
- SECRET_KEYを強力なランダム文字列に変更
- HTTPSを有効化
- Rate Limitingを設定
- ログ監視を実装

## 📝 ライセンス

[プロジェクトのライセンスを記載]