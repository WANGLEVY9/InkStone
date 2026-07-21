import { createContext, useContext, type ReactNode } from 'react';
import { useProjectChat } from '@/hooks/useProjectChat';
import { useProjectContext } from '@/contexts/ProjectContext';

type ChatState = ReturnType<typeof useProjectChat>;

const ChatContext = createContext<ChatState | null>(null);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const { currentProject } = useProjectContext();
  const chatState = useProjectChat(currentProject?.id || '');

  // Only provide state when project is loaded
  if (!currentProject) {
    return <>{children}</>;
  }

  return (
    <ChatContext.Provider value={chatState}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChatContext = (): ChatState | null => {
  return useContext(ChatContext);
};
