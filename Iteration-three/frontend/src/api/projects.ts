import client from './client';
import type { Project, CreateProjectRequest, UpdateProjectRequest } from '@/types';

export const projectsApi = {
  list: (limit = 100, offset = 0) =>
    client.get<Project[]>('/projects/', { params: { limit, offset } }),
  get: (id: string) =>
    client.get<Project>(`/projects/${id}`),
  create: (data: CreateProjectRequest) =>
    client.post<Project>('/projects/', data),
  update: (id: string, data: UpdateProjectRequest) =>
    client.patch<Project>(`/projects/${id}`, data),
  delete: (id: string) =>
    client.delete(`/projects/${id}`),
};
