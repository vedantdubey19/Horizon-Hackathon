import React, { useEffect, useState } from 'react';
import { fetchHealth, fetchProblems } from './api/client';
import { ErrorBanner } from './components/ErrorBanner';
import { ImageUploader } from './components/ImageUploader';
import { MarksBreakdown } from './components/MarksBreakdown';
import { ProblemPicker } from './components/ProblemPicker';
import { StepEditor } from './components/StepEditor';
import { useGrading } from './hooks/useGrading';
import { ProblemSummary } from './types';
import './styles/base.css';
import './styles/paper.css';

export const App: React.FC = () => {
  const [problems, setProblems] = useState<ProblemSummary[]>([]);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(true);

  const {
    status,
    selectedProblem,
    steps,
    gradeResponse,
    previousResponse,
    error,
    setError,
    activeHint,
    highlightedStepId,
    selectProblem,
    handleTranscribe,
    updateStepText,
    confirmStep,
    confirmAllSteps,
    submitGrade,
    requestHint,
    closeHint,
    pulseStep,
    dismissError,
  } = useGrading();

  // Load initial problems and health status
  useEffect(() => {
    fetchHealth()
      .then((h) => setIsDemoMode(h.demo_mode))
      .catch(() => setIsDemoMode(true));

    fetchProblems()
      .then((data) => {
        setProblems(data);
        if (data.length > 0 && !selectedProblem) {
          selectProblem(data[0]);
        }

        // Check for quick sample presets via URL search query
        const params = new URLSearchParams(window.location.search);
        const sampleQuery = params.get('sample');

        if (sampleQuery === 'correct') {
          const p = data.find((x) => x.id === 'phy-ohm-01') || data[0];
          selectProblem(p);
          setTimeout(() => {
            handleTranscribe(
              new Blob(['sample_ohm_correct_image_bytes'], { type: 'image/png' }),
              'phy-ohm-01.png',
              'phy-ohm-01'
            );
          }, 100);
        } else if (sampleQuery === 'error') {
          const p = data.find((x) => x.id === 'phy-ohm-01') || data[0];
          selectProblem(p);
          setTimeout(() => {
            handleTranscribe(
              new Blob(['sample_ohm_wrong_sub_image_bytes'], { type: 'image/png' }),
              'phy-ohm-01-slip.png',
              'phy-ohm-01'
            );
          }, 100);
        }
      })
      .catch((err) => {
        console.error('Failed to load problems:', err);
      });
  }, []);

  // Auto-grade sample presets once transcribed
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sampleQuery = params.get('sample');
    if (sampleQuery && steps.length > 0 && status === 'transcribed') {
      if (sampleQuery === 'error') {
        confirmAllSteps();
      }
      submitGrade();
    } else if (sampleQuery === 'error' && status === 'graded' && !activeHint) {
      // Auto-open Level 2 hint for the error preset
      setTimeout(() => {
        requestHint('substitution', 'V = 0.5 * 2', 2);
      }, 200);
    }
  }, [steps, status, confirmAllSteps, submitGrade, activeHint, requestHint]);

  const handleSelectProblemById = (problemId: string) => {
    const found = problems.find((p) => p.id === problemId);
    if (found) {
      selectProblem(found);
    }
  };

  const handleRequestHint = (ruleId: string) => {
    // Find step corresponding to rule
    const ruleResult = gradeResponse?.results.find((r) => r.rule_id === ruleId);
    const stepId = ruleResult?.step_id;
    const step = steps.find((s) => s.id === stepId) || steps[steps.length - 1];
    requestHint(ruleId, step ? step.text : '', 1);
  };

  const handleNextHintLevel = (ruleId: string, stepText: string, nextLevel: number) => {
    requestHint(ruleId, stepText, nextLevel);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="wordmark-container">
          <span className="wordmark">MarkLoss</span>
          <span className="tagline">Step-level AI examiner for handwritten physics & math</span>
        </div>

        <div className="header-status">
          {isDemoMode && <span className="demo-pill">Demo Mode</span>}
          {problems.length > 0 && (
            <ProblemPicker
              problems={problems}
              selectedProblem={selectedProblem}
              onSelectProblem={selectProblem}
            />
          )}
        </div>
      </header>

      {/* Main Workspace */}
      <main>
        {error && (
          <div style={{ marginTop: 'var(--space-4)' }}>
            <ErrorBanner error={error} onDismiss={dismissError} onRetry={submitGrade} />
          </div>
        )}

        <div className="workspace-grid">
          {/* Left Column: Ruled Paper Sheet */}
          <section className="paper-sheet" aria-label="Student Answer Sheet">
            {selectedProblem && (
              <div className="problem-banner">
                <div className="problem-meta">
                  <span style={{ textTransform: 'uppercase', fontWeight: 600 }}>
                    {selectedProblem.subject} &bull; Class {selectedProblem.class}
                  </span>
                  <span>Maximum Marks: {selectedProblem.total_marks}</span>
                </div>
                <h2 className="problem-title">{selectedProblem.statement}</h2>
              </div>
            )}

            {steps.length === 0 ? (
              <div style={{ padding: 'var(--space-8) var(--space-6)' }}>
                <ImageUploader
                  status={status}
                  onUpload={handleTranscribe}
                  onSelectProblemById={handleSelectProblemById}
                  onError={setError}
                />
              </div>
            ) : (
              <div>
                <StepEditor
                  steps={steps}
                  gradeResponse={gradeResponse}
                  highlightedStepId={highlightedStepId}
                  status={status}
                  onUpdateStep={updateStepText}
                  onConfirmStep={confirmStep}
                  onConfirmAll={confirmAllSteps}
                  onSubmitGrade={submitGrade}
                />
                <div style={{ padding: 'var(--space-3) var(--space-6)', display: 'flex', justifyContent: 'flex-start' }}>
                  <button
                    type="button"
                    className="text-btn"
                    onClick={() => selectProblem(selectedProblem!)}
                  >
                    &larr; Upload a different answer photo
                  </button>
                </div>
              </div>
            )}
          </section>

          {/* Right Column: Examiner's Margin */}
          <MarksBreakdown
            currentResponse={gradeResponse}
            previousResponse={previousResponse}
            activeHint={activeHint}
            onShowStep={pulseStep}
            onRequestHint={handleRequestHint}
            onNextHintLevel={handleNextHintLevel}
            onCloseHint={closeHint}
          />
        </div>
      </main>

      {/* Footer & Honest Limitations */}
      <footer className="app-footer">
        <p className="limitations-note">
          <strong>Note & Limitations:</strong> MarkLoss is a step-level practice tool for Class 10–12 physics and mathematics.
          Marks are awarded deterministically by code against board rubrics, not official board evaluations.
          Diagrams, graphs, and chemistry equations are out of scope.
        </p>
      </footer>
    </div>
  );
};
