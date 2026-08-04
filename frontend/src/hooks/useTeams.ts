import { useQuery } from '@tanstack/react-query';
import { getTeamMeApi, getTeamQuestionsApi, getTeamHistoryApi } from '../api/teams';

export const useTeamProfile = () => {
  return useQuery({
    queryKey: ['team-profile'],
    queryFn: getTeamMeApi,
  });
};

export const useTeamQuestions = () => {
  return useQuery({
    queryKey: ['team-questions'],
    queryFn: getTeamQuestionsApi,
  });
};

export const useTeamHistory = () => {
  return useQuery({
    queryKey: ['team-history'],
    queryFn: getTeamHistoryApi,
  });
};
