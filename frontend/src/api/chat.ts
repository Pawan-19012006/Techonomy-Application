import { sendChatMessage } from '../services/api';
import { ChatResponse } from '../types';

export const postChatQueryApi = async (query: string, team_name?: string): Promise<ChatResponse> => {
  const storedTeamRaw = localStorage.getItem('techonomy_team');
  const name = team_name || (storedTeamRaw ? JSON.parse(storedTeamRaw).team_name : 'TEAM-01');
  return sendChatMessage(name, query);
};
