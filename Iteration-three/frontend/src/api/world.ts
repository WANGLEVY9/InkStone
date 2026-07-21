import client from './client';
import type { WorldSetting, CreateWorldRequest, UpdateWorldRequest } from '@/types';

export const worldApi = {
  list: (projectId: string) =>
    client.get<WorldSetting[]>(`/projects/${projectId}/world/`),
  get: (projectId: string, worldId: string) =>
    client.get<WorldSetting>(`/projects/${projectId}/world/${worldId}`),
  create: (projectId: string, data: CreateWorldRequest) =>
    client.post<WorldSetting>(`/projects/${projectId}/world/`, data),
  update: (projectId: string, worldId: string, data: UpdateWorldRequest) =>
    client.post<WorldSetting>(`/projects/${projectId}/world/${worldId}/update`, data),
  delete: (projectId: string, worldId: string) =>
    client.post(`/projects/${projectId}/world/${worldId}/delete`),
};
