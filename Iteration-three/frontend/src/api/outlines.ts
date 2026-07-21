import client from './client';
import type { Outline, CreateOutlineRequest, UpdateOutlineRequest } from '@/types';

export const outlinesApi = {
  getRoot: (projectId: string) =>
    client.get<Outline>(`/projects/${projectId}/outlines/`),
  get: (projectId: string, outlineId: string) =>
    client.get<Outline>(`/projects/${projectId}/outlines/${outlineId}`),
  getChildren: (projectId: string, outlineId: string) =>
    client.get<Outline[]>(`/projects/${projectId}/outlines/${outlineId}/children`),
  getTree: (projectId: string, outlineId: string) =>
    client.get<Outline>(`/projects/${projectId}/outlines/${outlineId}/tree`),
  create: (projectId: string, data: CreateOutlineRequest) =>
    client.post<Outline>(`/projects/${projectId}/outlines/`, data),
  update: (projectId: string, outlineId: string, data: UpdateOutlineRequest) =>
    client.post<Outline>(`/projects/${projectId}/outlines/${outlineId}/update`, data),
  delete: (projectId: string, outlineId: string) =>
    client.post(`/projects/${projectId}/outlines/${outlineId}/delete`),
};
