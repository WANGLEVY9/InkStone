import { useState, useEffect } from 'react';
import { Form, Input, Button, Space } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { projectsApi } from '@/api/projects';
import { useProjectContext } from '@/contexts/ProjectContext';
import PageHeader from '@/components/common/PageHeader';
import type { Project } from '@/types';
import PageContainer from '@/components/common/PageContainer';

const ProjectSettings = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const modal = useAppModal();
  const { setCurrentProject } = useProjectContext();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (!projectId) return;
    projectsApi.get(projectId).then(res => {
      setProject(res.data);
      form.setFieldsValue({
        name: res.data.name,
        description: res.data.description,
      });
      setLoading(false);
    }).catch(() => {
      message.error('加载项目失败');
      navigate('/');
    });
  }, [projectId]);

  const handleSave = async () => {
    if (!projectId) return;
    setSaving(true);
    try {
      const values = await form.validateFields();
      const res = await projectsApi.update(projectId, values);
      setProject(res.data);
      setCurrentProject(res.data);
      message.success('保存成功');
    } catch {
      // validation error
    }
    setSaving(false);
  };

  const handleDelete = () => {
    if (!projectId) return;
    modal.confirm({
      title: '确认删除项目',
      content: '删除后无法恢复，所有内容都将被删除。确认吗？',
      okText: '确认删除',
      okType: 'danger',
      onOk: async () => {
        try {
          await projectsApi.delete(projectId);
          setCurrentProject(null);
          message.success('项目已删除');
          navigate('/');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  if (loading || !project) return null;

  return (
    <PageContainer>
    <div>
      <PageHeader title="项目设置" subtitle={project.name} dataTour="project-settings-header" />

      <Form form={form} layout="vertical" data-tour-project-settings-form style={{ maxWidth: 600 }}>
        <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="description" label="项目描述">
          <Input.TextArea rows={4} />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
            <Button onClick={() => navigate('/')}>返回</Button>
          </Space>
        </Form.Item>
      </Form>

      <div style={{ marginTop: 48, padding: 24, border: '1px solid #ffccc7', borderRadius: 8 }}>
        <h3 style={{ color: '#cf1322', marginBottom: 8 }}>危险操作</h3>
        <p style={{ color: '#666', marginBottom: 16 }}>删除项目后，所有世界观、角色、大纲、章节内容都将被永久删除。</p>
        <Button danger onClick={handleDelete}>删除项目</Button>
      </div>
    </div>
    </PageContainer>
  );
};

export default ProjectSettings;
