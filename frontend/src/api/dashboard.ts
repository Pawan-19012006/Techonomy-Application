import { apiClient } from './axios';
import { DashboardData } from '../types';

export const getDashboardApi = async (): Promise<DashboardData> => {
  const response = await apiClient.get<DashboardData>('/dashboard');
  return response.data;
};
