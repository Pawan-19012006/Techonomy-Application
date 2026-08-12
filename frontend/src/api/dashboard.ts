import { getTeam } from '../services/api';
import { DashboardData } from '../types';

export const getDashboardApi = async (): Promise<DashboardData> => {
  const saved = localStorage.getItem('techonomy_team');
  let teamName = 'TEAM-01';
  let memberNames: string[] = [];
  let startedAt = new Date().toISOString();

  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      teamName = parsed.team_name || teamName;
      memberNames = parsed.member_names || memberNames;
      startedAt = parsed.started_at || startedAt;
    } catch (e) {
      console.error('Failed to parse techonomy_team for dashboard', e);
    }
  }

  try {
    const remote = await getTeam(teamName);
    if (remote && remote.team_name) {
      teamName = remote.team_name;
      memberNames = remote.member_names || memberNames;
      startedAt = remote.started_at || startedAt;
    }
  } catch (err) {
    // Gracefully keep cached local team details if backend is unreachable
  }

  return {
    team_name: teamName,
    member_names: memberNames,
    started_at: startedAt,
    documents_available: 8,
  };
};
