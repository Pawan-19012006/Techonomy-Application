import { apiClient } from '../api/axios';
import { ChatResponse, PromptLog, SourceItem, TeamData } from '../types';

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL =
  rawApiBaseUrl !== undefined && rawApiBaseUrl !== null && rawApiBaseUrl !== ''
    ? rawApiBaseUrl
    : (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');

/**
 * 1. Join or Register Event Team
 * POST /api/teams/join
 */
export const joinTeam = async (team_name: string, member_names: string[]): Promise<TeamData> => {
  const response = await apiClient.post<TeamData>('/api/teams/join', {
    team_name,
    member_names,
  });
  return response.data;
};

/**
 * 2. Submit RAG Chat Question (REST synchronous fallback)
 * POST /api/chat
 */
export const sendChatMessage = async (team_name: string, question: string): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/api/chat', {
    team_name,
    question,
  });
  return response.data;
};

export interface StreamHandlers {
  onChunk: (token: string) => void;
  onComplete: (sources: SourceItem[], teamName: string) => void;
  onError: (error: Error) => void;
}

/**
 * 2b. Submit RAG Chat Question with SSE Token Streaming
 * POST /api/chat/stream
 */
export const sendChatMessageStream = async (
  team_name: string,
  question: string,
  handlers: StreamHandlers
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ team_name, question }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      let msg = 'Failed to connect to chat stream.';
      try {
        const parsed = JSON.parse(errorText);
        msg = parsed.detail || msg;
      } catch (e) {
        msg = errorText || msg;
      }
      throw new Error(msg);
    }

    if (!response.body) {
      throw new Error('No response body received for streaming.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            if (data.token) {
              handlers.onChunk(data.token);
            }
            if (data.done) {
              handlers.onComplete(data.sources || [], data.team_name || team_name);
            }
          } catch (e) {
            console.warn('Failed to parse SSE JSON chunk:', jsonStr, e);
          }
        }
      }
    }
  } catch (err: any) {
    handlers.onError(err instanceof Error ? err : new Error(String(err)));
  }
};

/**
 * 3. Retrieve Team Details
 * GET /api/teams/{team_name}
 */
export const getTeam = async (team_name: string): Promise<TeamData> => {
  const response = await apiClient.get<TeamData>(`/api/teams/${encodeURIComponent(team_name)}`);
  return response.data;
};

/**
 * 4. Retrieve Team Prompt History
 * GET /api/teams/{team_name}/prompts
 */
export const getTeamPrompts = async (team_name: string): Promise<PromptLog[]> => {
  const response = await apiClient.get<PromptLog[]>(`/api/teams/${encodeURIComponent(team_name)}/prompts`);
  return response.data;
};

/**
 * 5. Discover Official Competition Documents
 * GET /api/documents
 */
export const getDocuments = async (): Promise<any[]> => {
  const response = await apiClient.get<any[]>('/api/documents');
  return response.data;
};

/**
 * Helper to construct safe backend file download/view URL
 */
export const getDocumentFileUrl = (document_id: string): string => {
  return `${API_BASE_URL}/api/documents/${encodeURIComponent(document_id)}/file`;
};

/**
 * 6. Admin Login
 * POST /api/admin/login
 */
export const adminLoginApi = async (
  username: string,
  password: string
): Promise<{ access_token: string; username: string; role: string }> => {
  const response = await apiClient.post<{ access_token: string; username: string; role: string }>(
    '/api/admin/login',
    { username, password }
  );
  return response.data;
};

/**
 * 7. Admin Overview Metrics
 * GET /api/admin/overview
 */
export const getAdminOverviewApi = async (token: string): Promise<any> => {
  const response = await apiClient.get<any>('/api/admin/overview', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

/**
 * 8. Admin Registered Teams List
 * GET /api/admin/teams
 */
export const getAdminTeamsApi = async (token: string): Promise<any[]> => {
  const response = await apiClient.get<any[]>('/api/admin/teams', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

/**
 * 9. Admin Team Detail & Prompt Execution History
 * GET /api/admin/teams/{team_name}
 */
export const getAdminTeamDetailApi = async (token: string, team_name: string): Promise<any> => {
  const response = await apiClient.get<any>(`/api/admin/teams/${encodeURIComponent(team_name)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};
