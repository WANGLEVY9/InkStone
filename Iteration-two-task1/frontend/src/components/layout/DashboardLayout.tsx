import { Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import IconSidebar from './IconSidebar';

const { Content } = Layout;

const DashboardLayout = () => {
  const { token: { colorBgContainer } } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <IconSidebar />
      <Layout style={{ marginLeft: 64 }}>
        <Content style={{
          padding: 24,
          background: colorBgContainer,
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default DashboardLayout;
