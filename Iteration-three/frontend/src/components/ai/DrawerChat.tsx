import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Badge, Button, Drawer, theme } from 'antd';
import { MessageOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { useProjectContext } from '@/contexts/ProjectContext';
import { useChatContext } from '@/contexts/ChatContext';
import { Conversations } from '@ant-design/x';
import Draggable from 'react-draggable';
import ChatCore from './ChatCore';

const SIDEBAR_WIDTH = 250;

const DrawerChat = ({
  open: openProp,
  onOpenChange,
  onRequestChatMount,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  onRequestChatMount?: () => void;
}) => {
  const [openLocal, setOpenLocal] = useState(false);
  const open = openProp ?? openLocal;
  const setOpen = useCallback((next: boolean | ((prev: boolean) => boolean)) => {
    const current = openProp ?? openLocal;
    const resolved = typeof next === 'function' ? next(current) : next;
    if (resolved) {
      onRequestChatMount?.();
    }
    if (onOpenChange) {
      onOpenChange(resolved);
    } else {
      setOpenLocal(resolved);
    }
  }, [onOpenChange, onRequestChatMount, openProp, openLocal]);
  const [drawerSize, setDrawerSize] = useState(800);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { currentProject } = useProjectContext();
  const chat = useChatContext();
  const location = useLocation();
  const { token } = theme.useToken();
  const nodeRef = useRef<HTMLDivElement>(null);
  const dragStartPos = useRef<{ x: number; y: number } | null>(null);

  // Auto-close drawer when chat page is active
  const isChatPage = location.pathname.includes('/chat');
  useEffect(() => {
    if (isChatPage && open) {
      setOpen(false);
    }
  }, [isChatPage, open, setOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'j') {
        e.preventDefault();
        setOpen(prev => !prev);
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  const {
    sessions, activeKey, setActiveKey, deleteSession, renameSession,
  } = chat || {};

  const conversationItems = useMemo(() =>
    (sessions || []).map(s => ({
      key: s.id,
      label: s.title || `会话 ${s.id.substring(0, 8)}...`,
      icon: <MessageOutlined />,
    })),
    [sessions],
  );

  const conversationMenu = useCallback((conversation: { key: string }) => ({
    items: [
      { key: 'rename', label: '重命名', icon: <EditOutlined /> },
      { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'delete') {
        deleteSession?.(conversation.key);
      } else if (key === 'rename') {
        const newTitle = prompt('请输入新名称:');
        if (newTitle?.trim()) {
          renameSession?.(conversation.key, newTitle.trim());
        }
      }
    },
  }), [deleteSession, renameSession]);

  if (!currentProject) return null;
  if (isChatPage) return null;

  return (
    <>
      <Draggable
        nodeRef={nodeRef as React.RefObject<HTMLElement>}
        bounds="body"
        defaultPosition={{ x: 0, y: 0 }}
        onStart={(_, data) => { dragStartPos.current = { x: data.x, y: data.y }; }}
        onStop={(_, data) => {
          const start = dragStartPos.current;
          const moved = start && (Math.abs(data.x - start.x) > 3 || Math.abs(data.y - start.y) > 3);
          if (!moved) setOpen(true);
          dragStartPos.current = null;
        }}
      >
        <div
          ref={nodeRef}
          style={{
            position: 'fixed',
            right: 24,
            bottom: 24,
            zIndex: 1000,
            cursor: 'grab',
            touchAction: 'none',
          }}
        >
          <Badge size="small">
            <div
              data-tour-project-chat-fab
              style={{
                width: 48,
                height: 48,
                borderRadius: 'var(--radius-md)',
                background: `linear-gradient(135deg, ${token.colorPrimary}, ${token.colorPrimaryActive})`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--paper-base)',
                fontSize: 22,
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
                boxShadow: `0 3px 12px ${token.colorPrimary}66, inset 0 0 0 1px rgba(255, 255, 255, 0.18)`,
                textShadow: '0 1px 0 rgba(0, 0, 0, 0.18)',
                cursor: 'grab',
                transition: 'transform 0.2s, box-shadow 0.2s',
                userSelect: 'none',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.transform = 'scale(1.08)';
                (e.currentTarget as HTMLDivElement).style.boxShadow = `0 5px 20px ${token.colorPrimary}88, inset 0 0 0 1px rgba(255, 255, 255, 0.22)`;
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.transform = 'scale(1)';
                (e.currentTarget as HTMLDivElement).style.boxShadow = `0 3px 12px ${token.colorPrimary}66, inset 0 0 0 1px rgba(255, 255, 255, 0.18)`;
              }}
              title="AI 助手 (Ctrl+J)"
              aria-label="打开 AI 问询"
            >
              问
            </div>
          </Badge>
        </div>
      </Draggable>

      {/* Conversation sidebar - outside drawer, to the left */}
      <div
        style={{
          position: 'fixed',
          right: drawerSize,
          top: 0,
          bottom: 0,
          width: open && sidebarOpen ? SIDEBAR_WIDTH : 0,
          zIndex: 1001,
          background: token.colorBgLayout,
          borderRight: open && sidebarOpen ? `1px solid ${token.colorBorderSecondary}` : 'none',
          boxShadow: open && sidebarOpen ? '2px 0 8px rgba(0,0,0,0.08)' : 'none',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transition: 'width 0.25s ease, border-right 0.25s ease, box-shadow 0.25s ease',
        }}
      >
        <div style={{ width: SIDEBAR_WIDTH, display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{
            padding: '12px 12px 8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            flexShrink: 0,
          }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: token.colorText }}>会话</span>
            <Button
              type="text"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => chat?.createSession()}
              title="新建会话"
            />
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            <Conversations
              items={conversationItems}
              activeKey={activeKey || undefined}
              onActiveChange={(key) => setActiveKey?.(key)}
              menu={conversationMenu}
            />
          </div>
        </div>
      </div>

      <Drawer
        title={null}
        closable={false}
        placement="right"
        size={drawerSize}
        resizable={{
          onResize: (newSize) => setDrawerSize(newSize),
        }}
        maxSize={800}
        open={open}
        onClose={() => setOpen(false)}
        destroyOnClose={false}
        styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100%' } }}
      >
        <ChatCore mode="drawer" sidebarOpen={sidebarOpen} onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />
      </Drawer>
    </>
  );
};

export default DrawerChat;
