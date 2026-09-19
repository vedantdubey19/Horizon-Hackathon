import { ApiError, GradeResponse, HintResponse, ProblemSummary, StepInput, TranscribedStep } from '../types';

function normalizeApiBase(): string {
  const envBase = (import.meta.env.VITE_API_BASE_URL || '').trim();
  if (!envBase) return '';
  let url = envBase;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    if (url.startsWith('localhost') || url.startsWith('127.0.0.1')) {
      url = `http://${url}`;
    } else {
      url = `https://${url}`;
    }
  }
  return url.replace(/\/+$/, '');
}

const API_BASE = normalizeApiBase();

function apiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

async function handleResponse<T>(res: Response): Promise<T> {
  const contentType = res.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  if (!res.ok) {
    let errorData: { error?: ApiError; detail?: any } | null = null;
    if (isJson) {
      try {
        errorData = await res.json();
      } catch {
        // Ignored
      }
    }

    if (errorData?.error) {
      throw errorData.error;
    }

    const message =
      typeof errorData?.detail === 'string'
        ? errorData.detail
        : `Request failed with status ${res.status}: ${res.statusText}`;

    throw {
      code: 'HTTP_ERROR',
      message,
      action:
        res.status === 404
          ? 'API endpoint not found. Please verify that the backend is running and reachable.'
          : 'Please check your connection and try again.',
    } as ApiError;
  }

  if (!isJson) {
    throw {
      code: 'INVALID_RESPONSE',
      message: 'Received non-JSON response from server.',
      action: 'Please ensure VITE_API_BASE_URL points to the backend server and not a static host.',
    } as ApiError;
  }

  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<{ status: string; version: string; demo_mode: boolean }> {
  const res = await fetch(apiUrl('/api/health'));
  return handleResponse(res);
}

export async function fetchProblems(): Promise<ProblemSummary[]> {
  const res = await fetch(apiUrl('/api/problems'));
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

  const res = await fetch(apiUrl('/api/transcribe'), {
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
  const res = await fetch(apiUrl('/api/grade'), {
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
  const res = await fetch(apiUrl('/api/hint'), {
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
