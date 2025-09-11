// src/components/layout/AdminNavigation.tsx

const navigationItems = [
  { label: 'ダッシュボード', path: '/admin/dashboard' },
  { label: 'ユーザー管理', path: '/admin/users' },
  { label: 'マルチセンサーアップロード', path: '/admin/multi-sensor' }, // 🆕
  { label: '大会管理', path: '/admin/competitions' },
  // ❌ 古いCSVアップロードは削除
];