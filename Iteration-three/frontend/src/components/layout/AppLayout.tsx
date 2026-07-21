import { useCallback, useEffect, useState, lazy, Suspense } from 'react';
import { Layout, theme } from 'antd';
import { Outlet, useLocation } from 'react-router-dom';
import IconSidebar from './IconSidebar';
import SecondaryNav from './SecondaryNav';
import { ProjectLoader } from '@/contexts/ProjectContext';
import { ChatProvider } from '@/contexts/ChatContext';
import { registerChatDrawerOpener } from '@/components/onboarding/chatDrawerBridge';

const DrawerChat = lazy(() => import('@/components/ai/DrawerChat'));

const { Content } = Layout;

const AppLayout = () => {
  const { token: { colorBgContainer } } = theme.useToken();
  const location = useLocation();
  const isChatPage = location.pathname.includes('/chat');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatEnabled, setChatEnabled] = useState(isChatPage);

  useEffect(() => {
    if (isChatPage) {
      setChatEnabled(true);
    }
  }, [isChatPage]);

  const handleDrawerOpenChange = useCallback((open: boolean) => {
    setDrawerOpen(open);
    if (open) {
      setChatEnabled(true);
      return;
    }
    if (!isChatPage) {
      setChatEnabled(false);
    }
  }, [isChatPage]);

  const handleRequestChatMount = useCallback(() => {
    setChatEnabled(true);
  }, []);

  useEffect(() => {
    if (isChatPage) return undefined;
    return registerChatDrawerOpener(() => {
      handleDrawerOpenChange(true);
    });
  }, [isChatPage, handleDrawerOpenChange]);

  const pageContent = (
    <>
      <Outlet />
      {!isChatPage && (
        <Suspense fallback={null}>
          <DrawerChat
            open={drawerOpen}
            onOpenChange={handleDrawerOpenChange}
            onRequestChatMount={handleRequestChatMount}
          />
        </Suspense>
      )}
    </>
  );

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <IconSidebar />
      <SecondaryNav />
      <Layout style={{ marginLeft: 264, height: '100vh' }}>
        <Content style={{
          padding: isChatPage ? 0 : 24,
          background: colorBgContainer,
          height: '100vh',
          overflow: isChatPage ? 'hidden' : 'auto',
          display: isChatPage ? 'flex' : 'block',
          flexDirection: isChatPage ? 'column' : undefined,
        }}>
          <ProjectLoader>
            {chatEnabled ? (
              <ChatProvider>{pageContent}</ChatProvider>
            ) : (
              pageContent
            )}
          </ProjectLoader>
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
