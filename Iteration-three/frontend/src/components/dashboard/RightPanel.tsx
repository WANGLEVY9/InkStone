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
  managementMode: boolean;
  selectedProjectIds: Set<string>;
  onManageToggle: () => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onToggleSelectProject: (projectId: string) => void;
  onBatchDelete: () => void;
  onBatchPin: (isPinned: boolean) => void;
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
  managementMode,
  selectedProjectIds,
  onManageToggle,
  onSelectAll,
  onClearSelection,
  onToggleSelectProject,
  onBatchDelete,
  onBatchPin,
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
        managementMode={managementMode}
        selectedCount={selectedProjectIds.size}
        totalCount={projects.length}
        onManageToggle={onManageToggle}
        onSelectAll={onSelectAll}
        onClearSelection={onClearSelection}
        onBatchDelete={onBatchDelete}
        onBatchPin={onBatchPin}
      />
      {viewMode === 'bookshelf' ? (
        <div data-tour-dashboard-content style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <BookshelfView
          projects={projects}
          onTogglePin={onTogglePin}
          onCreate={onCreate}
          managementMode={managementMode}
          selectedProjectIds={selectedProjectIds}
          onToggleSelectProject={onToggleSelectProject}
        />
        </div>
      ) : (
        <div data-tour-dashboard-content style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <ListView
          projects={projects}
          onTogglePin={onTogglePin}
          managementMode={managementMode}
          selectedProjectIds={selectedProjectIds}
          onToggleSelectProject={onToggleSelectProject}
        />
        </div>
      )}
    </div>
  );
};

export default RightPanel;
