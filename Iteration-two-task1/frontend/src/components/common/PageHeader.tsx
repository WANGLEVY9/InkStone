import { Breadcrumb, Space } from 'antd';
import { Link } from 'react-router-dom';

interface BreadcrumbItem {
  title: string;
  path?: string;
}

interface PageHeaderProps {
  title?: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  extra?: React.ReactNode;
  leftExtra?: React.ReactNode;
}

const PageHeader = ({ title, subtitle, breadcrumbs, extra, leftExtra }: PageHeaderProps) => {
  return (
    <div style={{ marginBottom: 24 }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumb
          style={{ marginBottom: 10, fontFamily: 'var(--font-display)', letterSpacing: '0.04em' }}
          items={breadcrumbs.map(item => ({
            title: item.path ? <Link to={item.path}>{item.title}</Link> : item.title,
          }))}
        />
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {leftExtra}
          {title && (
            <div>
              <h1 className="literati-heading">{title}</h1>
              <div className="literati-heading-rule" />
              {subtitle && (
                <p
                  style={{
                    margin: '8px 0 0',
                    color: 'var(--ink-light)',
                    fontSize: 12,
                    fontFamily: 'var(--font-display)',
                    letterSpacing: '0.08em',
                  }}
                >
                  {subtitle}
                </p>
              )}
            </div>
          )}
        </div>
        {extra && <Space>{extra}</Space>}
      </div>
    </div>
  );
};

export default PageHeader;
