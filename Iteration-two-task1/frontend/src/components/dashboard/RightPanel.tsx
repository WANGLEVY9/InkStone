import type { Project } from '@/types';
import ControlBar from './ControlBar';
import type { SortOption, FilterOption, ViewMode } from './ControlBar';
import BookshelfView from './BookshelfView';
import ListView from './ListView';

interface RightPanelProps {
  projects: Project[];
  search: string;
  onSearchChange: (value: string) => void;
  sort: SortOption;
  onSortChange: (value: SortOption) => void;
  filter: FilterOption;
  onFilterChange: (value: FilterOption) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onCreate: () => void;
  onTogglePin: (projectId: string) => void;
}

const RightPanel = ({
  projects,
  search,
  onSearchChange,
  sort,
  onSortChange,
  filter,
  onFilterChange,
  viewMode,
  onViewModeChange,
  onCreate,
  onTogglePin,
}: RightPanelProps) => {
  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
      <ControlBar
        search={search}
        onSearchChange={onSearchChange}
        sort={sort}
        onSortChange={onSortChange}
        filter={filter}
        onFilterChange={onFilterChange}
        viewMode={viewMode}
        onViewModeChange={onViewModeChange}
        onCreate={onCreate}
      />
      {viewMode === 'bookshelf' ? (
        <BookshelfView projects={projects} onTogglePin={onTogglePin} onCreate={onCreate} />
      ) : (
        <ListView projects={projects} onTogglePin={onTogglePin} />
      )}
    </div>
  );
};

export default RightPanel;
