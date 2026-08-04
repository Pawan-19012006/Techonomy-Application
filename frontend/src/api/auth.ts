import { apiClient } from './axios';
import { TokenResponse, Team } from '../types';

export const loginApi = async (email: string, password: string): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/login', { email, password });
  return response.data;
};

export const getMeApi = async (): Promise<Team> => {
  const response = await apiClient.get<Team>('/auth/me');
  return response.data;
};
