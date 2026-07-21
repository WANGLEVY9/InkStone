import { useState, useEffect, useRef } from 'react';
import { Form, Input, InputNumber, Switch, Button, Space, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { configApi, KEEP_EXISTING } from '@/api/config';
import PageHeader from '@/components/common/PageHeader';
import PageContainer from '@/components/common/PageContainer';
import type { ConfigResponse } from '@/types';

const SENSITIVE_KEYS = new Set(['anthropic_api_key', 'langsmith_api_key']);

const SystemSettings = () => {
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [maskedPlaceholders, setMaskedPlaceholders] = useState<Record<string, string>>({});
  const initialLoadDone = useRef(false);

  useEffect(() => {
    configApi.get().then(res => {
      const data: ConfigResponse = res.data;
      const formValues: Record<string, unknown> = {};
      const placeholders: Record<string, string> = {};

      for (const item of data.items) {
        if (SENSITIVE_KEYS.has(item.key)) {
          // Sensitive: store masked value as placeholder, leave input empty
          if (item.value) {
            placeholders[item.key] = `已设置 (${item.value})`;
          }
          formValues[item.key] = '';
        } else if (item.key === 'langsmith_tracing') {
          formValues[item.key] = item.value === 'true';
        } else if (item.key === 'llm_max_tokens') {
          formValues[item.key] = item.value ? parseInt(item.value, 10) : undefined;
        } else {
          formValues[item.key] = item.value || '';
        }
      }

      form.setFieldsValue(formValues);
      setMaskedPlaceholders(placeholders);
      initialLoadDone.current = true;
      setLoading(false);
    }).catch(() => {
      message.error('加载配置失败');
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const values = await form.validateFields();

      // Replace empty sensitive fields with KEEP_EXISTING sentinel
      const payload: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(values)) {
        if (SENSITIVE_KEYS.has(key) && (value === '' || value === undefined)) {
          payload[key] = KEEP_EXISTING;
        } else {
          payload[key] = value;
        }
      }

      await configApi.update(payload as Parameters<typeof configApi.update>[0]);
      message.success('配置已保存');
      setHasChanges(false);

      // Reload to get fresh masked values
      const res = await configApi.get();
      const placeholders: Record<string, string> = {};
      for (const item of res.data.items) {
        if (SENSITIVE_KEYS.has(item.key) && item.value) {
          placeholders[item.key] = `已设置 (${item.value})`;
        }
      }
      setMaskedPlaceholders(placeholders);
      // Clear sensitive fields after save
      for (const key of SENSITIVE_KEYS) {
        form.setFieldValue(key, '');
      }
    } catch {
      // validation error
    }
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await configApi.test();
      const data = res.data;
      if (data.success) {
        message.success(`连接成功，延迟 ${data.latency_ms} ms`);
      } else {
        message.error(data.message || '连接测试失败');
      }
    } catch {
      message.error('连接测试失败');
    }
    setTesting(false);
  };

  if (loading) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', paddingTop: 120 }}>
          <Spin size="large" />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader title="系统设置" subtitle="LLM 配置" dataTour="settings-header" />

      <Form
        form={form}
        layout="vertical"
        data-tour-settings-form
        style={{ maxWidth: 600 }}
        onValuesChange={() => {
          if (initialLoadDone.current) setHasChanges(true);
        }}
      >
        <Form.Item
          name="llm_base_url"
          label="LLM Base URL"
        >
          <Input placeholder="https://api.anthropic.com" />
        </Form.Item>

        <div data-tour-settings-sensitive>
        <Form.Item
          name="anthropic_api_key"
          label="Anthropic API Key"
        >
          <Input.Password
            placeholder={maskedPlaceholders.anthropic_api_key || '请输入 API Key'}
          />
        </Form.Item>

        <Form.Item name="langsmith_api_key" label="LangSmith API Key">
          <Input.Password
            placeholder={maskedPlaceholders.langsmith_api_key || '可选'}
          />
        </Form.Item>
        </div>

        <Form.Item
          name="langsmith_tracing"
          label="LangSmith Tracing"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="langsmith_endpoint"
          label="LangSmith Endpoint"
        >
          <Input placeholder="https://api.smith.langchain.com" />
        </Form.Item>

        <Form.Item
          name="langsmith_project"
          label="LangSmith Project"
        >
          <Input placeholder="novel" />
        </Form.Item>

        <Form.Item
          name="llm_model"
          label="LLM Model"
        >
          <Input placeholder="claude-sonnet-4-20250514" />
        </Form.Item>

        <Form.Item
          name="llm_max_tokens"
          label="LLM Max Tokens"
        >
          <InputNumber min={1} style={{ width: '100%' }} placeholder="65536" />
        </Form.Item>

        <Form.Item data-tour-settings-actions>
          <Space>
            <Button type="primary" loading={saving} onClick={handleSave}>
              保存
            </Button>
            <Button
              loading={testing}
              disabled={hasChanges}
              onClick={handleTest}
            >
              测试连接
            </Button>
            <Button onClick={() => navigate('/')}>返回</Button>
          </Space>
        </Form.Item>
      </Form>
    </PageContainer>
  );
};

export default SystemSettings;
