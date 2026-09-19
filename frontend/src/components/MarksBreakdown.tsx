import React from 'react';
import { GradeResponse } from '../types';
import { HintPanel } from './HintPanel';
import { RubricRow } from './RubricRow';
import { ScoreBadge } from './ScoreBadge';

interface MarksBreakdownProps {
  currentResponse: GradeResponse | null;
  previousResponse: GradeResponse | null;
  activeHint: any;
  onShowStep: (stepId: number) => void;
  onRequestHint: (ruleId: string) => void;
  onNextHintLevel: (ruleId: string, stepText: string, level: number) => void;
  onCloseHint: () => void;
}

export const MarksBreakdown: React.FC<MarksBreakdownProps> = ({
  currentResponse,
  previousResponse,
  activeHint,
  onShowStep,
  onRequestHint,
  onNextHintLevel,
  onCloseHint,
}) => {
  return (
    <aside className="examiner-margin" aria-label="Examiner's Marks and Margin">
      <ScoreBadge
        currentResponse={currentResponse}
        previousResponse={previousResponse}
      />

      {activeHint && (
        <HintPanel
          hint={activeHint}
          onNextLevel={onNextHintLevel}
          onClose={onCloseHint}
        />
      )}

      <div className="rubric-list">
        {currentResponse?.results.map((item, idx) => (
          <RubricRow
            key={item.rule_id}
            item={item}
            animationDelay={idx * 120}
            onShowStep={onShowStep}
            onRequestHint={onRequestHint}
          />
        ))}
      </div>
    </aside>
  );
};
