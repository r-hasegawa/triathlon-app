# Triathlon Sensor Data Feedback System - Frontend

トライアスロン研究センサデータフィードバックシステムのフロントエンド

## 🛠️ 技術構成

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Hooks
- **Routing**: React Router
- **HTTP Client**: Fetch API

## 🚀 開発環境セットアップ

### 1. 依存関係インストール
```bash
npm install
```

### 2. 開発サーバー起動
```bash
npm run dev
```

### 3. アクセス
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## 📋 初期アカウント

**管理者**
- Username: `admin`
- Password: `admin123`

**テストユーザー**
- Username: `testuser1`
- Password: `password123`

## 🎯 実装済み機能

### 認証
- ログイン・ログアウト
- 管理者・一般ユーザー判定
- 認証保護されたルート

### 管理者ダッシュボード
- システム統計表示
- ユーザー管理へのナビゲーション
- 大会管理へのナビゲーション
- データアップロードへのナビゲーション

### ユーザー管理 (管理者のみ)
- ユーザー一覧表示
- ユーザー詳細情報

### 大会管理 (管理者のみ)
- 大会一覧表示
- 新規大会作成
- 大会削除

### データアップロード (管理者のみ)
- 大会選択
- センサーデータアップロード（体表温、コア体温、心拍）
- WBGTデータアップロード
- マッピングデータアップロード
- アップロード結果表示

## 📂 プロジェクト構造

```
triathlon-frontend/
├── src/
│   ├── components/         # 再利用可能コンポーネント
│   │   ├── ui/            # UIコンポーネント
│   │   └── layout/        # レイアウトコンポーネント
│   ├── pages/             # ページコンポーネント
│   │   ├── Login.tsx
│   │   ├── AdminDashboard.tsx
│   │   ├── UserManagement.tsx
│   │   ├── CompetitionManagement.tsx
│   │   └── MultiSensorUpload.tsx
│   ├── contexts/          # React Context
│   │   └── AuthContext.tsx
│   ├── services/          # API通信
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   └── adminService.ts
│   ├── types/             # TypeScript型定義
│   └── styles/            # スタイル
├── package.json
└── README.md
```

## 🔧 ビルド・デプロイ

### 本番ビルド
```bash
npm run build
```

### プレビュー
```bash
npm run preview
```

## ⚙️ 設定

### API接続設定
`src/services/api.ts`でバックエンドURL設定：
```typescript
const BASE_URL = 'http://localhost:8000';
```

### プロキシ設定
`vite.config.ts`でプロキシ設定済み：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```