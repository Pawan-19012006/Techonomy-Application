export interface Team {
  id: number;
  name: string;
  email: string;
  question_limit: number;
  questions_used: number;
  is_admin: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface Event {
  id: number;
  name: string;
  description?: string;
  business_objective?: string;
  rules?: string;
  start_time: string;
  end_time: string;
  question_limit: number;
  is_active: boolean;
  status: 'UPCOMING' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'NO_EVENT';
  created_at: string;
}

export interface EventStatus {
  event_id?: number;
  event_name?: string;
  status: 'UPCOMING' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'NO_EVENT';
  start_time?: string;
  end_time?: string;
  question_limit: number;
  timer_remaining_seconds: number;
  started: boolean;
  finished: boolean;
}

export interface DocumentMetadata {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  content_type: string;
  pages: number;
  status: string;
  team_id: number;
  uploaded_at: string;
}

export interface DocumentUploadResponse {
  message: string;
  document: DocumentMetadata;
}

export interface DocumentDeleteResponse {
  message: string;
  doc_id: number;
}

export interface PromptLog {
  id: number;
  team_id: number;
  prompt: string;
  response?: string;
  status_code: number;
  response_time_ms: number;
  created_at: string;
}

export interface DashboardData {
  team_name: string;
  current_event?: string;
  business_objective?: string;
  rules?: string;
  question_limit: number;
  questions_remaining: number;
  timer_remaining_seconds: number;
  documents_available: number;
  event_status: 'UPCOMING' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'NO_EVENT';
}

export interface QuestionMetrics {
  question_limit: number;
  questions_used: number;
  questions_remaining: number;
}

export interface TeamHistory {
  logs: PromptLog[];
  total_count: number;
}

export interface AnalyticsSummary {
  total_teams: number;
  active_teams: number;
  questions_used: number;
  questions_remaining: number;
  total_prompts: number;
  average_response_time_ms: number;
  most_active_team?: string;
  most_used_document?: string;
}

export interface ChatQueryRequest {
  query: string;
}

export interface ChatQueryResponse {
  query: string;
  response: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  status?: 'sending' | 'sent' | 'error';
}
