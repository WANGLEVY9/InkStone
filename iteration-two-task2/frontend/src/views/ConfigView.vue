<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { getDatasetAnalysis, listDatasets } from "../api/dataset";
import { listMetrics } from "../api/metric";
import { listStrategies, saveStrategy, StrategyEntity } from "../api/strategy";

const form = reactive({
  name: "quality-heavy",
  metrics: ["response_time", "task_success", "answer_relevancy"],
  description: "强调效果准确性与成功率",
});

const weights = ref<Record<string, number>>({
  response_time: 0.2,
  task_success: 0.4,
  answer_relevancy: 0.4,
});

const saving = ref(false);
const loading = ref(false);
const activeTemplateLabel = ref("");
const metricDetailVisible = ref(false);
const currentMetricKey = ref("");
const strategyList = ref<StrategyEntity[]>([]);
const metricOptions = ref<string[]>(["response_time", "token_usage", "task_success", "answer_relevancy"]);
const dimensionWeights = ref<Record<string, number>>({
  plan: 0.18,
  tool: 0.16,
  tool_relevance: 0.06,
  hallucination: 0.16,
  memory: 0.12,
  context_consistency: 0.06,
  efficiency: 0.20,
});
const dimensionWeightOpen = ref(false);

const dimensionLabels: Record<string, string> = {
  plan: "plan（规划）",
  tool: "tool（工具）",
  tool_relevance: "tool_relevance（工具相关性）",
  hallucination: "hallucination（幻觉）",
  memory: "memory（记忆）",
  context_consistency: "context_consistency（上下文连贯性）",
  efficiency: "efficiency（效率）",
};
const datasetOptions = ref<Array<{ dataset_id: string; name: string }>>([]);
const selectedDatasetId = ref("");
const realtimeInsights = ref<{ live_metrics: Record<string, number>; findings: string[] } | null>(null);

const presetTemplates: Array<{ label: string; metrics: string[]; weights: Record<string, number>; description: string }> = [
  {
    label: "效果优先",
    metrics: ["task_success", "answer_relevancy", "faithfulness"],
    weights: { task_success: 0.4, answer_relevancy: 0.35, faithfulness: 0.25 },
    description: "强调任务成功与回答可信度",
  },
  {
    label: "稳定性优先",
    metrics: ["runtime_success_rate", "runtime_error_rate", "response_time"],
    weights: { runtime_success_rate: 0.5, runtime_error_rate: 0.25, response_time: 0.25 },
    description: "强调连续运行稳定性与时延控制",
  },
  {
    label: "成本性能平衡",
    metrics: ["response_time", "token_usage", "runtime_avg_latency_ms"],
    weights: { response_time: 0.35, token_usage: 0.4, runtime_avg_latency_ms: 0.25 },
    description: "兼顾交互速度与资源消耗",
  },
];

const metricDetails: Record<string, { title: string; description: string; source: string }> = {
  faithfulness: {
    title: "faithfulness（事实一致性）",
    description:
      "衡量回答是否忠于给定事实与上下文，分值越高表示越少出现幻觉。该指标通常结合 RAGAS/LLM Judge 计算，在依赖缺失时可能回退到启发式值。",
    source: "文档依据：README/运维说明中关于高级评测与 answer_relevancy/faithfulness 的说明。",
  },
  task_success: {
    title: "task_success（任务成功率）",
    description:
      "表示任务是否成功完成。在输入样本中 `task_success=true` 计为 1，`false` 计为 0，常用于衡量完成率。",
    source: "文档依据：README 显式样本字段说明 + 后端指标注册逻辑。",
  },
  answer_relevancy: {
    title: "answer_relevancy（答案相关性）",
    description:
      "衡量回答与问题目标的相关程度，分值越高说明回答越贴题、偏离越少。常与 faithfulness 组合评估效果质量。",
    source: "文档依据：运维说明中 answer_relevancy/faithfulness 指标说明。",
  },
  runtime_success_rate: {
    title: "runtime_success_rate（运行成功率）",
    description:
      "统计运行轨迹中成功记录的占比，越接近 1 代表运行越稳定、可用性越高。",
    source: "文档依据：运行时评测指标定义（evaluation engine 聚合指标）。",
  },
  runtime_error_rate: {
    title: "runtime_error_rate（运行错误率）",
    description:
      "统计运行轨迹中错误记录的占比，数值越低越好，常与 runtime_success_rate 联合观察稳定性。",
    source: "文档依据：运行时评测指标定义（evaluation engine 聚合指标）。",
  },
  response_time: {
    title: "response_time（响应时长）",
    description:
      "来源于样本字段 `response_time_ms`，反映请求响应速度。通常越低越好，适用于稳定性和成本性能场景。",
    source: "文档依据：README 显式样本字段 `response_time_ms`。",
  },
  token_usage: {
    title: "token_usage（Token 消耗）",
    description:
      "来源于样本字段 `token_usage`，表示一次交互消耗的 token 量。通常越低越省成本。",
    source: "文档依据：README 显式样本字段 `token_usage`。",
  },
  runtime_avg_latency_ms: {
    title: "runtime_avg_latency_ms（运行平均时延）",
    description:
      "聚合一段运行轨迹的平均时延（毫秒），用于评估系统在连续运行下的真实延迟表现，越低越好。",
    source: "文档依据：运行时评测指标定义（evaluation engine 聚合指标）。",
  },
};

const metricDetailTargets = new Set([
  "faithfulness",
  "task_success",
  "answer_relevancy",
  "runtime_success_rate",
  "runtime_error_rate",
  "response_time",
  "token_usage",
  "runtime_avg_latency_ms",
]);

const currentMetricDetail = computed(() =>
  metricDetails[currentMetricKey.value] ?? {
    title: currentMetricKey.value,
    description: "暂无该指标的详细解释。",
    source: "文档依据：-",
  }
);

const showMetricDetail = (metric: string) => {
  currentMetricKey.value = metric;
  metricDetailVisible.value = true;
};

const selectedWeightRows = computed(() =>
  form.metrics.map((metric) => ({
    metric,
    value: Number(weights.value[metric] ?? 0),
  }))
);

const totalWeight = computed(() => selectedWeightRows.value.reduce((sum, row) => sum + row.value, 0));

const refreshStrategies = async () => {
  loading.value = true;
  try {
    strategyList.value = await listStrategies();
  } catch {
    strategyList.value = [];
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await Promise.all([refreshStrategies(), refreshMetrics(), refreshDatasets()]);
});

const ensureWeightsForMetrics = () => {
  if (!form.metrics.length) {
    weights.value = {};
    return;
  }

  const existing = { ...weights.value };
  const synced: Record<string, number> = {};
  form.metrics.forEach((metric) => {
    synced[metric] = Number(existing[metric] ?? 0);
  });

  const total = Object.values(synced).reduce((acc, cur) => acc + cur, 0);
  if (total <= 0) {
    const avg = 1 / form.metrics.length;
    form.metrics.forEach((metric) => {
      synced[metric] = Number(avg.toFixed(4));
    });
  }

  weights.value = synced;

  // 校正舍入误差：保证总和精确为 1.0
  const curTotal = totalWeight.value;
  if (Math.abs(curTotal - 1) > 0.0001 && form.metrics.length > 0) {
    const last = form.metrics[form.metrics.length - 1];
    weights.value[last] = Number((Number(weights.value[last] ?? 0) + (1 - curTotal)).toFixed(6));
  }
};

watch(
  () => [...form.metrics],
  () => {
    ensureWeightsForMetrics();
  },
  { immediate: true }
);

const normalizeWeights = () => {
  if (!form.metrics.length) return;
  const total = totalWeight.value;
  if (total <= 0) {
    const avg = 1 / form.metrics.length;
    form.metrics.forEach((metric) => {
      weights.value[metric] = Number(avg.toFixed(4));
    });
  } else {
    form.metrics.forEach((metric) => {
      weights.value[metric] = Number((Number(weights.value[metric] ?? 0) / total).toFixed(4));
    });
  }
  // 校正舍入误差：将差值补偿到最后一个指标，保证总和精确为 1.0
  const curTotal = totalWeight.value;
  if (Math.abs(curTotal - 1) > 0.0001 && form.metrics.length > 0) {
    const last = form.metrics[form.metrics.length - 1];
    weights.value[last] = Number((Number(weights.value[last] ?? 0) + (1 - curTotal)).toFixed(6));
  }
  ElMessage.success("已完成权重归一化");
};

const refreshMetrics = async () => {
  try {
    const metrics = await listMetrics();
    metricOptions.value = Array.from(new Set([...metricOptions.value, ...metrics.map((item) => item.name)]));
  } catch {
    // fallback to builtin list when backend is unavailable
  }
};

const refreshDatasets = async () => {
  try {
    const datasets = await listDatasets();
    datasetOptions.value = datasets.items.map((item) => ({ dataset_id: item.dataset_id, name: item.name }));
    if (!selectedDatasetId.value && datasetOptions.value.length) {
      selectedDatasetId.value = datasetOptions.value[0].dataset_id;
    }
  } catch {
    datasetOptions.value = [];
  }
};

const applyDatasetMetrics = async () => {
  if (!selectedDatasetId.value) {
    ElMessage.warning("请先选择一个已上传数据集");
    return;
  }

  try {
    const analysis = await getDatasetAnalysis(selectedDatasetId.value);
    realtimeInsights.value = {
      live_metrics: analysis.live_metrics,
      findings: analysis.findings,
    };
    const metricNames = Object.keys(analysis.live_metrics || {});
    if (metricNames.length) {
      metricOptions.value = Array.from(new Set([...metricOptions.value, ...metricNames]));
      form.metrics = Array.from(new Set([...form.metrics, ...metricNames]));
      ensureWeightsForMetrics();
      normalizeWeights();
    }
    ElMessage.success("已根据数据集实时分析结果补充指标");
  } catch {
    ElMessage.error("加载数据集分析失败");
  }
};

const applyTemplate = (template: { label: string; metrics: string[]; weights: Record<string, number>; description: string }) => {
  form.metrics = [...template.metrics];
  form.description = template.description;
  weights.value = { ...template.weights };
  activeTemplateLabel.value = template.label;
  metricOptions.value = Array.from(new Set([...metricOptions.value, ...template.metrics]));
  ensureWeightsForMetrics();
  ElMessage.success(`已应用模板：${template.label}`);
};

const save = async () => {
  if (!form.metrics.length) {
    ElMessage.warning("请至少选择一个指标");
    return;
  }

  if (Math.abs(totalWeight.value - 1) > 0.001) {
    ElMessage.warning("所选指标权重总和需为 1.0，可点击“归一化权重”自动调整");
    return;
  }

  saving.value = true;
  try {
    const selectedWeights = form.metrics.reduce<Record<string, number>>((acc, metric) => {
      acc[metric] = Number(weights.value[metric] ?? 0);
      return acc;
    }, {});

    await saveStrategy({
      name: form.name,
      metrics: form.metrics,
      weights: selectedWeights,
      description: form.description,
      dimension_weights: { ...dimensionWeights.value },
    });
    ElMessage.success("组合策略已保存");
    await refreshStrategies();
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "请求失败，请检查后端服务是否正常";
    ElMessage.error("保存策略失败: " + msg);
  } finally {
    saving.value = false;
  }
};

const applyStrategy = (item: StrategyEntity) => {
  form.name = item.name;
  form.metrics = item.metrics;
  form.description = item.description ?? "";
  const nextWeights: Record<string, number> = {};
  Object.entries(item.weights).forEach(([key, value]) => {
    nextWeights[key] = Number(value ?? 0);
  });
  weights.value = nextWeights;
  if (item.dimension_weights) {
    dimensionWeights.value = { ...item.dimension_weights };
  }
  activeTemplateLabel.value = "";
  ensureWeightsForMetrics();
  ElMessage.success("已回填策略配置");
};

const refreshAll = async () => {
  await Promise.all([refreshStrategies(), refreshMetrics(), refreshDatasets()]);
  ElMessage.success("策略与指标列表已刷新");
};
</script>

<template>
  <section class="panel card-rise">
    <div class="panel-head stagger-item" style="--stagger-order: 0">
      <div>
        <h2>评测配置中心</h2>
        <p>支持模式/方式/维度组合与自定义策略权重</p>
      </div>
    </div>

    <el-form label-width="160px" class="config-form stagger-item" style="--stagger-order: 1">
      <el-form-item label="快速模板">
        <div class="template-row">
          <el-button
            v-for="tpl in presetTemplates"
            :key="tpl.label"
            class="template-btn"
            :class="{ 'template-btn-active': activeTemplateLabel === tpl.label }"
            @click="applyTemplate(tpl)"
          >
            {{ tpl.label }}
          </el-button>
        </div>
      </el-form-item>
      <el-form-item label="策略名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="策略描述"><el-input v-model="form.description" /></el-form-item>
      <el-form-item label="数据集联动">
        <div class="dataset-row">
          <el-select v-model="selectedDatasetId" filterable placeholder="选择数据集" style="width: 260px">
            <el-option v-for="item in datasetOptions" :key="item.dataset_id" :label="item.name" :value="item.dataset_id" />
          </el-select>
          <el-button type="success" plain @click="applyDatasetMetrics">解析并补充指标</el-button>
        </div>
      </el-form-item>
      <el-form-item label="指标组合">
        <el-select v-model="form.metrics" multiple style="width: 100%">
          <el-option v-for="metric in metricOptions" :key="metric" :value="metric" :label="metric" />
        </el-select>
      </el-form-item>
      <el-form-item v-for="row in selectedWeightRows" :key="row.metric" :label="`${row.metric}权重`">
        <div class="metric-weight-row">
          <el-slider v-model="weights[row.metric]" :min="0" :max="1" :step="0.05" show-input />
          <el-button
            v-if="metricDetailTargets.has(row.metric)"
            class="metric-detail-btn"
            type="primary"
            link
            @click="showMetricDetail(row.metric)"
          >
            查看详情
          </el-button>
        </div>
      </el-form-item>
      <el-form-item label="当前权重总和">
        <el-tag :type="Math.abs(totalWeight - 1) < 0.001 ? 'success' : 'warning'">{{ totalWeight.toFixed(4) }}</el-tag>
      </el-form-item>
      <el-form-item>
        <el-button @click="normalizeWeights">归一化权重</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存策略</el-button>
        <el-button @click="refreshAll" :loading="loading">刷新策略列表</el-button>
      </el-form-item>
      <el-form-item label="批量评估维度权重">
        <el-button size="small" @click="dimensionWeightOpen = !dimensionWeightOpen">
          {{ dimensionWeightOpen ? '收起' : '展开配置' }}
        </el-button>
      </el-form-item>
      <template v-if="dimensionWeightOpen">
        <el-form-item v-for="(label, key) in dimensionLabels" :key="key" :label="label">
          <el-slider v-model="dimensionWeights[key]" :min="0" :max="1" :step="0.01" show-input style="width: 400px" />
        </el-form-item>
      </template>
    </el-form>

    <div class="insight-wrap stagger-item" style="--stagger-order: 2" v-if="realtimeInsights">
      <h3>数据集实时评估洞察</h3>
      <div class="insight-kpi">
        <article v-for="(value, key) in realtimeInsights.live_metrics" :key="key">
          <label>{{ key }}</label>
          <strong>{{ Number(value).toFixed(4) }}</strong>
        </article>
      </div>
      <ul>
        <li v-for="(item, idx) in realtimeInsights.findings" :key="idx">{{ item }}</li>
      </ul>
    </div>

    <div class="strategy-table-wrap stagger-item" style="--stagger-order: 3">
      <h3>已保存策略</h3>
      <el-table :data="strategyList" size="small" border v-loading="loading">
        <el-table-column prop="name" label="策略名" min-width="160" />
        <el-table-column prop="metrics" label="指标组合" min-width="220">
          <template #default="scope">{{ scope.row.metrics.join(", ") }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="220" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" type="primary" link @click="applyStrategy(scope.row)">回填</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="metricDetailVisible" width="560px" :title="currentMetricDetail.title">
      <div class="metric-detail-content">
        <p>{{ currentMetricDetail.description }}</p>
        <p class="metric-detail-source">{{ currentMetricDetail.source }}</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="metricDetailVisible = false">我知道了</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.config-form {
  max-width: 840px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid #d5e2f5;
}

.strategy-table-wrap {
  margin-top: 18px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid #d5e2f5;
}

.template-row,
.dataset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.template-btn {
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.template-btn:hover {
  transform: translateY(-1px);
}

.template-btn-active {
  color: #fff !important;
  border-color: #1e40af !important;
  background: linear-gradient(135deg, #1d4ed8, #0f766e) !important;
  box-shadow: 0 10px 22px rgba(29, 78, 216, 0.32);
  filter: saturate(1.1);
}

.metric-weight-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
}

.metric-weight-row :deep(.el-slider) {
  flex: 1;
}

.metric-detail-btn {
  flex-shrink: 0;
  font-weight: 600;
}

.insight-wrap {
  margin-top: 16px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid #d5e2f5;
}

.insight-wrap h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.insight-wrap ul {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #334155;
}

.insight-kpi {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.insight-kpi article {
  border-radius: 10px;
  border: 1px solid #d8e3f4;
  background: rgba(255, 255, 255, 0.82);
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.insight-kpi label {
  color: #64748b;
}

.insight-kpi strong {
  color: #0f766e;
}

.strategy-table-wrap h3 {
  margin: 0 0 10px;
  font-size: 16px;
  letter-spacing: 0.2px;
}

.metric-detail-content p {
  margin: 0 0 10px;
  color: #334155;
  line-height: 1.65;
}

.metric-detail-source {
  font-size: 13px;
  color: #64748b !important;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
}

:deep(.el-slider__runway) {
  background: #e3edf9;
}

:deep(.el-slider__bar) {
  background: linear-gradient(90deg, #ef6c2f, #157a6e);
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #f4f8ff;
}
</style>
