import { Input, Button, Dropdown } from 'antd';
import {
  SearchOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  PlusOutlined,
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
      <Button type="primary" icon={<PlusOutlined />} onClick={onCreate} />
    </div>
  );
};

export default ControlBar;
