import { useState } from 'react';
import { Checkbox } from 'antd';
import type { Project } from '@/types';

interface BookCoverProps {
  project: Project;
  onClick: () => void;
  onTogglePin?: (e: React.MouseEvent) => void;
  managementMode?: boolean;
  selected?: boolean;
}

// 6 套锦缎配色：base = 主底色，deep = 渐变深色端，accent = 菱形织金/红纹色
const SILK_PATTERNS: ReadonlyArray<{ base: string; deep: string; accent: string }> = [
  { base: '#D4B96E', deep: '#B89A4E', accent: 'rgba(169, 54, 68, 0.22)' },  // 金红（参考样式）
  { base: '#5A6D7A', deep: '#3F4F5C', accent: 'rgba(245, 239, 227, 0.10)' }, // 青灰
  { base: '#7A5C46', deep: '#5C3F2E', accent: 'rgba(212, 185, 110, 0.16)' }, // 黄褐
  { base: '#5C4A6E', deep: '#3F2D52', accent: 'rgba(212, 185, 110, 0.10)' }, // 紫绛
  { base: '#4A6657', deep: '#2A4537', accent: 'rgba(212, 185, 110, 0.10)' }, // 墨绿
  { base: '#8A4A3D', deep: '#5C2E22', accent: 'rgba(212, 185, 110, 0.13)' }, // 朱栗
];

const hashStr = (s: string): number => {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
};

const formatWordCount = (n: number): string => {
  if (n === 0) return '尚未落墨';
  if (n < 10000) return `${n.toLocaleString()} 字`;
  return `${(n / 10000).toFixed(2)} 万字`;
};

const formatRelativeTime = (iso: string): string => {
  const diff = Date.now() - new Date(iso).getTime();
  const day = 86_400_000;
  if (diff < day) return '今日';
  if (diff < 30 * day) return `${Math.floor(diff / day)} 天前`;
  if (diff < 365 * day) return `${Math.floor(diff / (30 * day))} 月前`;
  return `${Math.floor(diff / (365 * day))} 年前`;
};

const getStatusSeal = (status: string, wordCount: number): string => {
  if (wordCount === 0) return '启';
  if (status === 'archived') return '终';
  return '续';
};

const SILK_AREA_HEIGHT = 224;
const FOOTER_HEIGHT = 36;
const SLIP_LEFT = 14;
const SLIP_TOP = 14;
const SLIP_WIDTH = 44;
const SLIP_HEIGHT = 200;
const TITLE_AREA_HEIGHT = SLIP_HEIGHT - 44; // padding 12 + 8 + seal 18 + seal-margin 6
const MIN_TITLE_FONT = 12;
const MAX_TITLE_FONT = 22;
const TITLE_FIT_FACTOR = 1.22; // line-height 1.05 + letter-spacing 0.16em + 0.01 缓冲

const fitTitle = (title: string): { display: string; size: number } => {
  const chars = [...title];
  const ideal = TITLE_AREA_HEIGHT / (chars.length * TITLE_FIT_FACTOR);
  if (ideal >= MIN_TITLE_FONT) {
    return { display: title, size: Math.min(MAX_TITLE_FONT, Math.floor(ideal)) };
  }
  const maxChars = Math.floor(TITLE_AREA_HEIGHT / (MIN_TITLE_FONT * TITLE_FIT_FACTOR));
  return {
    display: chars.slice(0, Math.max(1, maxChars - 1)).join('') + '⋯',
    size: MIN_TITLE_FONT,
  };
};

const BookCover = ({ project, onClick, onTogglePin, managementMode = false, selected = false }: BookCoverProps) => {
  const [hovered, setHovered] = useState(false);
  const seal = getStatusSeal(project.status, project.word_count);
  const silk = SILK_PATTERNS[hashStr(project.id) % SILK_PATTERNS.length];

  // 标题动态缩小以适应封签竖排空间，溢出时尾部截断
  const { display: displayTitle, size: titleFontSize } = fitTitle(project.name);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: 200,
        height: 260,
        position: 'relative',
        cursor: 'pointer',
        borderRadius: 'var(--radius-md)',
        boxShadow: hovered
          ? '0 8px 22px rgba(31, 26, 23, 0.20), 0 2px 6px rgba(31, 26, 23, 0.10)'
          : 'var(--shadow-sm)',
        transform: hovered ? 'translateY(-4px)' : 'translateY(0)',
        transition: 'transform 0.25s ease, box-shadow 0.25s ease',
        overflow: 'hidden',
        background: 'var(--paper-elevated)',
        outline: selected ? '3px solid var(--vermilion)' : 'none',
        outlineOffset: 2,
      }}
    >
      {managementMode && (
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: 10,
            zIndex: 5,
            width: 26,
            height: 26,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(251, 246, 234, 0.92)',
            border: '1px solid var(--silk-line-strong)',
            borderRadius: '50%',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <Checkbox checked={selected} />
        </div>
      )}

      {/* 锦缎区域 */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: SILK_AREA_HEIGHT,
          background: `
            repeating-linear-gradient(45deg, transparent 0 22px, ${silk.accent} 22px 24px),
            repeating-linear-gradient(-45deg, transparent 0 22px, ${silk.accent} 22px 24px),
            radial-gradient(ellipse at 30% 20%, ${silk.base} 0%, ${silk.deep} 90%)
          `,
        }}
      >
        {/* 中央菱形装饰，加强锦缎感 */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `
              radial-gradient(circle 4px at 50% 50%, ${silk.accent} 0%, transparent 60%)
            `,
            backgroundSize: '34px 34px',
            backgroundPosition: '17px 17px',
            opacity: 0.7,
          }}
        />
        {/* 暗角晕染 */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(ellipse at 60% 70%, transparent 40%, rgba(0, 0, 0, 0.20) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* 封签（白纸题签） */}
      <div
        style={{
          position: 'absolute',
          left: SLIP_LEFT,
          top: SLIP_TOP,
          width: SLIP_WIDTH,
          height: SLIP_HEIGHT,
          background: 'linear-gradient(180deg, #FBF6EA 0%, #F5EFE0 100%)',
          boxShadow:
            '0 2px 4px rgba(0, 0, 0, 0.22), 0 0 0 1px rgba(74, 63, 51, 0.10)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '12px 4px 8px',
        }}
      >
        {/* 封签标题（竖排） */}
        <div
          style={{
            writingMode: 'vertical-rl',
            textOrientation: 'upright',
            fontFamily: 'var(--font-brush)',
            fontSize: titleFontSize,
            fontWeight: 400,
            color: 'var(--ink-heavy)',
            letterSpacing: '0.16em',
            lineHeight: 1.05,
            flex: 1,
            overflow: 'hidden',
            textAlign: 'center',
          }}
          title={project.name}
        >
          {displayTitle}
        </div>

        {/* 封签底部状态印 */}
        <div
          className="seal-stamp"
          style={{
            width: 18,
            height: 18,
            fontSize: 10,
            marginTop: 6,
          }}
          title={seal === '启' ? '新立' : seal === '终' ? '已封' : '续作'}
        >
          {seal}
        </div>
      </div>

      {/* 置顶印（右上角，覆盖在锦缎上） */}
      {project.is_pinned && !managementMode && (
        <div
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin?.(e);
          }}
          className="seal-stamp"
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            width: 22,
            height: 22,
            fontSize: 12,
            zIndex: 3,
          }}
          title="已收藏 · 点击取消"
        >
          藏
        </div>
      )}

      {/* 页脚白纸条（字数 + 时间） */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: FOOTER_HEIGHT,
          background: 'var(--paper-elevated)',
          borderTop: '1px solid var(--silk-line)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 14px',
          fontFamily: 'var(--font-display)',
          fontSize: 11,
          color: 'var(--ink-light)',
          letterSpacing: '0.06em',
        }}
      >
        <span style={{ color: 'var(--ink-medium)' }}>{formatWordCount(project.word_count)}</span>
        <span>{formatRelativeTime(project.updated_at)}</span>
      </div>
    </div>
  );
};

export default BookCover;
