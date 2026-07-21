import client from './client';
import type { ConfigResponse, UpdateConfigRequest, ConfigTestResponse } from '@/types';

export const KEEP_EXISTING = '__KEEP_EXISTING__';

export const configApi = {
  get: () => client.get<ConfigResponse>('/config'),
  update: (data: UpdateConfigRequest) => client.post<ConfigResponse>('/config/update', data),
  test: () => client.post<ConfigTestResponse>('/config/test'),
};
