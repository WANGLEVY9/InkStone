import client from './client';
import type { Session, CreateSessionRequest } from '@/types';

export const sessionsApi = {
  list: (projectId: string, limit = 50, offset = 0) =>
    client.get<Session[]>(`/projects/${projectId}/sessions/`, { params: { limit, offset } }),
  create: (projectId: string, data?: CreateSessionRequest) =>
    client.post<Session>(`/projects/${projectId}/sessions/`, data),
  delete: (projectId: string, sessionId: string) =>
    client.delete(`/projects/${projectId}/sessions/${sessionId}`),
  getHistory: (projectId: string, sessionId: string) =>
    client.get(`/projects/${projectId}/sessions/${sessionId}/history`),
};
