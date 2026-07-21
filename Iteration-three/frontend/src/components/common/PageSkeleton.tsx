import { Skeleton } from 'antd';

const PageSkeleton = () => (
  <div style={{ padding: 24, maxWidth: 960 }}>
    <Skeleton active paragraph={{ rows: 1 }} title={{ width: '40%' }} />
    <div style={{ marginTop: 24 }}>
      <Skeleton active paragraph={{ rows: 8 }} />
    </div>
  </div>
);

export default PageSkeleton;
