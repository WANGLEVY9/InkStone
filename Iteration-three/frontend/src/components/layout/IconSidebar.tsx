import { Layout } from 'antd';
import { HomeOutlined, SettingOutlined, ApiOutlined, BookOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useProjectContext } from '@/contexts/ProjectContext';

const { Sider } = Layout;

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  dataTour?: string;
}

const SidebarItem = ({ icon, label, active, onClick, dataTour }: SidebarItemProps) => {
  const tourProps = dataTour ? { [`data-tour-${dataTour}`]: '' } as Record<string, string> : {};

  return (
  <div
    {...tourProps}
    onClick={onClick}
    title={label}
    style={{
      position: 'relative',
      width: 64,
      height: 56,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: active ? 'var(--vermilion)' : 'rgba(245, 239, 227, 0.7)',
      fontSize: 18,
      transition: 'color 0.2s',
    }}
    onMouseEnter={(e) => {
      if (!active) e.currentTarget.style.color = 'rgba(245, 239, 227, 1)';
    }}
    onMouseLeave={(e) => {
      if (!active) e.currentTarget.style.color = 'rgba(245, 239, 227, 0.7)';
    }}
  >
    {active && (
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 14,
          bottom: 14,
          width: 2,
          background: 'var(--vermilion)',
        }}
      />
    )}
    {icon}
  </div>
  );
};

const IconSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentProject } = useProjectContext();

  const isDashboard = location.pathname === '/';
  const settingsPath = currentProject ? `/projects/${currentProject.id}/settings` : null;
  const isSettings = settingsPath ? location.pathname === settingsPath : false;
  const isSystemSettings = location.pathname === '/settings';
  const isSkills = location.pathname === '/skills' || location.pathname.startsWith('/skills/');

  return (
    <Sider
      width={64}
      collapsedWidth={64}
      collapsed
      style={{
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 100,
        background: 'var(--wood-deep)',
        borderRight: '1px solid var(--wood-mid)',
        boxShadow: 'inset -1px 0 0 rgba(255, 255, 255, 0.04)',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          alignItems: 'center',
          paddingTop: 14,
        }}
      >
        <div
          onClick={() => navigate('/')}
          title="砚台 · 首页"
          style={{
            width: 40,
            height: 40,
            background: 'var(--vermilion)',
            color: '#F5EFE3',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: 22,
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            boxShadow:
              '0 2px 4px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.18), inset 0 -1px 0 rgba(0,0,0,0.25)',
            textShadow: '0 1px 0 rgba(0,0,0,0.3)',
            marginBottom: 18,
            letterSpacing: 0,
            transition: 'transform 0.2s ease',
            userSelect: 'none',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.06)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          砚
        </div>

        <SidebarItem
          icon={<HomeOutlined />}
          label="首页"
          active={isDashboard}
          onClick={() => navigate('/')}
        />

        <SidebarItem
          icon={<BookOutlined />}
          label="技能"
          active={isSkills}
          onClick={() => navigate('/skills')}
        />

        <div style={{ flex: 1 }} />

        <SidebarItem
          icon={<ApiOutlined />}
          label="系统设置"
          active={isSystemSettings}
          onClick={() => navigate('/settings')}
        />

        {settingsPath && (
          <SidebarItem
            dataTour="nav-settings"
            icon={<SettingOutlined />}
            label="设置"
            active={isSettings}
            onClick={() => navigate(settingsPath)}
          />
        )}

      </div>
    </Sider>
  );
};

export default IconSidebar;
