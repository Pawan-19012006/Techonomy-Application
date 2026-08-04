import { apiClient } from './axios';
import { Event, EventStatus } from '../types';

export const getEventApi = async (): Promise<Event> => {
  const response = await apiClient.get<Event>('/event');
  return response.data;
};

export const getEventStatusApi = async (): Promise<EventStatus> => {
  const response = await apiClient.get<EventStatus>('/event/status');
  return response.data;
};
