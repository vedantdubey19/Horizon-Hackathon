export type Subject = 'physics' | 'math';

export interface ProblemSummary {
  id: string;
  subject: Subject;
  class: number;
  statement: string;
  total_marks: number;
}

export interface TranscribedStep {
  id: number;
  text: string;
  confidence: number;
  needs_confirmation: boolean;
}

export interface StepInput {
  id: number;
  text: string;
}

export interface GradeResultItem {
  rule_id: string;
  label: string;
  awarded: number;
  max: number;
  reason: string;
  step_id?: number | null;
  is_recovered?: boolean;
}

export interface GradeResponse {
  problem_id: string;
  results: GradeResultItem[];
  total: number;
  max_total: number;
}

export interface HintResponse {
  rule_id: string;
  level: number;
  hint: string;
  max_level_reached: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  action: string;
  detail?: string;
}

export type GradingStatus =
  | 'idle'
  | 'transcribing'
  | 'transcribed'
  | 'grading'
  | 'graded'
  | 'retrying';
