import React from 'react';
import { GradeResultItem } from '../types';
import { HandCross, HandTick } from './Icons';

interface RubricRowProps {
  item: GradeResultItem;
  onShowStep?: (stepId: number) => void;
  onRequestHint?: (ruleId: string) => void;
  animationDelay?: number;
}

export const RubricRow: React.FC<RubricRowProps> = ({
  item,
  onShowStep,
  onRequestHint,
  animationDelay = 0,
}) => {
  const isAwarded = item.awarded >= item.max;

  return (
    <div
      className={`rubric-card ${isAwarded ? 'awarded' : 'failed'} ${
        item.is_recovered ? 'recovered' : ''
      }`}
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div className="rubric-header">
        <span className="rubric-label">{item.label}</span>
        <div
          className={`rubric-mark ${isAwarded ? 'awarded' : 'failed'}`}
          aria-label={`${item.awarded} out of ${item.max} marks`}
        >
          {isAwarded ? <HandTick size={18} /> : <HandCross size={18} />}
          <span>
            {item.awarded} / {item.max}
          </span>
        </div>
      </div>

      <p className="rubric-reason">{item.reason}</p>

      <div className="rubric-actions">
        {item.step_id ? (
          <button
            type="button"
            className="text-btn"
            onClick={() => onShowStep?.(item.step_id!)}
          >
            Show me where (Line {item.step_id})
          </button>
        ) : (
          <span style={{ fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
            Missing in working
          </span>
        )}

        {!isAwarded && (
          <button
            type="button"
            className="text-btn"
            style={{ fontWeight: 600 }}
            onClick={() => onRequestHint?.(item.rule_id)}
          >
            Get a hint &rarr;
          </button>
        )}
      </div>
    </div>
  );
};
