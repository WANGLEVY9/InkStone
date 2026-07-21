import { Layout, Menu } from 'antd';
import {
  GlobalOutlined,
  UserOutlined,
  OrderedListOutlined,
  BookOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useProjectContext } from '@/contexts/ProjectContext';

const { Sider } = Layout;

const SecondaryNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentProject } = useProjectContext();

  if (!currentProject) return null;

  const basePath = `/projects/${currentProject.id}`;

  const items = [
    { key: `${basePath}/world`, icon: <GlobalOutlined />, label: '世界观' },
    { key: `${basePath}/characters`, icon: <UserOutlined />, label: '角色' },
    { key: `${basePath}/outline`, icon: <OrderedListOutlined />, label: '大纲' },
    { key: `${basePath}/chapters`, icon: <BookOutlined />, label: '章节' },
    { key: `${basePath}/chat`, icon: <MessageOutlined />, label: 'AI 助手' },
  ];

  const selectedKey = items.find((item) => location.pathname.startsWith(item.key))?.key || '';

  return (
    <Sider
      width={200}
      theme="light"
      style={{
        height: '100vh',
        position: 'fixed',
        left: 64,
        top: 0,
        bottom: 0,
        background: 'var(--paper-elevated)',
        borderRight: '1px solid var(--silk-line)',
        overflow: 'auto',
      }}
    >
      <div
        title={currentProject.name}
        style={{
          padding: '22px 18px 6px',
          fontFamily: 'var(--font-display)',
          fontSize: 16,
          fontWeight: 700,
          color: 'var(--ink-heavy)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          letterSpacing: '0.06em',
        }}
      >
        {currentProject.name}
      </div>
      <div
        style={{
          marginLeft: 18,
          marginBottom: 14,
          height: 1,
          width: 28,
          background: 'var(--vermilion)',
        }}
      />
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onClick={({ key }) => navigate(key)}
        style={{
          borderRight: 0,
          background: 'transparent',
          fontFamily: 'var(--font-body)',
          fontSize: 14,
        }}
      />
    </Sider>
  );
};

export default SecondaryNav;
