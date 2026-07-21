export type GuidePlacement = 'right' | 'left' | 'bottom' | 'top' | 'center';

export type TourId =
  | 'dashboard'
  | 'project-shell'
  | 'world'
  | 'characters'
  | 'outline'
  | 'chapters'
  | 'chat'
  | 'system-settings'
  | 'project-settings';

export interface TourStep {
  id: string;
  selector: string;
  title: string;
  content: string;
  placement?: GuidePlacement;
  /** Used only for positioning highlight on a parent element (e.g. menu item). */
  interactiveClosest?: string;
  positionSelector?: string;
  forcePlacement?: boolean;
  offsetY?: number;
  /** 点击「确定」离开本步时先打开 AI 问询抽屉，再进入下一步 */
  openChatDrawerOnNext?: boolean;
  /** 与 openChatDrawerOnNext 配合：等待该选择器可见后再展示下一步引导 */
  waitForSelector?: string;
}

export interface TourConfig {
  id: TourId;
  storageKey: string;
  label: string;
  match: (pathname: string) => boolean;
  steps: TourStep[];
}

const projectRootPattern = /^\/projects\/[^/]+(?:\/(?:world|characters|outline|chapters|chat|settings)(?:\/.*)?)?$/;

/** 各页面新手教程 localStorage 持久化 key，触发后写入 true，不再自动弹出 */
export const TOUR_STORAGE_KEYS: Record<TourId, string> = {
  dashboard: 'inkstone-tour-dashboard-done',
  'project-shell': 'inkstone-tour-project-shell-done',
  world: 'inkstone-tour-world-done',
  characters: 'inkstone-tour-characters-done',
  outline: 'inkstone-tour-outline-done',
  chapters: 'inkstone-tour-chapters-done',
  chat: 'inkstone-tour-chat-done',
  'system-settings': 'inkstone-tour-system-settings-done',
  'project-settings': 'inkstone-tour-project-settings-done',
};

export const TOUR_CONFIGS: TourConfig[] = [
  {
    id: 'dashboard',
    storageKey: TOUR_STORAGE_KEYS.dashboard,
    label: '首页教程',
    match: (pathname) => pathname === '/',
    steps: [
      {
        id: 'dashboard-create',
        selector: '[data-tour-dashboard-create]',
        title: '新立卷宗',
        content: '此处用于创建新的作品卷宗，是开始创作的第一步。',
        placement: 'left',
      },
      {
        id: 'dashboard-manage',
        selector: '[data-tour-dashboard-manage]',
        title: '管理卷宗',
        content: '进入管理模式后，可批量选择卷宗，执行删除、标注或取消标注。',
        placement: 'bottom',
      },
      {
        id: 'dashboard-search',
        selector: '[data-tour-dashboard-search]',
        title: '查找卷宗',
        content: '搜索框用于筛选卷宗，也可配合排序与视图切换整理作品。',
        placement: 'bottom',
      },
      {
        id: 'dashboard-content',
        selector: '[data-tour-dashboard-content]',
        title: '卷宗书架',
        content: '这里展示全部作品；浏览完成后，可在书架中进入具体项目继续创作。',
        placement: 'top',
      },
    ],
  },
  {
    id: 'project-shell',
    storageKey: TOUR_STORAGE_KEYS['project-shell'],
    label: '项目导航教程',
    match: (pathname) => projectRootPattern.test(pathname),
    steps: [
      {
        id: 'project-name',
        selector: '[data-tour-project-name]',
        title: '当前项目',
        content: '这里显示当前卷宗名称，左侧导航中的功能都围绕这个项目展开。',
        placement: 'right',
      },
      {
        id: 'project-nav-world',
        selector: '[data-tour-nav-world]',
        interactiveClosest: '.ant-menu-item',
        title: '世界观',
        content: '用于维护地理、势力、文化、力量体系等世界设定。',
        placement: 'right',
      },
      {
        id: 'project-nav-characters',
        selector: '[data-tour-nav-characters]',
        interactiveClosest: '.ant-menu-item',
        title: '角色',
        content: '用于管理主要人物、配角、关系网和角色成长弧光。',
        placement: 'right',
      },
      {
        id: 'project-nav-outline',
        selector: '[data-tour-nav-outline]',
        interactiveClosest: '.ant-menu-item',
        title: '大纲',
        content: '用于规划卷、章、关键情节和故事推进结构。',
        placement: 'right',
      },
      {
        id: 'project-nav-chapters',
        selector: '[data-tour-nav-chapters]',
        interactiveClosest: '.ant-menu-item',
        title: '章节',
        content: '用于创建和编辑正文，管理章节状态与字数。',
        placement: 'right',
      },
      {
        id: 'project-nav-chat',
        selector: '[data-tour-nav-chat]',
        interactiveClosest: '.ant-menu-item',
        title: 'AI 助手',
        content: '用于与 AI 对话，协助整理设定、续写章节或审阅内容。',
        placement: 'right',
      },
      {
        id: 'project-nav-settings',
        selector: '[data-tour-nav-settings]',
        title: '项目设置',
        content: '左下角齿轮图标，用于维护当前卷宗的名称、描述等项目信息。',
        placement: 'right',
      },
      {
        id: 'project-chat-fab',
        selector: '[data-tour-project-chat-fab]',
        title: 'AI 问询',
        content: '右下角「问」按钮用于打开 AI 助手抽屉，可随时向 AI 提问或下达创作指令。',
        placement: 'left',
        forcePlacement: true,
        openChatDrawerOnNext: true,
        waitForSelector: '[data-tour-drawer-new-session]',
      },
      {
        id: 'project-chat-new-session',
        selector: '[data-tour-drawer-new-session]',
        title: '新建对话',
        content: '打开抽屉后，点击右上角的加号可开启一场新的 AI 对话。',
        placement: 'left',
      },
    ],
  },
  {
    id: 'world',
    storageKey: TOUR_STORAGE_KEYS.world,
    label: '世界观教程',
    match: (pathname) => /^\/projects\/[^/]+\/world$/.test(pathname),
    steps: [
      {
        id: 'world-header',
        selector: '[data-tour-world-header]',
        title: '世界观设定',
        content: '此页集中管理作品的世界设定。',
        placement: 'bottom',
      },
      {
        id: 'world-create',
        selector: '[data-tour-world-create]',
        title: '新建设定',
        content: '此按钮用于新增一条世界观设定。',
        placement: 'left',
      },
      {
        id: 'world-list',
        selector: '[data-tour-world-list]',
        title: '设定列表',
        content: '已创建的设定展示在此；若暂无内容，可通过空状态提示新建。',
        placement: 'top',
      },
    ],
  },
  {
    id: 'characters',
    storageKey: TOUR_STORAGE_KEYS.characters,
    label: '角色教程',
    match: (pathname) => /^\/projects\/[^/]+\/characters$/.test(pathname),
    steps: [
      {
        id: 'characters-create',
        selector: '[data-tour-characters-create]',
        title: '新建角色',
        content: '此按钮用于创建角色档案。',
        placement: 'left',
      },
      {
        id: 'characters-list',
        selector: '[data-tour-characters-list]',
        title: '角色列表',
        content: '角色卡片展示在此，进入编辑页可完善人物设定。',
        placement: 'top',
      },
      {
        id: 'characters-edit-hint',
        selector: '[data-tour-characters-edit-hint]',
        title: '编辑入口',
        content: '角色卡片是进入详情页的入口，可维护档案、关系和性格弧光。',
        placement: 'top',
      },
    ],
  },
  {
    id: 'outline',
    storageKey: TOUR_STORAGE_KEYS.outline,
    label: '大纲教程',
    match: (pathname) => /^\/projects\/[^/]+\/outline$/.test(pathname),
    steps: [
      {
        id: 'outline-header',
        selector: '[data-tour-outline-header]',
        title: '大纲编辑',
        content: '大纲用于规划故事结构和主要情节。',
        placement: 'bottom',
      },
      {
        id: 'outline-tree',
        selector: '[data-tour-outline-tree]',
        title: '大纲树',
        content: '左侧为卷、章等层级结构，可选择节点进行编辑。',
        placement: 'right',
      },
      {
        id: 'outline-add',
        selector: '[data-tour-outline-add]',
        title: '新增节点',
        content: '节点菜单中的「新建子节点」用于扩展大纲层级。',
        placement: 'bottom',
      },
      {
        id: 'outline-editor',
        selector: '[data-tour-outline-editor]',
        title: '节点编辑区',
        content: '右侧用于编辑当前选中节点的标题和内容，编辑后记得保存。',
        placement: 'left',
      },
    ],
  },
  {
    id: 'chapters',
    storageKey: TOUR_STORAGE_KEYS.chapters,
    label: '章节教程',
    match: (pathname) => /^\/projects\/[^/]+\/chapters$/.test(pathname),
    steps: [
      {
        id: 'chapters-header',
        selector: '[data-tour-chapters-header]',
        title: '章节管理',
        content: '此页管理正文章节，可查看字数、状态与更新时间。',
        placement: 'bottom',
      },
      {
        id: 'chapters-create',
        selector: '[data-tour-chapters-create]',
        title: '新建章节',
        content: '此按钮用于创建新的章节草稿。',
        placement: 'left',
      },
      {
        id: 'chapters-list',
        selector: '[data-tour-chapters-list]',
        title: '章节列表',
        content: '章节按序号展示，标题或编辑按钮可进入正文编辑页。',
        placement: 'top',
      },
    ],
  },
  {
    id: 'chat',
    storageKey: TOUR_STORAGE_KEYS.chat,
    label: 'AI 助手教程',
    match: (pathname) => /^\/projects\/[^/]+\/chat(?:\/.*)?$/.test(pathname),
    steps: [
      {
        id: 'chat-new-session',
        selector: '[data-tour-chat-new-session]',
        title: '新建对话',
        content: '加号按钮用于新建一份 AI 对话。',
        placement: 'left',
      },
      {
        id: 'chat-sessions',
        selector: '[data-tour-chat-sessions]',
        title: '会话列表',
        content: '已创建的会话展示在此，可切换不同对话。',
        placement: 'left',
      },
      {
        id: 'chat-input',
        selector: '[data-tour-chat-input]',
        title: '输入创作需求',
        content: '输入框用于描述世界观、设定、人物、篇幅等创作需求。',
        placement: 'top',
      },
      {
        id: 'chat-send',
        selector: '[data-tour-chat-send]',
        title: '发送消息',
        content: 'Enter 或发送按钮用于将需求提交给 AI。',
        placement: 'top',
      },
      {
        id: 'chat-confirm',
        selector: '[data-tour-chat-input]',
        title: '开始创作',
        content: '教程结束后，可在此输入作品相关需求，让 AI 协助创作。',
        placement: 'top',
      },
    ],
  },
  {
    id: 'system-settings',
    storageKey: TOUR_STORAGE_KEYS['system-settings'],
    label: '系统设置教程',
    match: (pathname) => pathname === '/settings',
    steps: [
      {
        id: 'system-settings-form',
        selector: '[data-tour-settings-form]',
        title: '系统配置',
        content: '此处配置模型服务、API Key 和跟踪选项。',
        placement: 'right',
      },
      {
        id: 'system-settings-actions',
        selector: '[data-tour-settings-actions]',
        title: '保存与测试',
        content: '修改配置后先保存，再测试模型连接是否可用。',
        placement: 'top',
      },
      {
        id: 'system-settings-sensitive',
        selector: '[data-tour-settings-sensitive]',
        title: '敏感字段',
        content: 'API Key 等敏感信息以掩码显示，留空表示保留原值。',
        placement: 'top',
      },
    ],
  },
  {
    id: 'project-settings',
    storageKey: TOUR_STORAGE_KEYS['project-settings'],
    label: '项目设置教程',
    match: (pathname) => /^\/projects\/[^/]+\/settings$/.test(pathname),
    steps: [
      {
        id: 'project-settings-form',
        selector: '[data-tour-project-settings-form]',
        title: '项目设置',
        content: '此处维护当前卷宗的名称、描述等项目级信息。',
        placement: 'right',
      },
    ],
  },
];

export const getToursForPath = (pathname: string) => {
  const matched = TOUR_CONFIGS.filter((tour) => tour.match(pathname));
  return matched.sort((a, b) => {
    if (a.id === 'project-shell') return 1;
    if (b.id === 'project-shell') return -1;
    return 0;
  });
};

export const getTourById = (tourId: TourId | null) => TOUR_CONFIGS.find((tour) => tour.id === tourId) || null;

const TOUR_RESET_VERSION_KEY = 'inkstone-tour-reset-version';
const TOUR_RESET_VERSION = '20260611-b';

export const clearAllTourStorageKeys = () => {
  Object.values(TOUR_STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
};

/** 版本变更时清空全部教程持久化标志，使各页面教程可再次首次触发 */
export const ensureTourStorageReset = () => {
  if (localStorage.getItem(TOUR_RESET_VERSION_KEY) === TOUR_RESET_VERSION) return;
  clearAllTourStorageKeys();
  localStorage.setItem(TOUR_RESET_VERSION_KEY, TOUR_RESET_VERSION);
};
