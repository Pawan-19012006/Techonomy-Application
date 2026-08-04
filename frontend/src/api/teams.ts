import { apiClient } from './axios';
import { Team, QuestionMetrics, TeamHistory } from '../types';

export const getTeamMeApi = async (): Promise<Team> => {
  const response = await apiClient.get<Team>('/teams/me');
  return response.data;
};

export const getTeamQuestionsApi = async (): Promise<QuestionMetrics> => {
  const response = await apiClient.get<QuestionMetrics>('/teams/questions');
  return response.data;
};

export const getTeamHistoryApi = async (): Promise<TeamHistory> => {
  const response = await apiClient.get<TeamHistory>('/teams/history');
  return response.data;
};
