import client from './client';
import type { Character, CreateCharacterRequest, UpdateCharacterRequest } from '@/types';

export const charactersApi = {
  list: (projectId: string) =>
    client.get<Character[]>(`/projects/${projectId}/characters/`),
  get: (projectId: string, characterId: string) =>
    client.get<Character>(`/projects/${projectId}/characters/${characterId}`),
  create: (projectId: string, data: CreateCharacterRequest) =>
    client.post<Character>(`/projects/${projectId}/characters/`, data),
  update: (projectId: string, characterId: string, data: UpdateCharacterRequest) =>
    client.post<Character>(`/projects/${projectId}/characters/${characterId}/update`, data),
  delete: (projectId: string, characterId: string) =>
    client.post(`/projects/${projectId}/characters/${characterId}/delete`),
};
