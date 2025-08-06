import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      // カスタムフォールバックがあれば使用
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // デフォルトエラー画面
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-md mx-auto">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.19 2.5 1.732 2.5z" />
                </svg>
              </div>
              
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                エラーが発生しました
              </h1>
              
              <p className="text-gray-600 mb-6">
                申し訳ございません。予期しないエラーが発生しました。
                ページを再読み込みするか、しばらく時間をおいて再度お試しください。
              </p>

              <div className="space-y-3">
                <Button onClick={this.handleReload} className="w-full">
                  ページを再読み込み
                </Button>
                
                <Button onClick={this.handleReset} variant="outline" className="w-full">
                  エラーをリセット
                </Button>
              </div>
            </div>

            {/* 開発環境でのエラー詳細表示 */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-8 p-4 bg-gray-100 rounded-md">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                  エラー詳細（開発環境）
                </summary>
                <div className="text-xs text-gray-600 space-y-2">
                  <div>
                    <strong>エラーメッセージ:</strong>
                    <pre className="mt-1 whitespace-pre-wrap">{this.state.error.message}</pre>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <strong>スタックトレース:</strong>
                      <pre className="mt-1 whitespace-pre-wrap">{this.state.errorInfo.componentStack}</pre>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC形式のエラーバウンダリ
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
};

// 軽量エラーバウンダリ（インラインエラー用）
export const InlineErrorBoundary: React.FC<{
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
}> = ({ children, fallback }) => {
  return (
    <ErrorBoundary 
      fallback={
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">
                コンポーネントエラー
              </h3>
              <p className="text-sm text-red-600 mt-1">
                このセクションの読み込みに失敗しました。ページを再読み込みしてください。
              </p>
            </div>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
};