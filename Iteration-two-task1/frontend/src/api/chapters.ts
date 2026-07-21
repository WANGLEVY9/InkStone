import client from './client';
import type { Chapter, CreateChapterRequest, UpdateChapterRequest } from '@/types';

export const chaptersApi = {
  list: (projectId: string) =>
    client.get<Chapter[]>(`/projects/${projectId}/chapters/`),
  get: (projectId: string, chapterId: string) =>
    client.get<Chapter>(`/projects/${projectId}/chapters/${chapterId}`),
  create: (projectId: string, data: CreateChapterRequest) =>
    client.post<Chapter>(`/projects/${projectId}/chapters/`, data),
  update: (projectId: string, chapterId: string, data: UpdateChapterRequest) =>
    client.post<Chapter>(`/projects/${projectId}/chapters/${chapterId}/update`, data),
  delete: (projectId: string, chapterId: string) =>
    client.post(`/projects/${projectId}/chapters/${chapterId}/delete`),
};
