/** Prefetch lazy route chunks during idle time to reduce first-navigation delay. */
const routeImports = [
  () => import('@/pages/Dashboard'),
  () => import('@/pages/world/WorldList'),
  () => import('@/pages/world/WorldEdit'),
  () => import('@/pages/characters/CharacterList'),
  () => import('@/pages/characters/CharacterEdit'),
  () => import('@/pages/outline/OutlineEditor'),
  () => import('@/pages/chapters/ChapterList'),
  () => import('@/pages/chapters/ChapterEdit'),
  () => import('@/pages/settings/ProjectSettings'),
  () => import('@/pages/settings/SystemSettings'),
  () => import('@/pages/chat/ChatPage'),
  () => import('@/pages/skills/SkillManager'),
  () => import('@/pages/skills/SkillEdit'),
];

let prefetched = false;

export function prefetchRouteChunks(): void {
  if (prefetched) return;
  prefetched = true;
  routeImports.forEach((load) => {
    load().catch(() => {
      /* ignore prefetch failures */
    });
  });
}

export function scheduleRoutePrefetch(): void {
  if (typeof window === 'undefined') return;
  const run = () => prefetchRouteChunks();
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(run, { timeout: 2000 });
    return;
  }
  globalThis.setTimeout(run, 300);
}
