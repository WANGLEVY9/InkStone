import { useState, useCallback, useRef, useEffect } from 'react';
import { sessionsApi } from '@/api/sessions';
import { useAppMessage } from '@/hooks/useAppMessage';
import type { Session, ChatMessage, ChatBubbleMessage, ChatTimelineEvent } from '@/types';

const DELEGATE_TOOLS = new Set([
  'delegate_to_world_builder',
  'delegate_to_character',
  'delegate_to_plot',
  'delegate_to_chapter',
  'delegate_to_review',
]);

const READ_ONLY_TOOLS = new Set([
  'list_world_settings',
  'list_characters',
  'get_story_outline',
  'list_chapters',
  'load_skill',
  'query_content',
  'get_content',
  'get_outline_tree',
]);

let messageIdCounter = 0;
const genId = () => `msg-${++messageIdCounter}-${Date.now()}`;

export function useProjectChat(projectId: string) {
  const { message: messageApi } = useAppMessage();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatBubbleMessage[]>([]);
  const [isRequesting, setIsRequesting] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<ChatBubbleMessage[]>([]);

  messagesRef.current = messages;

  // Load sessions on mount
  useEffect(() => {
    if (!projectId) return;
    sessionsApi.list(projectId).then(res => {
      setSessions(res.data);
      if (res.data.length > 0 && !activeKey) {
        setActiveKey(res.data[0].id);
      }
    }).catch(() => {
      messageApi.error('加载会话列表失败');
    });
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load history when activeKey changes
  useEffect(() => {
    if (!activeKey || !projectId) return;
    setLoadingHistory(true);
    sessionsApi.getHistory(projectId, activeKey).then(res => {
      const history: ChatMessage[] = res.data;

      // Pre-pass: collect tool results for matching by tool_call_id
      const toolResults: Record<string, string> = {};
      for (const m of history) {
        if (m.role === 'tool' && m.tool_call_id) {
          toolResults[m.tool_call_id] = m.content;
        }
      }

      const converted: ChatBubbleMessage[] = [];
      // Accumulator for merging consecutive assistant messages into one bubble
      let pendingTimeline: ChatTimelineEvent[] = [];
      let pendingContent = '';

      const flushAssistant = () => {
        if (pendingTimeline.length > 0 || pendingContent) {
          converted.push({
            id: genId(),
            role: 'assistant',
            content: pendingContent,
            status: 'success',
            timeline: pendingTimeline.length > 0 ? pendingTimeline : undefined,
          });
          pendingTimeline = [];
          pendingContent = '';
        }
      };

      for (const msg of history) {
        if (msg.role === 'user') {
          // Flush accumulated assistant messages before the user message
          flushAssistant();
          converted.push({
            id: genId(),
            role: 'user',
            content: msg.content,
            status: 'success',
          });
          continue;
        }

        if (msg.role === 'tool') {
          // Skip tool result messages — they're attached to tool_call events
          continue;
        }

        if (msg.role === 'assistant') {
          // Thinking
          if (msg.thinking_content) {
            pendingTimeline.push({ type: 'thinking', content: msg.thinking_content });
          }

          // Text content
          if (msg.content) {
            pendingTimeline.push({ type: 'text', content: msg.content });
            pendingContent = msg.content;
          }

          // Tool calls
          if (msg.tool_calls && msg.tool_calls.length) {
            for (const tc of msg.tool_calls) {
              const isDelegate = DELEGATE_TOOLS.has(tc.name);
              const isReadOnly = READ_ONLY_TOOLS.has(tc.name);
              const result = toolResults[tc.id] ?? null;

              const toolEvent: ChatTimelineEvent = {
                type: 'tool',
                name: tc.name,
                toolCallId: tc.id,
                status: 'completed',
                isDelegate,
                isReadOnly,
                result,
                subTimeline: isDelegate && result ? [{ type: 'text', content: result }] : undefined,
              };
              pendingTimeline.push(toolEvent);
            }
          }
          continue;
        }

        // system
        flushAssistant();
        converted.push({
          id: genId(),
          role: 'system',
          content: msg.content,
          status: 'success',
        });
      }
      // Flush any remaining assistant messages at the end
      flushAssistant();

      setMessages(converted);
      messagesRef.current = converted;
    }).catch(() => {
      messageApi.error('加载会话历史失败');
    }).finally(() => {
      setLoadingHistory(false);
    });
  }, [activeKey, projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  const createSession = useCallback(async () => {
    try {
      const res = await sessionsApi.create(projectId);
      setSessions(prev => [res.data, ...prev]);
      setActiveKey(res.data.id);
      setMessages([]);
      messagesRef.current = [];
      return res.data;
    } catch {
      messageApi.error('创建会话失败');
      return null;
    }
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await sessionsApi.delete(projectId, sessionId);
      setSessions(prev => {
        const remaining = prev.filter(s => s.id !== sessionId);
        if (activeKey === sessionId) {
          setActiveKey(remaining.length > 0 ? remaining[0].id : null);
          setMessages([]);
          messagesRef.current = [];
        }
        return remaining;
      });
    } catch {
      messageApi.error('删除会话失败');
    }
  }, [projectId, activeKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const renameSession = useCallback((sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
  }, []);

  // Recursively set all running timeline items to completed
  const finalizeRunningItems = (msg: ChatBubbleMessage) => {
    const finalizeTimeline = (events: ChatTimelineEvent[]) => {
      for (const ev of events) {
        if (ev.type === 'tool' && ev.status === 'running') {
          ev.status = 'completed';
        }
        if (ev.subTimeline) {
          finalizeTimeline(ev.subTimeline);
        }
      }
    };
    if (msg.timeline) finalizeTimeline(msg.timeline);
  };

  const sendMessage = useCallback(async (content: string) => {
    if (!activeKey || !content.trim() || isRequesting) return;

    setIsRequesting(true);
    const controller = new AbortController();
    abortRef.current = controller;

    const userMsg: ChatBubbleMessage = {
      id: genId(),
      role: 'user',
      content: content.trim(),
      status: 'success',
    };
    const agentMsg: ChatBubbleMessage = {
      id: genId(),
      role: 'assistant',
      content: '',
      agent: '',
      streaming: true,
      timeline: [],
      status: 'loading',
    };

    const newMessages = [...messagesRef.current, userMsg, agentMsg];
    messagesRef.current = newMessages;
    setMessages(newMessages);

    try {
      const response = await fetch(
        `/api/v1/projects/${projectId}/sessions/${activeKey}/chat/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: content.trim() }),
          signal: controller.signal,
        },
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error('Streaming not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEventType = '';

      const getCurrentAgentMsg = (): ChatBubbleMessage => {
        const msgs = messagesRef.current;
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant' && last.streaming) return last;
        const newMsg: ChatBubbleMessage = {
          id: genId(),
          role: 'assistant',
          content: '',
          agent: '',
          streaming: true,
          timeline: [],
          status: 'updating',
        };
        msgs.push(newMsg);
        return newMsg;
      };

      const processEvent = (eventType: string, data: Record<string, unknown>) => {
        const agentMsg = getCurrentAgentMsg();
        if (!agentMsg.timeline) agentMsg.timeline = [];
        const tl = agentMsg.timeline;

        // Find last running delegate's subTimeline
        const findLastDelegate = (): ChatTimelineEvent | null => {
          for (let i = tl.length - 1; i >= 0; i--) {
            if (tl[i].type === 'tool' && tl[i].isDelegate && tl[i].status === 'running') {
              return tl[i];
            }
          }
          return null;
        };

        switch (eventType) {
          case 'messages': {
            const source = data.source as string | undefined;
            const isSubAgent = source && source !== 'orchestrator';
            let targetTimeline = tl;

            // Route sub-agent events to delegate's subTimeline
            if (isSubAgent) {
              const delegateToolName = 'delegate_to_' + source;
              for (let i = tl.length - 1; i >= 0; i--) {
                const ev = tl[i];
                if (ev.type === 'tool' && ev.isDelegate && ev.name === delegateToolName && ev.status === 'running') {
                  if (!ev.subTimeline) ev.subTimeline = [];
                  targetTimeline = ev.subTimeline;
                  break;
                }
              }
            }

            if (!isSubAgent && source === 'orchestrator') {
              agentMsg.agent = 'Orchestrator';
            }

            // Thinking — merge with last thinking or create new
            if (data.thinking) {
              const last = targetTimeline[targetTimeline.length - 1];
              if (last && last.type === 'thinking') {
                last.content = (last.content || '') + (data.thinking as string);
              } else {
                targetTimeline.push({ type: 'thinking', content: data.thinking as string });
              }
              break;
            }

            // Text token — merge with last text or create new
            if (data.token) {
              const last = targetTimeline[targetTimeline.length - 1];
              if (last && last.type === 'text') {
                last.content = (last.content || '') + (data.token as string);
              } else {
                targetTimeline.push({ type: 'text', content: data.token as string });
              }
            }
            break;
          }

          case 'updates': {
            const lastDelegate = findLastDelegate();

            if (data.type === 'tool_start') {
              const toolName = data.tool as string;
              if (!toolName) break;
              const isDelegate = DELEGATE_TOOLS.has(toolName);
              const isReadOnly = READ_ONLY_TOOLS.has(toolName);
              const toolEvent: ChatTimelineEvent = {
                type: 'tool',
                name: toolName,
                toolCallId: data.tool_call_id as string | undefined,
                status: 'running',
                isDelegate,
                isReadOnly,
                result: null,
                subTimeline: isDelegate ? [] : undefined,
              };
              if (lastDelegate?.subTimeline) {
                lastDelegate.subTimeline.push(toolEvent);
              } else {
                tl.push(toolEvent);
              }
            } else if (data.type === 'tool_end') {
              const toolName = data.tool as string;
              if (!toolName) break;
              let found = false;
              // Search in delegate's subTimeline first
              if (lastDelegate?.subTimeline) {
                for (let j = lastDelegate.subTimeline.length - 1; j >= 0; j--) {
                  const se = lastDelegate.subTimeline[j];
                  if (se.type === 'tool' && se.name === toolName && se.status === 'running') {
                    se.status = 'completed';
                    se.result = data.result ?? null;
                    found = true;
                    break;
                  }
                }
              }
              // Fallback: search main timeline
              if (!found) {
                for (let i = tl.length - 1; i >= 0; i--) {
                  const ev = tl[i];
                  if (ev.type === 'tool' && ev.name === toolName && ev.status === 'running') {
                    ev.status = 'completed';
                    ev.result = data.result ?? null;
                    break;
                  }
                }
              }
            }
            break;
          }

          case 'error': {
            tl.push({ type: 'error', content: data.message as string });
            break;
          }
        }

        agentMsg.status = 'updating';
        setMessages([...messagesRef.current]);
      };

      // Read SSE stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim();
          }
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const parsed = JSON.parse(raw);
              processEvent(currentEventType, parsed);
            } catch { /* ignore malformed JSON */ }
          }
        }
      }

      // Finalize
      const last = messagesRef.current[messagesRef.current.length - 1];
      if (last?.role === 'assistant') {
        last.streaming = false;
        last.status = 'success';
        finalizeRunningItems(last);
        setMessages([...messagesRef.current]);
      }
    } catch (e) {
      if ((e as Error).name === 'AbortError') {
        const last = messagesRef.current[messagesRef.current.length - 1];
        if (last?.role === 'assistant') {
          last.streaming = false;
          last.status = 'success';
          finalizeRunningItems(last);
          setMessages([...messagesRef.current]);
        }
      } else {
        const errorMsg: ChatBubbleMessage = {
          id: genId(),
          role: 'system',
          content: `Error: ${(e as Error).message}`,
          status: 'error',
        };
        messagesRef.current.push(errorMsg);
        setMessages([...messagesRef.current]);
      }
    }

    abortRef.current = null;
    setIsRequesting(false);
  }, [activeKey, projectId, isRequesting]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    messagesRef.current = [];
    setMessages([]);
    setIsRequesting(false);
  }, []);

  return {
    sessions,
    activeKey,
    setActiveKey,
    messages,
    setMessages,
    isRequesting,
    loadingHistory,
    sendMessage,
    cancel,
    clearMessages,
    createSession,
    deleteSession,
    renameSession,
  };
}
