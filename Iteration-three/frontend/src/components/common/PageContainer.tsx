import type { ReactNode } from 'react';

const PageContainer = ({ children }: { children: ReactNode }) => (
  <div style={{ maxWidth: 1200, width: '100%', margin: '0 auto' }}>{children}</div>
);

export default PageContainer;
