import { Welcome, Prompts } from '@ant-design/x';

interface WelcomeScreenProps {
  onSend: (message: string) => void;
}

const SealIcon = ({ char, color }: { char: string; color: string }) => (
  <div
    style={{
      width: 36,
      height: 36,
      borderRadius: 'var(--radius-sm)',
      border: `1.5px solid ${color}`,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      color,
      fontFamily: 'var(--font-display)',
      fontWeight: 700,
      fontSize: 17,
      letterSpacing: 0,
      background: 'transparent',
      flexShrink: 0,
    }}
  >
    {char}
  </div>
);

const PROMPT_ITEMS = [
  {
    key: 'world',
    icon: <SealIcon char="域" color="var(--bamboo)" />,
    label: '构建世界观',
    description: '立地理、定文化、述沿革',
  },
  {
    key: 'character',
    icon: <SealIcon char="人" color="var(--vermilion)" />,
    label: '构建人物设定',
    description: '勾形貌、定性情、连关系',
  },
  {
    key: 'plot',
    icon: <SealIcon char="纲" color="var(--gold-leaf)" />,
    label: '构建故事大纲',
    description: '排卷次、布章节、列起伏',
  },
  {
    key: 'chapter',
    icon: <SealIcon char="笔" color="var(--ink-heavy)" />,
    label: '开始章节写作',
    description: '依纲叙事，缀字成文',
  },
];

const WelcomeScreen = ({ onSend }: WelcomeScreenProps) => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flex: 1,
        padding: 24,
      }}
    >
      <Welcome
        icon={
          <div
            className="seal-stamp"
            style={{
              width: 56,
              height: 56,
              fontSize: 28,
              borderRadius: 'var(--radius-sm)',
            }}
            aria-hidden="true"
          >
            润
          </div>
        }
        title="书房润笔"
        description="构世、塑人、定纲、落笔——皆可托付"
        variant="filled"
        styles={{
          title: {
            fontFamily: 'var(--font-display)',
            color: 'var(--ink-heavy)',
            letterSpacing: '0.06em',
          },
          description: {
            fontFamily: 'var(--font-body)',
            color: 'var(--ink-medium)',
            letterSpacing: '0.04em',
          },
        }}
        extra={
          <Prompts
            items={PROMPT_ITEMS}
            wrap
            onItemClick={({ data }) => onSend(data.label as string)}
            styles={{
              item: {
                fontFamily: 'var(--font-display)',
              },
            }}
          />
        }
      />
    </div>
  );
};

export default WelcomeScreen;
