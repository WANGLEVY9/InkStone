<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import type { UploadRequestOptions } from "element-plus";

import { getOfflineJob, listOfflineJobs, OfflineEvalJob, submitOfflineEval } from "../api/modeEval";

const sampleTrace = {
  session_id: "s_demo_001",
  task: "查询订单并退款",
  steps: [
    {
      step: 1,
      thought: "先查询订单状态",
      action: { tool: "query_order", params: { order_id: "A001" } },
      result: "订单状态：已发货",
      duration: 1.2,
    },
    {
      step: 2,
      thought: "判断是否可退款",
      action: { tool: "refund_policy", params: { order_status: "shipped" } },
      result: "规则：已发货不可退款",
      duration: 1.4,
    },
  ],
  final_result: "无法退款",
  success: false,
  expected_result: "无法退款",
};

const traceText = ref(JSON.stringify(sampleTrace, null, 2));
const traceInputMode = ref<"text" | "file">("text");
const uploadedTraceRaw = ref("");
const uploadedTraceName = ref("");
const uploadedTraceSize = ref(0);
const jobs = ref<OfflineEvalJob[]>([]);
const activeJobId = ref("");
const activeJob = ref<OfflineEvalJob | null>(null);
const submitting = ref(false);
const fileUploading = ref(false);
const loading = ref(false);
const loadError = ref("");
let pollTimer: ReturnType<typeof setInterval> | null = null;

const loadJobs = async () => {
  try {
    const data = await listOfflineJobs();
    jobs.value = data.items;
    if (!activeJobId.value && jobs.value.length) {
      activeJobId.value = jobs.value[0].job_id;
    }
    loadError.value = "";
  } catch {
    loadError.value = "任务列表加载失败";
  }
};

const loadActiveJob = async () => {
  if (!activeJobId.value) {
    activeJob.value = null;
    return;
  }
  try {
    activeJob.value = await getOfflineJob(activeJobId.value);
    loadError.value = "";
  } catch {
    loadError.value = "任务详情加载失败";
  }
};

const refreshAll = async () => {
  loading.value = true;
  try {
    await loadJobs();
    await loadActiveJob();
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await refreshAll();
  pollTimer = setInterval(() => {
    void refreshAll();
  }, 3000);
});

onBeforeUnmount(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
});

const submitTrace = async () => {
  const rawTrace = traceInputMode.value === "file" ? uploadedTraceRaw.value : traceText.value;
  if (!rawTrace.trim()) {
    ElMessage.warning("请先输入或上传 Trace JSON");
    return;
  }

  submitting.value = true;
  try {
    const trace = JSON.parse(rawTrace);
    if (!trace || typeof trace !== "object" || Array.isArray(trace)) {
      ElMessage.warning("Trace JSON 顶层需为对象格式");
      return;
    }
    const job = await submitOfflineEval(trace);
    activeJobId.value = job.job_id;
    ElMessage.success("离线评估任务已提交");
    await refreshAll();
  } catch (error) {
    ElMessage.error("提交失败，请检查 Trace JSON 格式");
    console.error(error);
  } finally {
    submitting.value = false;
  }
};

const fillSample = () => {
  traceInputMode.value = "text";
  traceText.value = JSON.stringify(sampleTrace, null, 2);
};

const clearUploadedTrace = () => {
  uploadedTraceRaw.value = "";
  uploadedTraceName.value = "";
  uploadedTraceSize.value = 0;
};

const onUploadTraceFile = async (options: UploadRequestOptions) => {
  fileUploading.value = true;
  try {
    const file = options.file as File;
    const raw = await file.text();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("invalid-trace-root");
    }

    uploadedTraceRaw.value = raw;
    uploadedTraceName.value = file.name;
    uploadedTraceSize.value = file.size;
    traceInputMode.value = "file";
    ElMessage.success("Trace 文件已加载，可直接提交离线评估");
    options.onSuccess?.({});
  } catch (error) {
    ElMessage.error("上传失败，请确认文件内容为有效 JSON 对象");
    options.onError?.(error as any);
  } finally {
    fileUploading.value = false;
  }
};

const formatSize = (size: number) => {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
};

const statusTagType = (status: string) => {
  if (status === "completed") return "success";
  if (status === "running") return "warning";
  if (status === "failed") return "danger";
  return "info";
};

const reportScores = computed(() => {
  const scores = activeJob.value?.report?.scores ?? {};
  return Object.entries(scores).map(([name, value]) => ({ name, value: Number(value) }));
});

const scoreBarOption = computed(() => ({
  tooltip: { trigger: "axis" },
  xAxis: {
    type: "category",
    data: reportScores.value.map((item) => item.name),
    axisLabel: { interval: 0, rotate: 20 },
  },
  yAxis: { type: "value", max: 100 },
  series: [
    {
      type: "bar",
      data: reportScores.value.map((item) => item.value),
      itemStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "#1f8a70" },
            { offset: 1, color: "#86d3c0" },
          ],
        },
      },
      label: { show: true, position: "top" },
    },
  ],
}));

const radarScores = computed(() => {
  const scores = activeJob.value?.report?.scores ?? {};
  const subDims = ["plan", "tool", "hallucination", "memory", "efficiency"];
  if (scores.tool_relevance !== undefined) subDims.push("tool_relevance");
  if (scores.context_consistency !== undefined) subDims.push("context_consistency");
  return subDims.filter((k) => scores[k] !== undefined);
});

const scoreRadarOption = computed(() => {
  const dims = radarScores.value;
  const scores = activeJob.value?.report?.scores ?? {};
  return {
    tooltip: {},
    radar: {
      indicator: dims.map((name) => ({ name, max: 100 })),
      shape: "polygon",
      splitNumber: 4,
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: dims.map((name) => Number(scores[name] ?? 0)),
            name: activeJob.value?.report?.session_id || "当前评估",
            areaStyle: { color: "rgba(31,138,112,0.25)" },
            lineStyle: { color: "#1f8a70", width: 2 },
            itemStyle: { color: "#0f766e" },
          },
        ],
      },
    ],
  };
});
</script>

<template>
  <section class="panel card-rise" v-loading="loading">
    <div class="panel-head">
      <div>
        <h2>模式2：轨迹采集 + 离线统一评估</h2>
        <p>上传标准 Trace，异步生成多维度评估报告（能力评分 + 根因 + 建议）</p>
      </div>
      <div class="actions">
        <el-button @click="fillSample">填充示例</el-button>
        <el-button @click="refreshAll">刷新</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" :title="loadError" type="error" show-icon :closable="true" class="load-error" @close="loadError = ''" />

    <div class="offline-layout">
      <el-card shadow="never" class="card-block">
        <template #header>Trace JSON 输入</template>
        <div class="trace-toolbar">
          <el-radio-group v-model="traceInputMode" size="small">
            <el-radio-button label="text">文本输入</el-radio-button>
            <el-radio-button label="file">本地文件</el-radio-button>
          </el-radio-group>

          <el-upload
            :show-file-list="false"
            :http-request="onUploadTraceFile"
            accept=".json,application/json"
          >
            <el-button plain :loading="fileUploading">上传 Trace 文件</el-button>
          </el-upload>
        </div>

        <el-input v-if="traceInputMode === 'text'" v-model="traceText" type="textarea" :rows="20" class="trace-editor" />

        <div v-else class="trace-file-panel">
          <el-alert
            v-if="uploadedTraceName"
            type="success"
            :closable="false"
            show-icon
            :title="`已加载文件：${uploadedTraceName}`"
          >
            <template #default>
              文件大小：{{ formatSize(uploadedTraceSize) }}。点击“提交离线评估”即可执行。
            </template>
          </el-alert>
          <el-empty v-else description="尚未上传 Trace 文件" />
          <div class="file-actions" v-if="uploadedTraceName">
            <el-button size="small" @click="clearUploadedTrace">清除文件</el-button>
          </div>
        </div>

        <div class="actions-row">
          <el-button type="primary" :loading="submitting" @click="submitTrace">提交离线评估</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="card-block">
        <template #header>离线任务队列</template>
        <el-table :data="jobs" size="small" height="260" v-if="jobs.length > 0">
          <el-table-column prop="job_id" label="Job ID" min-width="180" />
          <el-table-column label="状态" width="110">
            <template #default="scope">
              <el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" link type="primary" @click="activeJobId = scope.row.job_id; loadActiveJob()">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无离线任务，请上传 Trace 并提交" />

        <div v-if="activeJob?.report" class="report-panel">
          <h3>评估报告：{{ activeJob.report.session_id }}</h3>
          <p>
            任务：{{ activeJob.report.task }}
            <el-tag :type="activeJob.report.success ? 'success' : 'danger'" size="small">{{ activeJob.report.success ? "成功" : "失败" }}</el-tag>
          </p>
          <p>根因分类：<strong>{{ activeJob.report.root_cause }}</strong></p>
          <div class="chart-row">
            <v-chart class="chart" :option="scoreBarOption" autoresize />
            <v-chart class="chart" :option="scoreRadarOption" autoresize />
          </div>
          <div class="recommendations">
            <h4>优化建议</h4>
            <ul>
              <li v-for="(item, idx) in activeJob.report.recommendations" :key="idx">{{ item }}</li>
            </ul>
          </div>
        </div>
      </el-card>
    </div>
  </section>
</template>

<style scoped>
.offline-layout {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 14px;
}

.offline-layout > * {
  min-width: 0;
}

.card-block {
  border-radius: 14px;
}

.trace-editor :deep(textarea) {
  font-family: Consolas, "Courier New", monospace;
  line-height: 1.45;
}

.trace-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.trace-file-panel {
  min-height: 360px;
  border: 1px dashed #c7d7ee;
  border-radius: 10px;
  padding: 12px;
  background: #fbfdff;
}

.file-actions {
  margin-top: 10px;
}

.actions-row {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.report-panel {
  margin-top: 12px;
  border-top: 1px dashed #c7d7ee;
  padding-top: 10px;
}

.report-panel h3 {
  margin: 0 0 8px;
}

.chart {
  height: 280px;
  margin: 8px 0;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.recommendations ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

.load-error {
  margin-bottom: 12px;
}

@media (max-width: 1280px) {
  .offline-layout {
    grid-template-columns: 1fr;
  }

  .actions-row {
    justify-content: flex-start;
  }

  .trace-file-panel {
    min-height: 240px;
  }
}
</style>
