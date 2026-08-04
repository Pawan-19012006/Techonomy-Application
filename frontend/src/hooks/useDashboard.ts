import { useQuery } from '@tanstack/react-query';
import { getDashboardApi } from '../api/dashboard';

export const useDashboard = () => {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardApi,
    refetchInterval: 10000, // Auto-refresh dashboard metrics every 10s
  });
};
