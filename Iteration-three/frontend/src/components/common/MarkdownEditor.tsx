import { useRef } from 'react';
import { useVditor, type VditorMode } from '@/hooks/useVditor';
import '@/styles/vditor-override.css';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number | 'auto';
  placeholder?: string;
  mode?: VditorMode;
}

const MarkdownEditor = ({ value, onChange, height = 'auto', placeholder, mode }: MarkdownEditorProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useVditor({ containerRef, value, onChange, height, placeholder, mode });

  return <div ref={containerRef} className="vditor-wrapper" />;
};

export default MarkdownEditor;
