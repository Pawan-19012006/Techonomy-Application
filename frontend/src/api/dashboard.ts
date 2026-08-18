import { getTeam } from '../services/api';
import { DashboardData } from '../types';

export const getDashboardApi = async (): Promise<DashboardData> => {
  const saved = localStorage.getItem('techonomy_team');
  let teamName = '';
  let memberNames: string[] = [];
  let startedAt = '';
  let questionLimit = 10;
  let questionsUsed = 0;
  let questionsRemaining = 10;

  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      teamName = parsed.team_name || teamName;
      memberNames = parsed.member_names || memberNames;
      startedAt = parsed.started_at || startedAt;
      if (parsed.question_limit !== undefined) questionLimit = parsed.question_limit;
      if (parsed.questions_used !== undefined) questionsUsed = parsed.questions_used;
      if (parsed.questions_remaining !== undefined) questionsRemaining = parsed.questions_remaining;
    } catch (e) {
      console.error('Failed to parse techonomy_team for dashboard', e);
    }
  }

  if (teamName) {
    try {
      const remote = await getTeam(teamName);
      if (remote && remote.team_name) {
        teamName = remote.team_name;
        memberNames = remote.member_names || memberNames;
        startedAt = remote.started_at || startedAt;
        questionLimit = remote.question_limit ?? 10;
        questionsUsed = remote.questions_used ?? 0;
        questionsRemaining = remote.questions_remaining ?? Math.max(0, questionLimit - questionsUsed);
      }
    } catch (err) {
      // Gracefully keep cached local team details if backend is unreachable
    }
  }

  return {
    team_name: teamName,
    member_names: memberNames,
    started_at: startedAt,
    documents_available: 8,
    question_limit: questionLimit,
    questions_used: questionsUsed,
    questions_remaining: questionsRemaining,
  };
};
