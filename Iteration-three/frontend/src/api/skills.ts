import client from './client';
import type { Skill, CreateSkillRequest, UpdateSkillRequest } from '@/types';

export const skillsApi = {
  list: () => client.get<Skill[]>('/skills/'),
  get: (name: string) => client.get<Skill>(`/skills/${name}`),
  create: (data: CreateSkillRequest) => client.post<Skill>('/skills/', data),
  update: (name: string, data: UpdateSkillRequest) =>
    client.post<Skill>(`/skills/${name}/update`, data),
  delete: (name: string) => client.post(`/skills/${name}/delete`),
};
