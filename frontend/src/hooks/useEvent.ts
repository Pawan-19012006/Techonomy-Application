import { useQuery } from '@tanstack/react-query';
import { getEventApi, getEventStatusApi } from '../api/event';

export const useEventDetails = () => {
  return useQuery({
    queryKey: ['event-details'],
    queryFn: getEventApi,
  });
};

export const useEventStatus = () => {
  return useQuery({
    queryKey: ['event-status'],
    queryFn: getEventStatusApi,
    refetchInterval: 5000, // Poll timer every 5 seconds for backend accuracy
  });
};
