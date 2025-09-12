# Triathlon Sensor Data Feedback System - Frontend

トライアスロン研究センサデータフィードバックシステムのフロントエンド

## 🛠️ 技術構成

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Hooks
- **Routing**: React Router
- **HTTP Client**: Fetch API
- **Charts**: Chart.js + React Chart.js 2

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

## ✅ 実装済み機能

### 🔐 認証システム
- ログイン・ログアウト
- 管理者・一般ユーザー判定
- 認証保護されたルート
- セッション管理

### 👨‍💼 管理者機能
- **ダッシュボード**: システム統計表示、ナビゲーション
- **ユーザー管理**: ユーザー一覧表示、詳細情報、検索・フィルタリング
- **大会管理**: 大会一覧、新規作成、削除機能
- **データアップロード**: 
  - 体表温データ（halshare CSV）
  - カプセル体温データ（e-Celcius CSV）
  - 心拍データ（Garmin TCX）
  - WBGT環境データ
  - マッピングデータ
  - 詳細なアップロード結果とエラー表示

### 👤 一般ユーザー機能
- **基本ダッシュボード**: データ統計表示
- **温度チャート**: 基本的なセンサーデータ可視化（部分実装）

### 🎨 UI/UXコンポーネント
- 再利用可能UIコンポーネント（Button, Card, Input, LoadingSpinner等）
- レスポンシブデザイン対応
- エラーハンドリング
- ローディング状態表示

## 🔄 実装中機能

### 📊 データ可視化 
- **温度チャート**: 基本実装済み、仕様完全準拠は未完了
- **一般ユーザーダッシュボード**: 基本構造実装、機能拡張中

## ❌ 未実装機能

### 🎯 フィードバックグラフ（仕様書3.1-3.4）
- [ ] 複数大会選択機能
- [ ] X軸/Y軸の適切な設定（温度・心拍 vs 時間）
- [ ] 背景色による競技区間表示（Swim/Bike/Run）
- [ ] オフセット表示機能（前後10分）
- [ ] 完全な仕様準拠チャート

### 👥 一般ユーザー向け機能
- [ ] 詳細なデータ表示ページ
- [ ] センサーデータ詳細画面
- [ ] パーソナライズされたフィードバック

### 🔧 管理機能
- [ ] CSVユーザー自動作成UI（仕様書1.1）
- [ ] バッチ削除UI
- [ ] 高度なデータ分析ツール

## 📂 プロジェクト構造

```
triathlon-frontend/
├── src/
│   ├── components/         # 再利用可能コンポーネント
│   │   ├── ui/            # 基本UIコンポーネント
│   │   ├── layout/        # レイアウトコンポーネント
│   │   ├── admin/         # 管理者専用コンポーネント
│   │   └── charts/        # チャートコンポーネント（実装中）
│   ├── pages/             # ページコンポーネント
│   │   ├── Login.tsx                    ✅ 実装済み
│   │   ├── AdminDashboard.tsx          ✅ 実装済み
│   │   ├── UserManagement.tsx          ✅ 実装済み
│   │   ├── CompetitionManagement.tsx   ✅ 実装済み
│   │   ├── MultiSensorUpload.tsx       ✅ 実装済み
│   │   ├── UserDashboard.tsx           🔄 実装中
│   │   └── DataVisualization.tsx       ❌ 未実装
│   ├── contexts/          # React Context
│   │   └── AuthContext.tsx             ✅ 実装済み
│   ├── services/          # API通信
│   │   ├── api.ts                      ✅ 実装済み
│   │   ├── authService.ts              ✅ 実装済み
│   │   ├── adminService.ts             ✅ 実装済み
│   │   └── dataService.ts              🔄 実装中
│   ├── types/             # TypeScript型定義
│   └── styles/            # スタイル
│       └── globals.css                 ✅ 実装済み
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

## 🎯 開発優先度

### 高優先度
1. **フィードバックグラフの完全実装** - 仕様書3.1-3.4準拠
2. **一般ユーザーダッシュボード機能拡充**
3. **データ可視化の改善**

### 中優先度  
1. **詳細なエラーハンドリング**
2. **パフォーマンス最適化**
3. **アクセシビリティ向上**

### 低優先度
1. **UI/UXの細かい調整**
2. **追加的な管理機能**