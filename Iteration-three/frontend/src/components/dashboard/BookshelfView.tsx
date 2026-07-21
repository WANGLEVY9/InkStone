import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Project } from '@/types';
import BookCover from './BookCover';

interface BookshelfViewProps {
  projects: Project[];
  onTogglePin: (projectId: string) => void;
  onCreate: () => void;
  managementMode: boolean;
  selectedProjectIds: Set<string>;
  onToggleSelectProject: (projectId: string) => void;
}

const CARD_WIDTH = 200;
const CARD_HEIGHT = 260;

const AddBookButton = ({ onClick }: { onClick: () => void }) => {
  const [hovered, setHovered] = useState(false);
  const cornerColor = hovered ? 'var(--vermilion)' : 'var(--silk-line-strong)';

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: CARD_WIDTH,
        height: CARD_HEIGHT,
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        background: hovered ? 'rgba(200, 50, 61, 0.04)' : 'transparent',
        borderRadius: 'var(--radius-md)',
        transition: 'background 0.2s',
      }}
    >
      <span
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 14,
          height: 14,
          borderTop: `2px solid ${cornerColor}`,
          borderLeft: `2px solid ${cornerColor}`,
          transition: 'border-color 0.2s',
        }}
      />
      <span
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: 14,
          height: 14,
          borderTop: `2px solid ${cornerColor}`,
          borderRight: `2px solid ${cornerColor}`,
          transition: 'border-color 0.2s',
        }}
      />
      <span
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: 14,
          height: 14,
          borderBottom: `2px solid ${cornerColor}`,
          borderLeft: `2px solid ${cornerColor}`,
          transition: 'border-color 0.2s',
        }}
      />
      <span
        style={{
          position: 'absolute',
          bottom: 0,
          right: 0,
          width: 14,
          height: 14,
          borderBottom: `2px solid ${cornerColor}`,
          borderRight: `2px solid ${cornerColor}`,
          transition: 'border-color 0.2s',
        }}
      />

      <span
        style={{
          color: hovered ? 'var(--vermilion)' : 'var(--ink-faint)',
          fontSize: 30,
          lineHeight: 1,
          fontFamily: 'var(--font-display)',
          fontWeight: 300,
          transition: 'color 0.2s',
        }}
      >
        ＋
      </span>
      <span
        style={{
          color: hovered ? 'var(--vermilion)' : 'var(--ink-light)',
          fontSize: 12,
          marginTop: 8,
          fontFamily: 'var(--font-display)',
          letterSpacing: '0.12em',
          transition: 'color 0.2s',
        }}
      >
        新立卷宗
      </span>
    </div>
  );
};

const BookshelfView = ({
  projects,
  onTogglePin,
  onCreate,
  managementMode,
  selectedProjectIds,
  onToggleSelectProject,
}: BookshelfViewProps) => {
  const navigate = useNavigate();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, minHeight: 0 }}>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          padding: 20,
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--silk-line-strong)',
          boxShadow: 'var(--shadow-md)',
          background: 'var(--paper-elevated)',
          overflowY: 'auto',
          display: 'grid',
          gridTemplateColumns: `repeat(auto-fill, ${CARD_WIDTH}px)`,
          gridAutoRows: `${CARD_HEIGHT}px`,
          gap: 16,
          alignContent: 'start',
          justifyContent: 'start',
        }}
      >
        {projects.map((project) => (
          <BookCover
            key={project.id}
            project={project}
            onClick={() => {
              if (managementMode) {
                onToggleSelectProject(project.id);
                return;
              }
              navigate(`/projects/${project.id}/world`);
            }}
            onTogglePin={() => onTogglePin(project.id)}
            managementMode={managementMode}
            selected={selectedProjectIds.has(project.id)}
          />
        ))}
        {!managementMode && <AddBookButton onClick={onCreate} />}
      </div>
    </div>
  );
};

export default BookshelfView;
