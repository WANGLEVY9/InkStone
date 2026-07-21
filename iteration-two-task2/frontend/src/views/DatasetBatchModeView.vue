<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import type { UploadRequestOptions } from "element-plus";

import { listDatasets, uploadDataset } from "../api/dataset";
import { listStrategies, type StrategyEntity } from "../api/strategy";
import { BatchEvalJob, getBatchJob, listBatchJobs, runBatchEval } from "../api/modeEval";

const datasets = ref<Array<{ dataset_id: string; name: string; filename: string }>>([]);
const selectedDatasetId = ref("");
const strategies = ref<StrategyEntity[]>([]);
const selectedStrategyName = ref("");
const jobs = ref<BatchEvalJob[]>([]);
const activeJobId = ref("");
const activeJob = ref<BatchEvalJob | null>(null);
const running = ref(false);
const loading = ref(false);
const loadError = ref("");
const uploading = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;
const sampleDatasets = [
  { name: "实时过程样例 (JSONL)", file: "/sample-datasets/realtime_trace_sample.jsonl" },
  { name: "离线轨迹样例 (JSON)", file: "/sample-datasets/offline_trace_sample.json" },
  { name: "批量评测样例 (CSV)", file: "/sample-datasets/batch_eval_sample.csv" },
  { name: "RAG 评测样例 (JSON)", file: "/sample-datasets/rag_eval_sample.json" },
];

const refreshDatasets = async () => {
  try {
    const data = await listDatasets();
    datasets.value = data.items.map((item) => ({
      dataset_id: item.dataset_id,
      name: item.name,
      filename: item.filename,
    }));
    if (!selectedDatasetId.value && datasets.value.length) {
      selectedDatasetId.value = datasets.value[0].dataset_id;
    }
    loadError.value = "";
  } catch {
    loadError.value = "数据集列表加载失败";
  }
};

const refreshJobs = async () => {
  try {
    const data = await listBatchJobs();
    jobs.value = data.items;
    if (!activeJobId.value && jobs.value.length) {
      activeJobId.value = jobs.value[0].job_id;
    }
    loadError.value = "";
  } catch {
    loadError.value = "任务列表加载失败";
  }
};

const refreshActiveJob = async () => {
  if (!activeJobId.value) {
    activeJob.value = null;
    return;
  }
  try {
    activeJob.value = await getBatchJob(activeJobId.value);
    loadError.value = "";
  } catch {
    loadError.value = "任务详情加载失败";
  }
};

const refreshStrategies = async () => {
  try {
    strategies.value = await listStrategies();
  } catch {
    strategies.value = [];
  }
};

const refreshAll = async () => {
  loading.value = true;
  try {
    await Promise.all([refreshDatasets(), refreshJobs(), refreshStrategies()]);
    await refreshActiveJob();
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await refreshAll();
  pollTimer = setInterval(() => {
    void refreshAll();
  }, 4000);
});

onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
});

const onUploadDataset = async (options: UploadRequestOptions) => {
  uploading.value = true;
  try {
    await uploadDataset(options.file as File);
    ElMessage.success("数据集上传成功");
    await refreshDatasets();
    options.onSuccess?.({});
  } catch (error) {
    options.onError?.(error as any);
    ElMessage.error("上传失败，请检查文件格式");
  } finally {
    uploading.value = false;
  }
};

const runBatch = async () => {
  if (!selectedDatasetId.value) {
    ElMessage.warning("请先选择数据集");
    return;
  }
  running.value = true;
  try {
    const job = await runBatchEval(selectedDatasetId.value, selectedStrategyName.value || undefined);
    activeJobId.value = job.job_id;
    ElMessage.success("批量评估任务已启动");
    await refreshAll();
  } finally {
    running.value = false;
  }
};

const statusTagType = (status: string) => {
  if (status === "completed") return "success";
  if (status === "running") return "warning";
  if (status === "failed") return "danger";
  return "info";
};

const progressPercent = computed(() => {
  const p = activeJob.value?.progress;
  if (!p || p.total <= 0) return 0;
  return Math.round((p.processed / p.total) * 100);
});

const rootCauseLabels: Record<string, string> = {
  none: "成功",
  tool_misuse: "工具误用",
  hallucination_risk: "幻觉风险",
  inefficient_plan: "低效规划",
  inconsistent_context: "上下文不一致",
  irrelevant_tool_use: "工具不相关",
  task_mismatch: "任务不匹配",
};

const scoreRows = computed(() => {
  const scoreMap = activeJob.value?.summary?.average_scores ?? {};
  return Object.entries(scoreMap).map(([name, value]) => ({ name, value: Number(value) }));
});

const avgScoreOption = computed(() => ({
  tooltip: { trigger: "axis" },
  title: { text: "各维度平均得分", left: "center", textStyle: { fontSize: 14 } },
  xAxis: {
    type: "category",
    data: scoreRows.value.map((item) => item.name),
    axisLabel: { interval: 0, rotate: 20 },
    name: "评估维度",
    nameLocation: "center",
    nameGap: 30,
  },
  yAxis: { type: "value", min: 0, max: 100, name: "平均得分" },
  grid: { top: 40, left: 50, right: 20, bottom: 50 },
  series: [
    {
      type: "bar",
      data: scoreRows.value.map((item) => item.value),
      itemStyle: { color: "#ef6c2f" },
      label: { show: true, position: "top", formatter: (p: { value: number }) => p.value.toFixed(2) },
    },
  ],
}));

const rootCausePieOption = computed(() => {
  const distribution = activeJob.value?.summary?.root_cause_distribution ?? {};
  return {
    title: { text: "根因分布", left: "center", textStyle: { fontSize: 14 } },
    tooltip: { trigger: "item", formatter: (p: { name: string; value: number; percent: number }) => `${p.name}: ${p.value} (${p.percent}%)` },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["35%", "68%"],
        data: Object.entries(distribution).map(([name, value]) => ({
          name: rootCauseLabels[name] ?? name,
          value,
        })),
        label: { formatter: "{b}: {d}%" },
      },
    ],
  };
});
</script>

<template>
  <section class="panel card-rise" v-loading="loading">
    <div class="panel-head">
      <div>
        <h2>模式3：离线数据集评估（历史数据批量评测）</h2>
        <p>导入历史日志/数据集，批量执行统一评估引擎，输出对比摘要报告</p>
      </div>
      <div class="actions">
        <el-button @click="refreshAll">刷新</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" :title="loadError" type="error" show-icon :closable="true" class="load-error" @close="loadError = ''" />

    <el-card shadow="never" class="card-block">
      <template #header>数据集选择与批量任务启动</template>
      <div class="dataset-row">
        <el-select v-model="selectedDatasetId" style="min-width: 320px" filterable placeholder="选择已上传数据集">
          <el-option
            v-for="item in datasets"
            :key="item.dataset_id"
            :label="`${item.name} (${item.filename})`"
            :value="item.dataset_id"
          />
        </el-select>
        <el-select v-model="selectedStrategyName" placeholder="选择策略(可选)" clearable style="min-width: 200px">
          <el-option label="无策略(默认权重)" value="" />
          <el-option v-for="s in strategies" :key="s.name" :label="s.name" :value="s.name" />
        </el-select>
        <el-upload :show-file-list="false" :http-request="onUploadDataset" accept=".json,.jsonl,.csv">
          <el-button type="primary" plain :loading="uploading">上传数据集</el-button>
        </el-upload>
        <el-button type="success" :loading="running" @click="runBatch">启动批量评估</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="card-block">
      <template #header>示例数据</template>
      <div class="sample-datasets">
        <span class="text-muted">下载示例后可直接通过“上传数据集”导入并发起评测：</span>
        <a v-for="sample in sampleDatasets" :key="sample.file" :href="sample.file" download class="sample-link">
          <el-button size="small" plain>{{ sample.name }}</el-button>
        </a>
      </div>
    </el-card>

    <div class="batch-layout">
      <el-card shadow="never" class="card-block">
        <template #header>批量评估任务队列</template>
        <el-table :data="jobs" size="small" height="280" v-if="jobs.length > 0">
          <el-table-column prop="job_id" label="Job ID" min-width="180" />
          <el-table-column label="状态" width="110">
            <template #default="scope">
              <el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="140">
            <template #default="scope">
              <span v-if="scope.row.status === 'running' && scope.row.progress">
                <el-progress :percentage="Math.round((scope.row.progress.processed ?? 0) / Math.max(scope.row.progress.total ?? 1, 1) * 100)" :stroke-width="10" />
              </span>
              <span v-else class="text-muted">{{ scope.row.status === 'queued' ? '等待中' : scope.row.status === 'completed' ? '已完成' : scope.row.status === 'failed' ? '失败' : '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" link type="primary" @click="activeJobId = scope.row.job_id; refreshActiveJob()">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无批量任务，请上传数据集并启动评估" />
      </el-card>

      <el-card shadow="never" class="card-block">
        <template #header>批量评估进度</template>
        <div v-if="activeJob && activeJob.status === 'running'" class="progress-area">
          <el-progress :percentage="progressPercent" status="warning" :stroke-width="16" />
          <p class="progress-label">已处理 {{ activeJob.progress?.processed ?? 0 }} / {{ activeJob.progress?.total ?? 0 }} 条</p>
        </div>
        <el-empty v-else-if="activeJob && activeJob.status === 'queued'" description="任务已加入队列，等待执行..." />
        <div v-else-if="!activeJob || activeJob.status === 'completed' || activeJob.status === 'failed'" class="progress-placeholder">
          <el-tag :type="activeJob?.status === 'completed' ? 'success' : 'danger'" v-if="activeJob?.status === 'completed' || activeJob?.status === 'failed'">
            {{ activeJob.status === 'completed' ? '评估已完成' : '评估失败' }}
          </el-tag>
          <span v-else class="text-muted">选择一个任务查看进度</span>
        </div>
      </el-card>

      <el-card shadow="never" class="card-block" v-if="activeJob?.summary">
        <template #header>批量评估摘要</template>
        <div class="summary-kpi">
          <article>
            <label>样本总数</label>
            <strong>{{ activeJob.summary.total_traces }}</strong>
          </article>
          <article>
            <label>成功率</label>
            <strong>{{ (activeJob.summary.success_rate * 100).toFixed(2) }}%</strong>
          </article>
          <article v-for="row in scoreRows" :key="row.name">
            <label>{{ row.name }}</label>
            <strong>{{ row.value.toFixed(2) }}</strong>
          </article>
        </div>
        <v-chart class="chart" :option="avgScoreOption" autoresize />
        <v-chart class="chart" :option="rootCausePieOption" autoresize />
      </el-card>
    </div>
  </section>
</template>

<style scoped>
.card-block {
  border-radius: 14px;
}

.dataset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.sample-datasets {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.sample-link {
  text-decoration: none;
}

.batch-layout {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.batch-layout > * {
  min-width: 0;
}

.progress-area {
  padding: 12px 0;
  text-align: center;
}

.progress-label {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 13px;
}

.progress-placeholder {
  text-align: center;
  padding: 24px 0;
}

.text-muted {
  color: #94a3b8;
  font-size: 13px;
}

.load-error {
  margin-bottom: 12px;
}

.text-muted {
  color: #94a3b8;
  font-size: 12px;
}

.summary-kpi {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.summary-kpi article {
  border: 1px solid #d8e4f5;
  border-radius: 10px;
  background: #f8fbff;
  padding: 10px;
}

.summary-kpi label {
  color: #64748b;
  display: block;
}

.summary-kpi strong {
  font-size: 20px;
  color: #0f766e;
}

.chart {
  height: 260px;
  margin-top: 8px;
}

@media (max-width: 1200px) {
  .batch-layout,
  .summary-kpi {
    grid-template-columns: 1fr;
  }
}
</style>
