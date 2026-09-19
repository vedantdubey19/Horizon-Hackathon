import React, { useState } from 'react';
import { ProblemSummary } from '../types';

interface ProblemPickerProps {
  problems: ProblemSummary[];
  selectedProblem: ProblemSummary | null;
  onSelectProblem: (problem: ProblemSummary) => void;
}

export const ProblemPicker: React.FC<ProblemPickerProps> = ({
  problems,
  selectedProblem,
  onSelectProblem,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const physicsProblems = problems.filter((p) => p.subject === 'physics');
  const mathProblems = problems.filter((p) => p.subject === 'math');

  return (
    <div style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          fontSize: '0.875rem',
          fontFamily: 'var(--font-sans)',
        }}
        aria-expanded={isOpen}
      >
        <span>Table of Contents ({problems.length} Problems)</span>
        <span>{isOpen ? '\u25b2' : '\u25bc'}</span>
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: 'var(--space-1)',
            width: '380px',
            maxHeight: '480px',
            overflowY: 'auto',
            backgroundColor: 'var(--paper-surface)',
            border: '1px solid var(--paper-edge)',
            borderRadius: 'var(--radius-sm)',
            boxShadow: 'var(--shadow-sheet)',
            zIndex: 10,
            padding: 'var(--space-3)',
          }}
        >
          <div style={{ marginBottom: 'var(--space-3)' }}>
            <h4
              style={{
                fontFamily: 'var(--font-serif)',
                fontSize: '0.875rem',
                color: 'var(--ink-muted)',
                textTransform: 'uppercase',
                borderBottom: '1px solid var(--paper-edge)',
                paddingBottom: 'var(--space-1)',
                marginBottom: 'var(--space-2)',
              }}
            >
              Physics (Class 10–12)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
              {physicsProblems.map((p, idx) => {
                const isSelected = selectedProblem?.id === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      onSelectProblem(p);
                      setIsOpen(false);
                    }}
                    style={{
                      textAlign: 'left',
                      padding: 'var(--space-2)',
                      backgroundColor: isSelected ? '#F2EDE4' : 'transparent',
                      border: 'none',
                      borderLeft: isSelected ? '3px solid var(--examiner-red)' : '3px solid transparent',
                      borderRadius: 0,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
                      <span>Q{idx + 1} &bull; Class {p.class}</span>
                      <span>[{p.total_marks} marks]</span>
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--ink-primary)', fontWeight: isSelected ? 600 : 400, marginTop: '2px' }}>
                      {p.statement.length > 55 ? `${p.statement.slice(0, 55)}...` : p.statement}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <h4
              style={{
                fontFamily: 'var(--font-serif)',
                fontSize: '0.875rem',
                color: 'var(--ink-muted)',
                textTransform: 'uppercase',
                borderBottom: '1px solid var(--paper-edge)',
                paddingBottom: 'var(--space-1)',
                marginBottom: 'var(--space-2)',
              }}
            >
              Mathematics (Class 10–12)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
              {mathProblems.map((p, idx) => {
                const isSelected = selectedProblem?.id === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      onSelectProblem(p);
                      setIsOpen(false);
                    }}
                    style={{
                      textAlign: 'left',
                      padding: 'var(--space-2)',
                      backgroundColor: isSelected ? '#F2EDE4' : 'transparent',
                      border: 'none',
                      borderLeft: isSelected ? '3px solid var(--examiner-red)' : '3px solid transparent',
                      borderRadius: 0,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--ink-muted)' }}>
                      <span>Q{idx + 9} &bull; Class {p.class}</span>
                      <span>[{p.total_marks} marks]</span>
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--ink-primary)', fontWeight: isSelected ? 600 : 400, marginTop: '2px' }}>
                      {p.statement.length > 55 ? `${p.statement.slice(0, 55)}...` : p.statement}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
