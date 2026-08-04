import { apiClient } from './axios';
import { ChatQueryResponse } from '../types';

export const postChatQueryApi = async (query: string): Promise<ChatQueryResponse> => {
  const response = await apiClient.post<ChatQueryResponse>('/chat/query', { query });
  return response.data;
};
