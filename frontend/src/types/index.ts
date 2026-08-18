export interface TeamData {
  team_name: string;
  member_names: string[];
  started_at: string;
  timer_remaining_seconds?: number;
  session_duration_seconds?: number;
  is_expired?: boolean;
  // Backwards compatibility fields
  id?: number;
  name?: string;
  email?: string;
  question_limit?: number;
  questions_used?: number;
  questions_remaining?: number;
  is_admin?: boolean;
  created_at?: string;
}

// Backwards compatibility alias
export type Team = TeamData;

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface SourceItem {
  document: string;
  page?: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: SourceItem[];
  team_name: string;
}

// Backwards compatibility alias for ChatQueryResponse
export interface ChatQueryResponse {
  query?: string;
  response: string;
  answer?: string;
  sources?: SourceItem[];
  team_name?: string;
}

export interface PromptLog {
  id: number;
  prompt: string;
  response?: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  sources?: SourceItem[];
  timestamp: string;
  status?: 'sending' | 'sent' | 'error';
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

export interface DashboardData {
  team_name: string;
  member_names: string[];
  started_at: string;
  documents_available: number;
  business_objective?: string;
  current_event?: string;
  timer_remaining_seconds?: number;
  question_limit?: number;
  questions_remaining?: number;
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
