import { Button } from 'antd';

interface EmptyStateProps {
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

const ScrollIcon = () => (
  <svg
    width="80"
    height="80"
    viewBox="0 0 80 80"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <g
      stroke="var(--ink-light)"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    >
      <rect x="14" y="20" width="52" height="40" rx="2" fill="var(--paper-elevated)" />
      <path d="M14 20 L8 18 L8 62 L14 60" />
      <path d="M66 20 L72 18 L72 62 L66 60" />
      <line x1="22" y1="32" x2="58" y2="32" />
      <line x1="22" y1="40" x2="48" y2="40" />
      <line x1="22" y1="48" x2="54" y2="48" />
    </g>
    <circle cx="40" cy="14" r="3" fill="var(--vermilion)" opacity="0.85" />
  </svg>
);

const EmptyState = ({ description = '尚无内容', actionText, onAction }: EmptyStateProps) => {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '60px 0',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
      }}
    >
      <ScrollIcon />
      <div
        style={{
          color: 'var(--ink-medium)',
          fontFamily: 'var(--font-display)',
          fontSize: 14,
          letterSpacing: '0.06em',
        }}
      >
        {description}
      </div>
      {actionText && onAction && (
        <Button type="primary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
