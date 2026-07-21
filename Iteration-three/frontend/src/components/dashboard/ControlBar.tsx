import { Input, Button, Dropdown, Popconfirm } from 'antd';
import {
  SearchOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PushpinOutlined,
} from '@ant-design/icons';

export type SortOption = 'updated_at' | 'created_at' | 'name' | 'word_count';
export type FilterOption = 'all' | 'active' | 'archived';
export type ViewMode = 'bookshelf' | 'list';

interface ControlBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  sort: SortOption;
  onSortChange: (value: SortOption) => void;
  filter: FilterOption;
  onFilterChange: (value: FilterOption) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onCreate: () => void;
  managementMode: boolean;
  selectedCount: number;
  totalCount: number;
  onManageToggle: () => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onBatchDelete: () => void;
  onBatchPin: (isPinned: boolean) => void;
}

const SORT_LABELS: Record<SortOption, string> = {
  updated_at: '最近更新',
  created_at: '最早创建',
  name: '名称',
  word_count: '字数最多',
};

const FILTER_LABELS: Record<FilterOption, string> = {
  all: '全部',
  active: '活跃',
  archived: '已归档',
};

const ControlBar = ({
  search,
  onSearchChange,
  sort,
  onSortChange,
  filter,
  onFilterChange,
  viewMode,
  onViewModeChange,
  onCreate,
  managementMode,
  selectedCount,
  totalCount,
  onManageToggle,
  onSelectAll,
  onClearSelection,
  onBatchDelete,
  onBatchPin,
}: ControlBarProps) => {
  const sortItems = Object.entries(SORT_LABELS).map(([key, label]) => ({
    key,
    label,
    onClick: () => onSortChange(key as SortOption),
  }));

  const filterItems = Object.entries(FILTER_LABELS).map(([key, label]) => ({
    key,
    label,
    onClick: () => onFilterChange(key as FilterOption),
  }));

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14 }}>
      <Input
        data-tour-dashboard-search
        prefix={<SearchOutlined />}
        placeholder="搜索项目..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        style={{ flex: 1 }}
        allowClear
      />
      <Dropdown menu={{ items: sortItems, selectedKeys: [sort] }}>
        <Button>{SORT_LABELS[sort]} ▾</Button>
      </Dropdown>
      <Dropdown menu={{ items: filterItems, selectedKeys: [filter] }}>
        <Button>{FILTER_LABELS[filter]} ▾</Button>
      </Dropdown>
      <Button.Group>
        <Button
          type={viewMode === 'bookshelf' ? 'primary' : 'default'}
          icon={<AppstoreOutlined />}
          onClick={() => onViewModeChange('bookshelf')}
        />
        <Button
          type={viewMode === 'list' ? 'primary' : 'default'}
          icon={<UnorderedListOutlined />}
          onClick={() => onViewModeChange('list')}
        />
      </Button.Group>
      {managementMode ? (
        <>
          <span style={{ fontSize: 12, color: 'var(--ink-light)', whiteSpace: 'nowrap' }}>
            已选 {selectedCount} / {totalCount}
          </span>
          <Button onClick={onSelectAll} disabled={totalCount === 0 || selectedCount === totalCount}>
            全选
          </Button>
          <Button onClick={onClearSelection} disabled={selectedCount === 0}>
            清空
          </Button>
          <Button icon={<PushpinOutlined />} onClick={() => onBatchPin(true)} disabled={selectedCount === 0}>
            标注
          </Button>
          <Button onClick={() => onBatchPin(false)} disabled={selectedCount === 0}>
            取消标注
          </Button>
          <Popconfirm
            title="删除选中的卷宗？"
            description="删除后不可恢复，请确认是否继续。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={onBatchDelete}
            disabled={selectedCount === 0}
          >
            <Button danger icon={<DeleteOutlined />} disabled={selectedCount === 0}>
              删除
            </Button>
          </Popconfirm>
          <Button onClick={onManageToggle}>退出管理</Button>
        </>
      ) : (
        <>
          <Button data-tour-dashboard-manage icon={<EditOutlined />} onClick={onManageToggle}>
            管理卷宗
          </Button>
          <Button data-tour-dashboard-create type="primary" icon={<PlusOutlined />} onClick={onCreate}>
            新立卷宗
          </Button>
        </>
      )}
    </div>
  );
};

export default ControlBar;
