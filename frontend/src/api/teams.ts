import { getTeam, getTeamPrompts } from '../services/api';
import { PromptLog, QuestionMetrics, TeamData, TeamHistory } from '../types';

export const getTeamMeApi = async (team_name?: string): Promise<TeamData> => {
  const storedTeamRaw = localStorage.getItem('techonomy_team');
  const name = team_name || (storedTeamRaw ? JSON.parse(storedTeamRaw).team_name : 'TEAM-01');
  return getTeam(name);
};

export const getTeamQuestionsApi = async (): Promise<QuestionMetrics> => {
  return {
    question_limit: 10,
    questions_used: 0,
    questions_remaining: 10,
  };
};

export const getTeamHistoryApi = async (team_name?: string): Promise<TeamHistory> => {
  const storedTeamRaw = localStorage.getItem('techonomy_team');
  const name = team_name || (storedTeamRaw ? JSON.parse(storedTeamRaw).team_name : 'TEAM-01');
  const logs: PromptLog[] = await getTeamPrompts(name);
  return {
    logs,
    total_count: logs.length,
  };
};
