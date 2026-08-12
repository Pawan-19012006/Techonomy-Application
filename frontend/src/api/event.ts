import { Event, EventStatus } from '../types';

export const getEventApi = async (): Promise<Event> => {
  const now = new Date().toISOString();
  return {
    id: 1,
    name: 'Techonomy Challenge 2026',
    description: 'Analyze company documents and deliver strategic insights.',
    business_objective: 'Increase Revenue by 20%',
    rules: 'No question quota limit.',
    start_time: now,
    end_time: now,
    question_limit: 999,
    is_active: true,
    status: 'ACTIVE',
    created_at: now,
  };
};

export const getEventStatusApi = async (): Promise<EventStatus> => {
  return {
    event_id: 1,
    event_name: 'Techonomy Challenge 2026',
    status: 'ACTIVE',
    question_limit: 999,
    timer_remaining_seconds: 3600,
    started: true,
    finished: false,
  };
};
