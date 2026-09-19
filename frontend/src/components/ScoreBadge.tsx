import React, { useMemo } from 'react';
import { GradeResponse } from '../types';
import { HandCircle } from './Icons';

interface ScoreBadgeProps {
  currentResponse: GradeResponse | null;
  previousResponse: GradeResponse | null;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({
  currentResponse,
  previousResponse,
}) => {
  if (!currentResponse) return null;

  const total = currentResponse.total;
  const maxTotal = currentResponse.max_total;
  const isPerfect = total === maxTotal;

  // Check if marks were recovered compared to previous attempt
  const recoveredDelta = useMemo(() => {
    if (!previousResponse) return 0;
    const diff = currentResponse.total - previousResponse.total;
    return diff > 0 ? diff : 0;
  }, [currentResponse, previousResponse]);

  return (
    <div className="score-badge-card" aria-live="polite">
      <div className="score-badge-left">
        <span className="score-label">Examiner Mark</span>
        <div className="score-display">
          <span className={`handwritten-total ${isPerfect ? 'perfect' : ''}`}>
            {total} / {maxTotal}
          </span>
          {recoveredDelta > 0 && (
            <span className="recovered-pill" title="Marks recovered after corrections!">
              +{recoveredDelta}
            </span>
          )}
        </div>
      </div>
      <div style={{ position: 'relative', width: 68, height: 68, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <HandCircle
          key={`${total}-${recoveredDelta}`}
          size={64}
          color={isPerfect ? 'var(--correct-green)' : 'var(--examiner-red)'}
        />
      </div>
    </div>
  );
};
