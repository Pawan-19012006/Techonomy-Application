import { apiClient } from '../api/axios';
import { ChatResponse, PromptLog, TeamData } from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

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
 * 2. Submit RAG Chat Question
 * POST /api/chat
 */
export const sendChatMessage = async (team_name: string, question: string): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/api/chat', {
    team_name,
    question,
  });
  return response.data;
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
