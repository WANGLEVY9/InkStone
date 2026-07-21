type ChatDrawerOpener = () => void | Promise<void>;

let chatDrawerOpener: ChatDrawerOpener | null = null;

export const registerChatDrawerOpener = (opener: ChatDrawerOpener) => {
  chatDrawerOpener = opener;
  return () => {
    if (chatDrawerOpener === opener) {
      chatDrawerOpener = null;
    }
  };
};

export const requestChatDrawerOpen = async () => {
  if (!chatDrawerOpener) return;
  await chatDrawerOpener();
};
