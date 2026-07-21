import { Buffer } from 'buffer';
globalThis.Buffer = Buffer;

import React from 'react';
import ReactDOM from 'react-dom/client';
import 'antd/dist/reset.css';
import './styles/theme.css';
import { ensureTourStorageReset } from '@/components/onboarding/tourConfig';
import { scheduleRoutePrefetch } from '@/utils/prefetchRoutes';
import App from './App';

ensureTourStorageReset();
scheduleRoutePrefetch();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
