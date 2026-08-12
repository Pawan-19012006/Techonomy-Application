import { useQuery } from '@tanstack/react-query';
import { getTeamMeApi, getTeamQuestionsApi, getTeamHistoryApi } from '../api/teams';

export const useTeamProfile = (teamName?: string) => {
  return useQuery({
    queryKey: ['team-profile', teamName],
    queryFn: () => getTeamMeApi(teamName),
  });
};

export const useTeamQuestions = () => {
  return useQuery({
    queryKey: ['team-questions'],
    queryFn: getTeamQuestionsApi,
  });
};

export const useTeamHistory = (teamName?: string) => {
  return useQuery({
    queryKey: ['team-history', teamName],
    queryFn: () => getTeamHistoryApi(teamName),
  });
};
