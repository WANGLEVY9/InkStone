import { useState, useMemo, useCallback } from 'react';
import { Bubble, Sender, Conversations, Actions, XProvider } from '@ant-design/x';
import { XMarkdown } from '@ant-design/x-markdown';
import {
  RobotOutlined,
  MenuOutlined,
  PlusOutlined,
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import { Collapse, Spin, Typography, Alert } from 'antd';
import { useChatContext } from '@/contexts/ChatContext';
import { useProjectContext } from '@/contexts/ProjectContext';
import WelcomeScreen from './WelcomeScreen';
import type { ChatBubbleMessage, ChatTimelineEvent } from '@/types';

interface ChatCoreProps {
  mode: 'drawer' | 'page';
  sidebarOpen?: boolean;
  onSidebarToggle?: () => void;
}

type ToolKind = 'delegate' | 'read' | 'write';

const TOOL_TAG_CLASS: Record<ToolKind, string> = {
  delegate: 'seal-tag-bamboo',
  read: 'seal-tag-gold',
  write: 'seal-tag',
};

const TOOL_LABELS: Record<ToolKind, string> = {
  delegate: '委',
  read: '阅',
  write: '记',
};

const getToolKind = (event: ChatTimelineEvent): ToolKind => {
  if (event.isDelegate) return 'delegate';
  if (event.isReadOnly) return 'read';
  return 'write';
};

/** Renders timeline events in chronological order */
const TimelineView = ({ events, depth = 0 }: { events: ChatTimelineEvent[]; depth?: number }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {events.map((event, i) => {
        if (event.type === 'thinking' && event.content) {
          return (
            <Collapse
              key={i}
              size="small"
              items={[{
                key: 'thinking',
                label: (
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 11,
                      color: 'var(--ink-medium)',
                      fontFamily: 'var(--font-display)',
                      letterSpacing: '0.06em',
                      fontWeight: 500,
                    }}
                  >
                    <span
                      className="seal-stamp"
                      style={{ width: 16, height: 16, fontSize: 9 }}
                      aria-hidden="true"
                    >
                      思
                    </span>
                    斟酌
                  </span>
                ),
                children: (
                  <Typography>
                    <pre style={{
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontSize: 12,
                      lineHeight: 1.7,
                      color: 'var(--ink-medium)',
                      fontFamily: 'var(--font-body)',
                      maxHeight: 260,
                      overflow: 'auto',
                    }}>
                      {event.content}
                    </pre>
                  </Typography>
                ),
              }]}
              style={{
                background: 'var(--paper-sunken)',
                borderColor: 'var(--silk-line)',
                borderLeft: '2px solid var(--ink-light)',
              }}
            />
          );
        }

        if (event.type === 'text' && event.content) {
          return (
            <div
              key={i}
              style={{
                fontSize: 14,
                lineHeight: 1.85,
                color: 'var(--ink-heavy)',
                fontFamily: 'var(--font-body)',
              }}
            >
              <XMarkdown>{event.content}</XMarkdown>
            </div>
          );
        }

        if (event.type === 'tool') {
          const toolKind = getToolKind(event);
          const hasSubTimeline = event.isDelegate && event.subTimeline && event.subTimeline.length > 0;
          const isRunning = event.status === 'running';

          return (
            <Collapse
              key={i}
              size="small"
              items={[{
                key: 'tool',
                label: (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                    <span style={{
                      width: 7, height: 7, borderRadius: '50%',
                      background: isRunning ? 'var(--gold-leaf)' : 'var(--bamboo)',
                      boxShadow: isRunning ? '0 0 6px rgba(184,146,74,0.5)' : 'none',
                      flexShrink: 0,
                    }} />
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 500,
                        color: 'var(--ink-heavy)',
                        background: 'var(--paper-sunken)',
                        padding: '0 6px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 11,
                      }}
                    >
                      {event.name}
                    </span>
                    <span
                      className={`ant-tag ${TOOL_TAG_CLASS[toolKind]}`}
                      style={{ fontSize: 10, lineHeight: '16px' }}
                    >
                      {TOOL_LABELS[toolKind]}
                    </span>
                    {isRunning && <Spin size="small" />}
                  </div>
                ),
                children: event.isDelegate ? (
                  hasSubTimeline ? (
                    <TimelineView events={event.subTimeline!} depth={depth + 1} />
                  ) : (
                    <span style={{ fontSize: 12, color: 'var(--ink-light)', fontStyle: 'italic' }}>
                      未见副手记录
                    </span>
                  )
                ) : event.result != null ? (
                  (() => {
                    if (event.name === 'load_skill' && typeof event.result === 'string') {
                      const match = event.result.match(/^Loaded skill: ([^\n]+)\n\n([\s\S]*)$/);
                      if (match) {
                        const skillName = match[1];
                        const skillContent = match[2];
                        return (
                          <div>
                            <div style={{
                              marginBottom: 8,
                              fontSize: 12,
                              fontFamily: 'var(--font-mono)',
                              color: 'var(--ink-heavy)',
                            }}>
                              <span style={{
                                background: 'var(--paper-sunken)',
                                padding: '2px 8px',
                                borderRadius: 'var(--radius-sm)',
                              }}>
                                {skillName}
                              </span>
                            </div>
                            <div style={{
                              maxHeight: 300,
                              overflow: 'auto',
                              fontSize: 12,
                              lineHeight: 1.6,
                            }}>
                              <XMarkdown>{skillContent}</XMarkdown>
                            </div>
                          </div>
                        );
                      }
                    }
                    return (
                      <Typography>
                        <pre style={{
                          margin: 0,
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          fontSize: 12,
                          lineHeight: 1.6,
                          color: 'var(--ink-medium)',
                          fontFamily: 'var(--font-mono)',
                          maxHeight: 300,
                          overflow: 'auto',
                        }}>
                          {typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2)}
                        </pre>
                      </Typography>
                    );
                  })()
                ) : null,
              }]}
              style={{
                background: event.isDelegate ? 'var(--bamboo-bg)' : 'var(--paper-elevated)',
                borderColor: event.isDelegate ? 'rgba(46, 90, 77, 0.20)' : 'var(--silk-line)',
                borderLeft: event.isDelegate ? '2px solid var(--bamboo)' : undefined,
              }}
            />
          );
        }

        if (event.type === 'error' && event.content) {
          return (
            <div key={i} style={{
              padding: '8px 12px',
              background: 'var(--vermilion-bg)',
              border: '1px solid rgba(159, 37, 48, 0.30)',
              borderLeft: '3px solid #A93F3F',
              borderRadius: 'var(--radius-sm)',
              fontSize: 12,
              color: '#A93F3F',
              fontFamily: 'var(--font-body)',
              lineHeight: 1.7,
            }}>
              {event.content}
            </div>
          );
        }

        if (event.type === 'system' && event.content) {
          return (
            <div key={i} style={{
              textAlign: 'center',
              fontSize: 11,
              color: 'var(--ink-light)',
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.05em',
              padding: '2px 0',
            }}>
              {event.content}
            </div>
          );
        }

        return null;
      })}
    </div>
  );
};

/**
 * Inner component that assumes chat context is available.
 */
const ChatCoreInner = ({ mode, chat, sidebarOpen: sidebarOpenProp, onSidebarToggle }: ChatCoreProps & { chat: NonNullable<ReturnType<typeof useChatContext>> }) => {
  const { currentProject } = useProjectContext();
  const [sidebarOpenLocal, setSidebarOpenLocal] = useState(mode === 'page');
  const [inputValue, setInputValue] = useState('');

  const sidebarOpen = mode === 'drawer' ? (sidebarOpenProp ?? false) : sidebarOpenLocal;
  const toggleSidebar = mode === 'drawer' ? (onSidebarToggle ?? (() => {})) : () => setSidebarOpenLocal(!sidebarOpenLocal);

  const {
    sessions, activeKey, setActiveKey, messages, setMessages, isRequesting, loadingHistory,
    sendMessage: sendMessageRaw, cancel, createSession, deleteSession, renameSession,
  } = chat;

  const sendMessage = useCallback((msg: string) => {
    sendMessageRaw(msg);
    setInputValue('');
  }, [sendMessageRaw]);

  const handleCreateSession = useCallback(async () => {
    await createSession();
  }, [createSession]);

  const handleFeedback = useCallback((msgId: string, value: 'like' | 'dislike' | 'default') => {
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, feedback: value } : m));
  }, [setMessages]);

  const currentSession = sessions.find(s => s.id === activeKey);

  const conversationItems = useMemo(() =>
    sessions.map(s => ({
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
        deleteSession(conversation.key);
      } else if (key === 'rename') {
        const newTitle = prompt('请输入新名称:');
        if (newTitle?.trim()) {
          renameSession(conversation.key, newTitle.trim());
        }
      }
    },
  }), [deleteSession, renameSession]);

  const roleConfig = useMemo(() => ({
    user: {
      placement: 'end' as const,
      avatar: <UserOutlined />,
      variant: 'filled' as const,
    },
    ai: {
      placement: 'start' as const,
      avatar: <RobotOutlined />,
      variant: 'borderless' as const,
    },
    system: {
      placement: 'start' as const,
      variant: 'borderless' as const,
    },
  }), [mode]);

  const bubbleItems = useMemo(() =>
    messages.map((msg: ChatBubbleMessage) => {
      const base = {
        key: msg.id,
        role: msg.role === 'assistant' ? 'ai' : msg.role,
        content: msg.content,
        loading: msg.status === 'loading' && !msg.content,
        streaming: msg.streaming,
      };

      if (msg.role === 'assistant') {
        const hasTimeline = msg.timeline && msg.timeline.length > 0;
        const isComplete = msg.status === 'success' && !msg.streaming;

        const contentRender = hasTimeline
          ? () => <TimelineView events={msg.timeline!} />
          : msg.content
            ? (content: string) => <XMarkdown>{content}</XMarkdown>
            : undefined;

        const footerContent = isComplete ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Actions.Copy text={msg.content || ' '} />
            <Actions
              items={[
                {
                  key: 'feedback',
                  actionRender: () => (
                    <Actions.Feedback
                      value={msg.feedback || 'default'}
                      onChange={(val) => handleFeedback(msg.id, val)}
                    />
                  ),
                },
              ]}
              variant="borderless"
              fadeIn
            />
          </div>
        ) : undefined;

        return {
          ...base,
          contentRender,
          footer: footerContent,
        };
      }

      if (msg.role === 'system') {
        return {
          ...base,
          content: <Alert message={msg.content} type="warning" showIcon banner />,
        };
      }

      return base;
    }),
    [messages, sendMessage],
  );

  const showWelcome = messages.length === 0 && !loadingHistory;

  const sidebarWidth = 250;
  const sidebarContent = (
    <div style={{
      width: sidebarWidth,
      minWidth: sidebarWidth,
      height: '100%',
      borderLeft: `1px solid var(--silk-line)`,
      background: 'var(--paper-base)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 12px 8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--silk-line)',
        flexShrink: 0,
      }}>
        <span
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--ink-heavy)',
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.06em',
          }}
        >
          会话
        </span>
        <a
          data-tour-chat-new-session
          onClick={handleCreateSession}
          style={{ fontSize: 14, color: 'var(--ink-light)', cursor: 'pointer' }}
          title="新建会话"
        >
          <PlusOutlined />
        </a>
      </div>
      <div data-tour-chat-sessions style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        <Conversations
          items={conversationItems}
          activeKey={activeKey || undefined}
          onActiveChange={(key) => {
            setActiveKey(key);
          }}
          menu={conversationMenu}
        />
      </div>
    </div>
  );

  return (
    <XProvider>
      <div style={{
        display: 'flex',
        flex: 1,
        height: '100%',
        minHeight: 0,
        overflow: 'hidden',
        background: 'var(--paper-elevated)',
      }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{
            padding: '10px 16px',
            borderBottom: `1px solid var(--silk-line)`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            flexShrink: 0,
          }}>
            <div
              className="seal-stamp"
              style={{
                width: 28,
                height: 28,
                fontSize: 14,
              }}
              aria-hidden="true"
            >
              印
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: 'var(--ink-heavy)',
                  fontFamily: 'var(--font-display)',
                  letterSpacing: '0.04em',
                  lineHeight: 1.3,
                }}
              >
                润笔
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--ink-light)',
                  fontFamily: 'var(--font-display)',
                  letterSpacing: '0.05em',
                  lineHeight: 1.3,
                }}
              >
                {currentSession?.title || currentProject?.name || '新会话'}
              </div>
            </div>
            <a
              data-tour-drawer-new-session={mode === 'drawer' ? '' : undefined}
              data-tour-chat-new-session
              onClick={handleCreateSession}
              style={{
                fontSize: 14, color: 'var(--ink-light)', cursor: 'pointer',
                padding: '4px 6px', borderRadius: 'var(--radius-sm)',
                transition: 'all 0.15s',
              }}
              title="新建会话"
            >
              <PlusOutlined />
            </a>
            <a
              onClick={toggleSidebar}
              style={{
                fontSize: 16, color: 'var(--ink-light)', cursor: 'pointer',
                padding: '4px 6px', borderRadius: 'var(--radius-sm)',
                transition: 'all 0.15s',
              }}
              title={sidebarOpen ? '隐藏会话列表' : '显示会话列表'}
            >
              <MenuOutlined />
            </a>
          </div>

          <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: mode === 'drawer' ? 12 : 24 }}>
            {loadingHistory ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: 40,
                  color: 'var(--ink-light)',
                  fontFamily: 'var(--font-display)',
                  letterSpacing: '0.06em',
                }}
              >
                展卷中…
              </div>
            ) : showWelcome ? (
              <WelcomeScreen onSend={sendMessage} />
            ) : (
              <Bubble.List
                items={bubbleItems}
                role={roleConfig}
                autoScroll
                style={{ height: '100%' }}
              />
            )}
          </div>

          <div data-tour-chat-input style={{
            padding: mode === 'drawer' ? '8px 12px' : '12px 24px',
            borderTop: `1px solid var(--silk-line)`,
            background: 'var(--paper-elevated)',
          }}>
            <div data-tour-chat-send>
            <Sender
              value={inputValue}
              onChange={(val) => setInputValue(val)}
              loading={isRequesting}
              onCancel={cancel}
              onSubmit={(msg) => sendMessage(msg)}
              placeholder={activeKey ? '请落墨…（Enter 发送）' : '请先开启或择一会话'}
              disabled={!activeKey}
              autoSize={mode === 'drawer' ? { maxRows: 4 } : { maxRows: 8 }}
            />
            </div>
          </div>
        </div>

        {mode === 'page' && (
          <div style={{
            width: sidebarOpen ? 250 : 0,
            height: '100%',
            overflow: 'hidden',
            transition: 'width 0.25s ease',
            flexShrink: 0,
          }}>
            {sidebarContent}
          </div>
        )}

      </div>
    </XProvider>
  );
};

const ChatCore = ({ mode, sidebarOpen, onSidebarToggle }: ChatCoreProps) => {
  const chat = useChatContext();
  if (!chat) return null;
  return <ChatCoreInner mode={mode} chat={chat} sidebarOpen={sidebarOpen} onSidebarToggle={onSidebarToggle} />;
};

export default ChatCore;
