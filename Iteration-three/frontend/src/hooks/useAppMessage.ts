import { App } from 'antd';

export function useAppMessage() {
  const { message, notification } = App.useApp();
  return { message, notification };
}

export function useAppModal() {
  const { modal } = App.useApp();
  return modal;
}
