import { ApiError, GradeResponse, HintResponse, ProblemSummary, StepInput, TranscribedStep } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorData: { error?: ApiError } | null = null;
    try {
      errorData = await res.json();
    } catch {
      // Ignored
    }

    if (errorData?.error) {
      throw errorData.error;
    }

    throw {
      code: 'HTTP_ERROR',
      message: `Request failed with status ${res.status}: ${res.statusText}`,
      action: 'Please check your connection and try again.',
    } as ApiError;
  }

  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<{ status: string; version: string; demo_mode: boolean }> {
  const res = await fetch(`${API_BASE}/api/health`);
  return handleResponse(res);
}

export async function fetchProblems(): Promise<ProblemSummary[]> {
  const res = await fetch(`${API_BASE}/api/problems`);
  return handleResponse(res);
}

export async function transcribeImage(
  problemId: string,
  file: File | Blob,
  fileName: string = 'solution.png',
  signal?: AbortSignal
): Promise<{ problem_id: string; steps: TranscribedStep[]; cached: boolean }> {
  const formData = new FormData();
  formData.append('problem_id', problemId);
  formData.append('file', file, fileName);

  const res = await fetch(`${API_BASE}/api/transcribe`, {
    method: 'POST',
    body: formData,
    signal,
  });

  return handleResponse(res);
}

export async function gradeSteps(
  problemId: string,
  steps: StepInput[],
  previousResults?: any[],
  signal?: AbortSignal
): Promise<GradeResponse> {
  const res = await fetch(`${API_BASE}/api/grade`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      problem_id: problemId,
      steps,
      previous_results: previousResults,
    }),
    signal,
  });

  return handleResponse(res);
}

export async function fetchHint(
  problemId: string,
  ruleId: string,
  stepText: string,
  level: number,
  signal?: AbortSignal
): Promise<HintResponse> {
  const res = await fetch(`${API_BASE}/api/hint`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      problem_id: problemId,
      rule_id: ruleId,
      step_text: stepText,
      level,
    }),
    signal,
  });

  return handleResponse(res);
}
