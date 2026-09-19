import React from 'react';
import { GradeResponse, GradingStatus, TranscribedStep } from '../types';

interface StepEditorProps {
  steps: TranscribedStep[];
  gradeResponse: GradeResponse | null;
  highlightedStepId: number | null;
  status: GradingStatus;
  onUpdateStep: (id: number, text: string) => void;
  onConfirmStep: (id: number) => void;
  onConfirmAll: () => void;
  onSubmitGrade: () => void;
}

export const StepEditor: React.FC<StepEditorProps> = ({
  steps,
  gradeResponse,
  highlightedStepId,
  status,
  onUpdateStep,
  onConfirmStep,
  onConfirmAll,
  onSubmitGrade,
}) => {
  // Find which step IDs had failed rubric rules
  const failedStepIds = new Set<number>();
  const recoveredStepIds = new Set<number>();

  if (gradeResponse) {
    for (const res of gradeResponse.results) {
      if (res.step_id) {
        if (res.awarded < res.max) {
          failedStepIds.add(res.step_id);
        } else if (res.is_recovered) {
          recoveredStepIds.add(res.step_id);
        }
      }
    }
  }

  const hasUnconfirmed = steps.some((s) => s.needs_confirmation);
  const isGrading = status === 'grading';
  const isGraded = status === 'graded';
  const isRetrying = status === 'retrying';

  return (
    <div className="paper-sheet">
      <div className="ruled-container">
        {steps.map((step) => {
          const isFailing = failedStepIds.has(step.id);
          const isRecovered = recoveredStepIds.has(step.id);
          const isPulsing = highlightedStepId === step.id;

          return (
            <div
              key={step.id}
              id={`step-line-${step.id}`}
              className={`step-line ${
                step.needs_confirmation ? 'needs-confirmation' : ''
              } ${isFailing ? 'has-error' : ''} ${
                isRecovered ? 'is-recovered' : ''
              } ${isPulsing ? 'is-pulsing' : ''}`}
            >
              <div className="step-number">{step.id}.</div>
              <div className="step-input-wrap">
                <input
                  type="text"
                  className={`step-input ${
                    step.needs_confirmation ? 'needs-confirmation' : ''
                  } ${isFailing ? 'has-error' : ''}`}
                  value={step.text}
                  onChange={(e) => onUpdateStep(step.id, e.target.value)}
                  placeholder="Type or edit mathematical step..."
                  aria-label={`Step ${step.id}`}
                />
              </div>

              {step.needs_confirmation && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span className="step-margin-flag" title={`OCR confidence: ${Math.round(step.confidence * 100)}%`}>
                    Please check &rarr;
                  </span>
                  <button
                    type="button"
                    onClick={() => onConfirmStep(step.id)}
                    style={{
                      fontSize: '0.75rem',
                      padding: '2px 6px',
                      backgroundColor: '#FAF0D1',
                      borderColor: '#D8C280',
                    }}
                    title="Confirm this line is transcribed correctly"
                  >
                    Confirm
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="paper-actions">
        <div className="action-left">
          {hasUnconfirmed && (
            <button
              type="button"
              onClick={onConfirmAll}
              style={{ fontSize: '0.8125rem' }}
            >
              Confirm All Lines
            </button>
          )}
          <span style={{ fontSize: '0.8125rem', color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)' }}>
            {steps.length} {steps.length === 1 ? 'step' : 'steps'} transcribed
          </span>
        </div>

        <div>
          <button
            type="button"
            className="primary-btn"
            disabled={isGrading}
            onClick={() => onSubmitGrade()}
          >
            {isGrading
              ? 'Evaluating Steps...'
              : isRetrying
              ? 'Regrade Solution \u21bb'
              : isGraded
              ? 'Regrade Solution \u21bb'
              : 'Grade Solution \u2192'}
          </button>
        </div>
      </div>
    </div>
  );
};
