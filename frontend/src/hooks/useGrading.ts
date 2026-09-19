import { useCallback, useRef, useState } from 'react';
import { fetchHint, gradeSteps, transcribeImage } from '../api/client';
import { ApiError, GradeResponse, GradingStatus, ProblemSummary, TranscribedStep } from '../types';

export function useGrading() {
  const [status, setStatus] = useState<GradingStatus>('idle');
  const [selectedProblem, setSelectedProblem] = useState<ProblemSummary | null>(null);
  const [steps, setSteps] = useState<TranscribedStep[]>([]);
  const [gradeResponse, setGradeResponse] = useState<GradeResponse | null>(null);
  const [previousResponse, setPreviousResponse] = useState<GradeResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [highlightedStepId, setHighlightedStepId] = useState<number | null>(null);

  const [activeHint, setActiveHint] = useState<{
    ruleId: string;
    stepText: string;
    level: number;
    text: string;
    maxReached: boolean;
    loading: boolean;
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Resize client-side to about 1600px max on long edge
  const resizeImage = useCallback(async (file: File): Promise<Blob> => {
    return new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(url);
        const maxDimension = 1600;
        let width = img.width;
        let height = img.height;

        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(img, 0, 0, width, height);
          canvas.toBlob(
            (blob) => {
              resolve(blob || file);
            },
            file.type || 'image/jpeg',
            0.92
          );
        } else {
          resolve(file);
        }
      };
      img.onerror = () => {
        resolve(file);
      };
      img.src = url;
    });
  }, []);

  const selectedProblemRef = useRef<ProblemSummary | null>(null);
  const stepsRef = useRef<TranscribedStep[]>([]);
  stepsRef.current = steps;

  const selectProblem = useCallback((problem: ProblemSummary) => {
    selectedProblemRef.current = problem;
    setSelectedProblem(problem);
    setSteps([]);
    setGradeResponse(null);
    setPreviousResponse(null);
    setError(null);
    setActiveHint(null);
    setStatus('idle');
  }, []);

  const handleTranscribe = useCallback(
    async (file: File | Blob, fileName: string = 'solution.png', problemIdOverride?: string) => {
      const probId = problemIdOverride || selectedProblemRef.current?.id || selectedProblem?.id;
      if (!probId) return;

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus('transcribing');
      setError(null);
      setGradeResponse(null);
      setActiveHint(null);

      try {
        let uploadBlob: Blob = file;
        if (file instanceof File) {
          uploadBlob = await resizeImage(file);
        }

        const data = await transcribeImage(probId, uploadBlob, fileName, controller.signal);
        setSteps(data.steps);
        stepsRef.current = data.steps;
        setStatus('transcribed');
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        setError(err as ApiError);
        setStatus('idle');
      }
    },
    [selectedProblem, resizeImage]
  );

  const updateStepText = useCallback((id: number, newText: string) => {
    setSteps((prev) =>
      prev.map((step) => {
        if (step.id === id) {
          return {
            ...step,
            text: newText,
            needs_confirmation: false, // Confirmed on edit
          };
        }
        return step;
      })
    );
    // If already graded, allow regrading
    setStatus((prev) => (prev === 'graded' ? 'retrying' : prev));
  }, []);

  const confirmStep = useCallback((id: number) => {
    setSteps((prev) =>
      prev.map((step) => (step.id === id ? { ...step, needs_confirmation: false } : step))
    );
  }, []);

  const confirmAllSteps = useCallback(() => {
    setSteps((prev) => prev.map((step) => ({ ...step, needs_confirmation: false })));
  }, []);

  const submitGrade = useCallback(async (stepsOverride?: any) => {
    const validOverride = Array.isArray(stepsOverride) ? (stepsOverride as TranscribedStep[]) : undefined;
    const rawSteps = validOverride || (stepsRef.current.length > 0 ? stepsRef.current : steps);
    const prob = selectedProblemRef.current || selectedProblem;
    if (!prob || !Array.isArray(rawSteps) || rawSteps.length === 0) return;

    // Auto-confirm all steps on submission so grading is never blocked
    const currentSteps = rawSteps.map((s) => ({ ...s, needs_confirmation: false }));
    setSteps(currentSteps);
    stepsRef.current = currentSteps;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setStatus('grading');
    setError(null);

    try {
      const stepInputs = currentSteps.map((s) => ({ id: s.id, text: s.text }));
      const prevResults = gradeResponse?.results;

      const res = await gradeSteps(
        prob.id,
        stepInputs,
        prevResults,
        controller.signal
      );

      if (gradeResponse) {
        setPreviousResponse(gradeResponse);
      }
      setGradeResponse(res);
      setStatus('graded');
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      setError(err as ApiError);
      setStatus(gradeResponse ? 'graded' : 'transcribed');
    }
  }, [selectedProblem, steps, gradeResponse]);

  const requestHint = useCallback(
    async (ruleId: string, stepText: string, level: number = 1) => {
      if (!selectedProblem) return;

      setActiveHint({
        ruleId,
        stepText,
        level,
        text: 'Examining step...',
        maxReached: level >= 3,
        loading: true,
      });

      try {
        const res = await fetchHint(selectedProblem.id, ruleId, stepText, level);
        setActiveHint({
          ruleId,
          stepText,
          level: res.level,
          text: res.hint,
          maxReached: res.max_level_reached || res.level >= 3,
          loading: false,
        });
      } catch (err: any) {
        setError(err as ApiError);
        setActiveHint(null);
      }
    },
    [selectedProblem]
  );

  const pulseStep = useCallback((stepId: number) => {
    setHighlightedStepId(stepId);
    // Scroll element into view smoothly
    const elem = document.getElementById(`step-line-${stepId}`);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    setTimeout(() => {
      setHighlightedStepId(null);
    }, 2000);
  }, []);

  const dismissError = useCallback(() => {
    setError(null);
  }, []);

  return {
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
    closeHint: () => setActiveHint(null),
    pulseStep,
    dismissError,
  };
}
