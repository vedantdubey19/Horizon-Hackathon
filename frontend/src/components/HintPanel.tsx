import React from 'react';

interface HintPanelProps {
  hint: {
    ruleId: string;
    stepText: string;
    level: number;
    text: string;
    maxReached: boolean;
    loading: boolean;
  } | null;
  onNextLevel: (ruleId: string, stepText: string, nextLevel: number) => void;
  onClose: () => void;
}

export const HintPanel: React.FC<HintPanelProps> = ({
  hint,
  onNextLevel,
  onClose,
}) => {
  if (!hint) return null;

  return (
    <div className="hint-sticky-panel" role="region" aria-label="Examiner Hint">
      <div className="hint-header">
        <span className="hint-title">Examiner's Note</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span className="hint-level-pill">
            Hint {hint.level} / 3
          </span>
          <button
            type="button"
            className="text-btn"
            onClick={onClose}
            style={{ fontSize: '1rem', color: '#5C4A00', textDecoration: 'none' }}
            aria-label="Close hint"
          >
            &times;
          </button>
        </div>
      </div>

      <div className="hint-body">
        {hint.loading ? (
          <em>Formulating pedagogical hint...</em>
        ) : (
          <p>{hint.text}</p>
        )}
      </div>

      <div className="hint-footer">
        {hint.level < 3 && !hint.maxReached ? (
          <button
            type="button"
            disabled={hint.loading}
            onClick={() => onNextLevel(hint.ruleId, hint.stepText, hint.level + 1)}
            style={{
              backgroundColor: '#F5E68C',
              borderColor: '#D8C564',
              color: '#4A3C00',
              fontSize: '0.8125rem',
              fontWeight: 600,
            }}
          >
            Need more help? (Level {hint.level + 1}) &rarr;
          </button>
        ) : (
          <span className="hint-max-reached">
            That's the most I can say without giving the answer!
          </span>
        )}
      </div>
    </div>
  );
};
