import { useMemo } from 'react';
import { ActivityCalendar } from 'react-activity-calendar';

const VERMILION_RAMP: [string, string, string, string, string] = [
  '#EDE5D2',
  '#F0CFC8',
  '#E89A98',
  '#D6635E',
  '#C8323D',
];

function generateMockData(): { date: string; count: number; level: number }[] {
  const data: { date: string; count: number; level: number }[] = [];
  const today = new Date();
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    const hasActivity = Math.random() < (i < 90 ? 0.7 : 0.4);
    const count = hasActivity ? Math.floor(Math.random() * 10) + 1 : 0;
    const level = count === 0 ? 0 : Math.min(Math.ceil(count / 2), 4);
    data.push({ date: dateStr, count, level });
  }
  return data;
}

const ActivityHeatmap = () => {
  const mockData = useMemo(() => generateMockData(), []);
  const totalDays = useMemo(() => mockData.filter((d) => d.count > 0).length, [mockData]);

  return (
    <div className="heatmap-no-scrollbar" style={{ overflow: 'hidden' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: 10,
        }}
      >
        <span
          style={{
            color: 'var(--ink-heavy)',
            fontSize: 13,
            fontWeight: 700,
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.06em',
          }}
        >
          笔耕日历
        </span>
        <span
          style={{
            color: 'var(--ink-light)',
            fontSize: 11,
            fontFamily: 'var(--font-display)',
          }}
        >
          过去 365 日
        </span>
      </div>
      <ActivityCalendar
        data={mockData}
        colorScheme="light"
        showTotalCount={false}
        blockSize={10}
        blockMargin={2}
        fontSize={12}
        theme={{
          light: VERMILION_RAMP,
          dark: VERMILION_RAMP,
        }}
        labels={{
          months: [
            '正月',
            '二月',
            '三月',
            '四月',
            '五月',
            '六月',
            '七月',
            '八月',
            '九月',
            '十月',
            '冬月',
            '腊月',
          ],
          weekdays: ['日', '一', '二', '三', '四', '五', '六'],
        }}
        style={{ color: 'var(--ink-light)', fontFamily: 'var(--font-display)' }}
      />
      <div
        style={{
          color: 'var(--ink-light)',
          fontSize: 11,
          marginTop: 6,
          fontFamily: 'var(--font-display)',
        }}
      >
        过去一载，落墨{' '}
        <span style={{ color: 'var(--vermilion)', fontWeight: 700 }}>{totalDays}</span> 日
      </div>
    </div>
  );
};

export default ActivityHeatmap;
