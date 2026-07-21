import { lazy, Suspense } from 'react';
import { App as AntApp, ConfigProvider } from 'antd';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from '@/contexts/ProjectContext';
import { OnboardingProvider } from '@/contexts/OnboardingContext';
import OnboardingGuide from '@/components/onboarding/OnboardingGuide';
import PageSkeleton from '@/components/common/PageSkeleton';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AppLayout from '@/components/layout/AppLayout';
import SystemLayout from '@/components/layout/SystemLayout';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const WorldList = lazy(() => import('@/pages/world/WorldList'));
const WorldEdit = lazy(() => import('@/pages/world/WorldEdit'));
const CharacterList = lazy(() => import('@/pages/characters/CharacterList'));
const CharacterEdit = lazy(() => import('@/pages/characters/CharacterEdit'));
const OutlineEditor = lazy(() => import('@/pages/outline/OutlineEditor'));
const ChapterList = lazy(() => import('@/pages/chapters/ChapterList'));
const ChapterEdit = lazy(() => import('@/pages/chapters/ChapterEdit'));
const ProjectSettings = lazy(() => import('@/pages/settings/ProjectSettings'));
const SystemSettings = lazy(() => import('@/pages/settings/SystemSettings'));
const ChatPage = lazy(() => import('@/pages/chat/ChatPage'));
const SkillManager = lazy(() => import('@/pages/skills/SkillManager'));
const SkillEdit = lazy(() => import('@/pages/skills/SkillEdit'));

const App = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#C8323D',
          colorPrimaryHover: '#9F2530',
          colorPrimaryActive: '#9F2530',
          colorPrimaryBg: '#F8E8E5',
          colorPrimaryBgHover: '#F2D6D2',
          colorPrimaryBorder: '#E0B5B0',
          colorSuccess: '#2E5A4D',
          colorWarning: '#B8924A',
          colorBgLayout: '#F5EFE3',
          colorBgContainer: '#FBF6EA',
          colorBgElevated: '#FBF6EA',
          colorText: '#1F1A17',
          colorTextSecondary: '#4A3F33',
          colorTextTertiary: '#6E5F4F',
          colorTextQuaternary: '#A89B85',
          colorBorder: '#C9B999',
          colorBorderSecondary: '#E0D5C2',
          borderRadius: 4,
          borderRadiusLG: 8,
          borderRadiusSM: 2,
          fontFamily:
            "'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', 'STSong', 'SimSun', serif",
        },
        components: {
          Button: { fontWeight: 500, controlHeight: 36 },
          Card: { borderRadiusLG: 8, paddingLG: 20 },
          Tag: { defaultBg: '#F8E8E5', defaultColor: '#C8323D', borderRadiusSM: 2 },
          Menu: { itemSelectedColor: '#C8323D', itemHoverColor: '#C8323D' },
          Tree: { directoryNodeSelectedBg: '#F8E8E5' },
          Input: { activeBorderColor: '#C8323D', hoverBorderColor: '#9F2530' },
          Layout: { headerBg: '#FBF6EA', siderBg: '#3A2A1F' },
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <OnboardingProvider>
            <ProjectProvider>
              <Suspense fallback={<PageSkeleton />}>
                <Routes>
                  <Route element={<DashboardLayout />}>
                    <Route path="/" element={<Dashboard />} />
                  </Route>
                  <Route element={<SystemLayout />}>
                    <Route path="/settings" element={<SystemSettings />} />
                    <Route path="/skills" element={<SkillManager />} />
                    <Route path="/skills/new" element={<SkillEdit />} />
                    <Route path="/skills/:skillName/edit" element={<SkillEdit />} />
                  </Route>
                  <Route element={<AppLayout />}>
                    <Route path="/projects/:id/world" element={<WorldList />} />
                    <Route path="/projects/:id/world/:worldId" element={<WorldEdit />} />
                    <Route path="/projects/:id/characters" element={<CharacterList />} />
                    <Route path="/projects/:id/characters/:charId" element={<CharacterEdit />} />
                    <Route path="/projects/:id/outline" element={<OutlineEditor />} />
                    <Route path="/projects/:id/chapters" element={<ChapterList />} />
                    <Route path="/projects/:id/chapters/:chapterId" element={<ChapterEdit />} />
                    <Route path="/projects/:id/chat" element={<ChatPage />} />
                    <Route path="/projects/:id/chat/:sessionId" element={<ChatPage />} />
                    <Route path="/projects/:id/settings" element={<ProjectSettings />} />
                  </Route>
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
              <OnboardingGuide />
            </ProjectProvider>
          </OnboardingProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;
