import React from 'react';
import { ApiError } from '../types';

interface ErrorBannerProps {
  error: ApiError | null;
  onDismiss: () => void;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, onDismiss, onRetry }) => {
  if (!error) return null;

  return (
    <div className="error-banner" role="alert">
      <div className="error-content">
        <span className="error-title">{error.message}</span>
        <span className="error-action-text">{error.action}</span>
      </div>
      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            style={{ fontSize: '0.8125rem', padding: '2px 8px' }}
          >
            Retry
          </button>
        )}
        <button
          type="button"
          onClick={onDismiss}
          style={{ fontSize: '0.8125rem', padding: '2px 8px' }}
          aria-label="Dismiss error"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
};
