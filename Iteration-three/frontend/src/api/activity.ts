import client from './client';
import type { HeatmapResponse } from '@/types';

export const activityApi = {
  getHeatmap: (days = 365) =>
    client.get<HeatmapResponse>('/activity/heatmap', { params: { days } }),
};
