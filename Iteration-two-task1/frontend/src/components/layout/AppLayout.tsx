import { Layout, theme } from 'antd';
import { Outlet, useLocation } from 'react-router-dom';
import IconSidebar from './IconSidebar';
import SecondaryNav from './SecondaryNav';
import { ProjectLoader } from '@/contexts/ProjectContext';
import { ChatProvider } from '@/contexts/ChatContext';
import DrawerChat from '@/components/ai/DrawerChat';

const { Content } = Layout;

const AppLayout = () => {
  const { token: { colorBgContainer } } = theme.useToken();
  const location = useLocation();
  const isChatPage = location.pathname.includes('/chat');

  return (
    <>
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
              <ChatProvider>
                <Outlet />
                <DrawerChat />
              </ChatProvider>
            </ProjectLoader>
          </Content>
        </Layout>
      </Layout>
    </>
  );
};

export default AppLayout;
