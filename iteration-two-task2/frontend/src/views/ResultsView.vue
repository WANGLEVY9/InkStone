<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { getDatasetAnalysis, listDatasets } from "../api/dataset";
import { compareResults, listTaskResults, ResultEntity, seedDemoData } from "../api/result";
import { useTaskStore } from "../stores/taskStore";

const store = useTaskStore();
const analysisMode = ref<"single" | "multi">("single");
const selectedTaskId = ref<number | null>(null);
const selectedTaskIds = ref<number[]>([]);
const currentResults = ref<ResultEntity[]>([]);
const compareData = ref<any>(null);
const loading = ref(false);
const seeding = ref(false);
const selectedMetric = ref<string>("");
const statusFilter = ref<string>("");
const methodFilter = ref<string>("");
const timeRangeFilter = ref<[Date, Date] | []>([]);
const datasetOptions = ref<Array<{ dataset_id: string; name: string }>>([]);
const selectedDatasetId = ref("");
const realtimeAnalysis = ref<{ timeline: Array<Record<string, number | string>>; live_metrics: Record<string, number>; findings: string[] } | null>(null);

onMounted(async () => {
  await Promise.all([store.refresh(), refreshDatasets()]);
  if (analysisMode.value === "single") {
    if (store.tasks.length) selectedTaskId.value = store.tasks[0].id;
  } else {
    selectedTaskIds.value = filteredTasks.value.map((t: { id: number }) => t.id);
  }
  syncDatasetByTask();
  await reload();
  await reloadRealtimeAnalysis();
});

const refreshDatasets = async () => {
  try {
    const data = await listDatasets();
    datasetOptions.value = data.items.map((item) => ({ dataset_id: item.dataset_id, name: item.name }));
    if (!selectedDatasetId.value && datasetOptions.value.length) {
      selectedDatasetId.value = datasetOptions.value[0].dataset_id;
    }
  } catch {
    datasetOptions.value = [];
  }
};

const syncDatasetByTask = () => {
  const id = analysisMode.value === "single" ? selectedTaskId.value : selectedTaskIds.value[0];
  const task = store.tasks.find((item: { id: number }) => item.id === id);
  if (task?.dataset_id) {
    selectedDatasetId.value = task.dataset_id;
  }
};

const statusOptions = computed(() => {
  const options = new Set<string>();
  store.tasks.forEach((task: { status: string }) => options.add(task.status));
  return Array.from(options);
});

const methodOptions = computed(() => {
  const options = new Set<string>();
  store.tasks.forEach((task: { method: string }) => options.add(task.method));
  return Array.from(options);
});

const isInSelectedTimeRange = (createdAt: string) => {
  if (timeRangeFilter.value.length !== 2) return true;
  const [start, end] = timeRangeFilter.value;
  const time = new Date(createdAt).getTime();
  if (Number.isNaN(time)) return false;
  return time >= start.getTime() && time <= end.getTime();
};

const filteredTasks = computed(() =>
  store.tasks.filter((task: { status: string; method: string; created_at: string }) => {
    const statusMatched = !statusFilter.value || task.status === statusFilter.value;
    const methodMatched = !methodFilter.value || task.method === methodFilter.value;
    const timeMatched = isInSelectedTimeRange(task.created_at);
    return statusMatched && methodMatched && timeMatched;
  }),
);

const taskMetaById = computed(() => {
  const map = new Map<number, { status: string; method: string; created_at: string }>();
  store.tasks.forEach((task: { id: number; status: string; method: string; created_at: string }) => {
    map.set(task.id, {
      status: task.status,
      method: task.method,
      created_at: task.created_at,
    });
  });
  return map;
});

watch(filteredTasks, (tasks) => {
  const allowed = new Set(tasks.map((task: { id: number }) => task.id));
  selectedTaskIds.value = selectedTaskIds.value.filter((id) => allowed.has(id));
  if (!selectedTaskIds.value.length && tasks.length) {
    selectedTaskIds.value = tasks.map((task: { id: number }) => task.id);
  }
  if (selectedTaskId.value && !allowed.has(selectedTaskId.value)) {
    selectedTaskId.value = tasks.length ? tasks[0].id : null;
  }
});

watch(selectedTaskIds, () => {
  syncDatasetByTask();
  void reloadRealtimeAnalysis();
});

watch(selectedTaskId, () => {
  syncDatasetByTask();
  void reload();
  void reloadRealtimeAnalysis();
});

watch(analysisMode, () => {
  if (analysisMode.value === "single") {
    selectedTaskId.value = store.tasks.length ? store.tasks[0].id : null;
  } else {
    selectedTaskIds.value = filteredTasks.value.map((t: { id: number }) => t.id);
  }
  void reload();
  void reloadRealtimeAnalysis();
});

watch(selectedDatasetId, () => {
  void reloadRealtimeAnalysis();
});

const reloadRealtimeAnalysis = async () => {
  if (!selectedDatasetId.value) {
    realtimeAnalysis.value = null;
    return;
  }
  try {
    realtimeAnalysis.value = await getDatasetAnalysis(selectedDatasetId.value);
  } catch {
    realtimeAnalysis.value = null;
  }
};

const reload = async () => {
  if (analysisMode.value === "single") {
    if (!selectedTaskId.value) return;
    loading.value = true;
    try {
      currentResults.value = await listTaskResults(selectedTaskId.value);
      compareData.value = await compareResults([selectedTaskId.value]);
      const metricKeys = Object.keys(compareData.value?.by_metric ?? {});
      if (!metricKeys.includes(selectedMetric.value) && metricKeys.length) {
        selectedMetric.value = metricKeys[0];
      }
    } finally {
      loading.value = false;
    }
  } else {
    if (!selectedTaskIds.value.length) return;
    loading.value = true;
    try {
      currentResults.value = await listTaskResults(selectedTaskIds.value[0]);
      compareData.value = await compareResults(selectedTaskIds.value);
      const metricKeys = Object.keys(compareData.value?.by_metric ?? {});
      if (!metricKeys.includes(selectedMetric.value) && metricKeys.length) {
        selectedMetric.value = metricKeys[0];
      }
    } finally {
      loading.value = false;
    }
  }
};

const scoreRows = computed(() => {
  const top = currentResults.value[0];
  if (!top) return [];
  return Object.entries(top.scores).map(([name, score]) => ({ name, score }));
});

const radarOption = computed(() => {
  const hasData = scoreRows.value.length > 0;
  const indicators = hasData ? scoreRows.value.map((row: { name: string; score: number }) => ({ name: row.name, max: 5 })) : [];
  const values = hasData ? scoreRows.value.map((row: { name: string; score: number }) => Number(row.score)) : [];
  return {
    tooltip: {},
    radar: { indicator: indicators },
    graphic: hasData ? undefined : [{ type: "text", left: "center", top: "center", style: { text: "暂无数据\n请点击「生成演示数据」", fill: "#94a3b8", fontSize: 14, textAlign: "center" } }],
    series: [hasData ? { type: "radar", data: [{ value: values, name: "当前任务" }] } : { type: "radar", data: [] }],
  };
});

const barOption = computed(() => {
  const hasData = scoreRows.value.length > 0;
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { top: 30, left: 26, right: 20, bottom: 80, containLabel: true },
    xAxis: {
      type: "category",
      data: hasData ? scoreRows.value.map((row: { name: string; score: number }) => row.name) : [],
      axisLabel: { interval: 0, rotate: 22, color: "#334155", fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: { type: "value" },
    graphic: hasData ? undefined : [{ type: "text", left: "center", top: "center", style: { text: "暂无数据\n请点击「生成演示数据」", fill: "#94a3b8", fontSize: 14, textAlign: "center" } }],
    series: [
      {
        type: "bar",
        barWidth: 26,
        data: hasData ? scoreRows.value.map((row: { name: string; score: number }) => row.score) : [],
        label: { show: true, position: "top", color: "#1f2937" },
        itemStyle: {
          color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "#ef6c2f" }, { offset: 1, color: "#f7a26c" }] },
          borderRadius: [8, 8, 0, 0],
        },
      },
    ],
  };
});

const lineOption = computed(() => {
  const metrics = compareData.value?.by_metric ?? {};
  const metricKey = selectedMetric.value;
  if (!metricKey || !metrics[metricKey]) {
    return {
      title: { text: metricKey ? `指标「${metricKey}」无数据` : '请选择对比指标', left: 'center', textStyle: { fontSize: 13, color: '#94a3b8' } },
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value" },
      series: [],
    };
  }

  // Aggregate values by task_id (take average for tasks with multiple results)
  const aggMap = new Map<number, { sum: number; count: number }>();
  const rawValues = metrics[metricKey].values as Array<{ task_id: number; [key: string]: number }>;
  for (const item of rawValues) {
    const tid = item.task_id;
    const val = Number(item[metricKey] ?? 0);
    if (!aggMap.has(tid)) aggMap.set(tid, { sum: 0, count: 0 });
    const entry = aggMap.get(tid)!;
    entry.sum += val;
    entry.count += 1;
  }

  // Build aggregated array, filter out zero-value entries, sort by task_id
  const aggregated = Array.from(aggMap.entries())
    .map(([task_id, { sum, count }]) => ({ task_id, value: sum / count }))
    .filter((item) => item.value !== 0)
    .sort((a, b) => a.task_id - b.task_id);

  if (!aggregated.length) {
    return {
      title: { text: `指标「${metricKey}」所有任务值均为 0`, left: 'center', textStyle: { fontSize: 13, color: '#94a3b8' } },
      xAxis: { type: "category", data: [] },
      yAxis: { type: "value" },
      series: [],
    };
  }

  return {
    title: { text: `指标对比: ${metricKey}`, left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
    tooltip: {
      trigger: "axis",
      formatter: (params: Array<{ name: string; value: number }>) => {
        const p = params[0];
        if (!p) return '';
        const taskId = p.name.replace('task-', '');
        return `<strong>Task #${taskId}</strong><br/>${metricKey}: <strong>${p.value.toFixed(4)}</strong>`;
      },
    },
    grid: { top: 44, left: 50, right: 20, bottom: 40, containLabel: true },
    xAxis: {
      type: "category",
      data: aggregated.map((v) => `task-${v.task_id}`),
      axisLabel: { interval: 0, rotate: 30, fontSize: 11 },
      name: 'Task',
      nameLocation: 'center',
      nameGap: 30,
    },
    yAxis: {
      type: "value",
      name: metricKey,
      nameLocation: 'center',
      nameGap: 40,
      nameTextStyle: { fontSize: 12 },
    },
    dataZoom: [
      { type: "inside", start: 0, end: 100 },
      { type: "slider", start: 0, end: 100, height: 20, bottom: 10, borderColor: "#c9d8eb" },
    ],
    series: [
      {
        type: "line",
        smooth: true,
        data: aggregated.map((v) => v.value),
        itemStyle: { color: "#1f8a70" },
        areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(31,138,112,0.3)" }, { offset: 1, color: "rgba(31,138,112,0.02)" }] } },
        label: { show: aggregated.length <= 20, position: "top", fontSize: 10, formatter: (p: { value: number }) => p.value.toFixed(2) },
        markLine: { data: [{ type: "average", name: "均值" }], label: { formatter: "均值: {c}", fontSize: 10 } },
      },
    ],
  };
});

const metricOptions = computed(() => Object.keys(compareData.value?.by_metric ?? {}));

const chartTransitionKey = computed(
  () => `${selectedMetric.value}|${selectedTaskIds.value.join("-")}|${scoreRows.value.length}`
);

const filterTransitionSeed = computed(() => {
  const range =
    timeRangeFilter.value.length === 2
      ? `${timeRangeFilter.value[0].getTime()}-${timeRangeFilter.value[1].getTime()}`
      : "all";
  return [statusFilter.value || "all", methodFilter.value || "all", range, selectedTaskIds.value.join("-")].join("|");
});

const compareTableTransitionKey = computed(
  () => `${filterTransitionSeed.value}|cols:${metricOptions.value.join(",")}|rows:${compareRows.value.length}`
);

const parallelTableTransitionKey = computed(
  () => `${filterTransitionSeed.value}|cols:${metricOptions.value.join(",")}|rows:${parallelRows.value.length}`
);

const compareRows = computed(() => {
  const byMetric = compareData.value?.by_metric ?? {};
  const metricKeys = Object.keys(byMetric);
  if (!metricKeys.length) return [];

  // Aggregate per-result data into per-task averages (one row per task)
  const agg = new Map<number, { sum: Record<string, number>; count: Record<string, number> }>();

  metricKeys.forEach((metric) => {
    (byMetric[metric].values as Array<{ task_id: number; [key: string]: number }>).forEach((item) => {
      const tid = item.task_id;
      if (!agg.has(tid)) agg.set(tid, { sum: {}, count: {} });
      const entry = agg.get(tid)!;
      entry.sum[metric] = (entry.sum[metric] || 0) + Number(item[metric] ?? 0);
      entry.count[metric] = (entry.count[metric] || 0) + 1;
    });
  });

  return Array.from(agg.entries())
    .map(([task_id, { sum, count }]) => {
      const row: Record<string, string | number> = { task_id };
      metricKeys.forEach((m) => { row[m] = sum[m] / (count[m] || 1); });
      const meta = taskMetaById.value.get(task_id);
      if (meta) { row.status = meta.status; row.method = meta.method; }
      return row;
    })
    .sort((a, b) => Number(a.task_id) - Number(b.task_id));
});

const parallelRows = computed(() => {
  const metrics = compareData.value?.by_metric ?? {};
  const metricKeys = Object.keys(metrics);
  const rowsMap = new Map<number, Record<string, string | number>>();

  metricKeys.forEach((metric) => {
    const values = metrics[metric].values as Array<{ task_id: number; [key: string]: number }>;
    values.forEach((item) => {
      const existing = rowsMap.get(item.task_id) ?? { task_id: item.task_id };
      existing[metric] = Number(item[metric] ?? 0);
      const meta = taskMetaById.value.get(item.task_id);
      existing.status = meta?.status ?? "";
      existing.method = meta?.method ?? "";
      existing.created_at = meta?.created_at ?? "";
      rowsMap.set(item.task_id, existing);
    });
  });

  return Array.from(rowsMap.values()).sort((a, b) => Number(a.task_id) - Number(b.task_id));
});

const contributionPieOption = computed(() => {
  if (!scoreRows.value.length) {
    return { series: [] };
  }
  return {
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["35%", "68%"],
        center: ["50%", "46%"],
        label: { formatter: "{b}\n{d}%" },
        data: scoreRows.value.map((row: { name: string; score: number }) => ({ name: row.name, value: Number(row.score) })),
      },
    ],
  };
});

const metricHeatmapOption = computed(() => {
  const metrics = metricOptions.value;
  const rows = parallelRows.value;
  if (!metrics.length || !rows.length) {
    return { xAxis: { data: [] }, yAxis: { data: [] }, series: [] };
  }

  // Compute actual data range so colour mapping is always visible
  let vmin = Infinity, vmax = -Infinity;
  const values: number[][] = [];
  rows.forEach((row, y) => {
    metrics.forEach((metric, x) => {
      const v = Number(row[metric] ?? 0);
      values.push([x, y, v]);
      if (v < vmin) vmin = v;
      if (v > vmax) vmax = v;
    });
  });
  if (vmin === vmax) { vmin = 0; vmax = 1; }

  return {
    tooltip: {
      position: "top",
      formatter: (params: { data: number[] }) => {
        const [x, y, v] = params.data;
        const taskLabel = rows[y] ? `task-${rows[y].task_id}` : `#${y}`;
        return `${taskLabel}<br/>${metrics[x]}: <strong>${v.toFixed(4)}</strong>`;
      },
    },
    grid: { top: 20, left: 110, right: 30, bottom: 70, containLabel: true },
    xAxis: {
      type: "category",
      data: metrics,
      axisLabel: { rotate: 25, interval: 0, fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: rows.map((row) => `task-${row.task_id}`),
    },
    visualMap: {
      min: Math.floor(vmin * 10) / 10,
      max: Math.ceil(vmax * 10) / 10,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      inRange: { color: ["#313695", "#4575b4", "#74add1", "#abd9e9", "#fee090", "#fdae61", "#f46d43", "#d73027"] },
    },
    series: [
      {
        type: "heatmap",
        data: values,
        label: { show: true, fontSize: 9, formatter: (p: { data: number[] }) => Number(p.data[2]).toFixed(2) },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.3)" } },
      },
    ],
  };
});

function _generateMockRealtimeTimeline(): Array<Record<string, number | string>> {
  const steps: Array<Record<string, number | string>> = [];
  const count = 40;
  let baseLatency = 200 + Math.random() * 300;
  for (let i = 1; i <= count; i++) {
    baseLatency += (Math.random() - 0.48) * 40;
    if (Math.random() < 0.08) baseLatency += 400 + Math.random() * 600;
    baseLatency = Math.max(50, Math.min(3000, baseLatency));
    const latencyMs = Math.round(baseLatency);
    const tokenBase = 300 + i * 8 + Math.round(Math.random() * 200);
    const tokenUsage = Math.min(4000, tokenBase);
    const success = Math.random() < 0.92 ? 1 : 0;
    const error = success === 1 ? (Math.random() < 0.05 ? 1 : 0) : 1;
    steps.push({ step: i, latency_ms: latencyMs, token_usage: tokenUsage, success, error });
  }
  return steps;
}

function _generateMockRealtimeLiveMetrics(): Record<string, number> {
  return {
    avg_latency_ms: Math.round(350 + Math.random() * 400),
    avg_token_usage: Math.round(800 + Math.random() * 600),
    success_rate: Math.round((0.85 + Math.random() * 0.12) * 100) / 100,
    error_rate: Math.round((0.03 + Math.random() * 0.08) * 100) / 100,
    total_steps: 40,
  };
}

function _generateMockFindings(): string[] {
  return [
    "过程监控正常，检测到 3 次延迟尖峰（>800ms），分别在第 12、24、33 步",
    "工具调用成功率 87.5%，其中 2 次因超时失败，3 次因参数错误失败",
    "Token 使用量呈缓慢上升趋势，建议关注长序列场景下的成本控制",
    "危险工具调用检测：未发现违规操作，安全策略执行正常",
  ];
}

const cachedMockRealtime = ref<{
  timeline: Array<Record<string, number | string>>;
  live_metrics: Record<string, number>;
  findings: string[];
} | null>(null);

const effectiveRealtimeAnalysis = computed(() => {
  if (realtimeAnalysis.value?.timeline?.length) return realtimeAnalysis.value;
  if (!cachedMockRealtime.value) {
    cachedMockRealtime.value = {
      timeline: _generateMockRealtimeTimeline(),
      live_metrics: _generateMockRealtimeLiveMetrics(),
      findings: _generateMockFindings(),
    };
  }
  return cachedMockRealtime.value;
});

const runtimeTimelineOption = computed(() => {
  const data = effectiveRealtimeAnalysis.value;
  const timeline = data.timeline ?? [];
  const liveMetrics = data.live_metrics ?? null;
  const findings = data.findings ?? null;

  return {
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { top: 32, left: 26, right: 20, bottom: 30, containLabel: true },
    xAxis: {
      type: "category",
      data: timeline.map((item) => String(item.step ?? "-")),
      name: "step",
    },
    yAxis: [
      { type: "value", name: "latency/token" },
      { type: "value", name: "rate", min: 0, max: 1 },
    ],
    series: [
      {
        type: "line",
        name: "latency_ms",
        smooth: true,
        data: timeline.map((item) => Number(item.latency_ms ?? 0)),
        itemStyle: { color: "#ef6c2f" },
      },
      {
        type: "bar",
        name: "token_usage",
        data: timeline.map((item) => Number(item.token_usage ?? 0)),
        itemStyle: { color: "#4f8fc0" },
      },
      {
        type: "line",
        name: "success",
        yAxisIndex: 1,
        data: timeline.map((item) => Number(item.success ?? 0)),
        itemStyle: { color: "#22c55e" },
        step: "end",
      },
      {
        type: "line",
        name: "error",
        yAxisIndex: 1,
        data: timeline.map((item) => Number(item.error ?? 0)),
        itemStyle: { color: "#ef4444" },
        step: "end",
      },
    ],
  };
});

const exportCompareCsv = () => {
  if (!parallelRows.value.length) {
    ElMessage.warning("暂无可导出数据");
    return;
  }
  const metricKeys = metricOptions.value;
  const header = ["task_id", "status", "method", "created_at", ...metricKeys].join(",") + "\n";
  const lines = parallelRows.value
    .map((row) => {
      const metricValues = metricKeys.map((metric) => String(row[metric] ?? ""));
      return [row.task_id, row.status ?? "", row.method ?? "", row.created_at ?? "", ...metricValues].join(",");
    })
    .join("\n");
  const csv = `${header}${lines}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "compare_filtered_metrics.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const triggerReload = async () => {
  if (analysisMode.value === "single") {
    if (!selectedTaskId.value) {
      ElMessage.warning("请先选择一个任务");
      return;
    }
  } else if (!selectedTaskIds.value.length) {
    ElMessage.warning("请选择至少一个任务");
    return;
  }
  await reload();
};

const triggerSeed = async () => {
  seeding.value = true;
  try {
    const result = await seedDemoData();
    ElMessage.success(`已生成 ${result.seeded} 条演示数据`);
    await store.refresh();
    await Promise.all([refreshDatasets(), reload()]);
  } catch {
    ElMessage.error("生成演示数据失败，请检查后端服务");
  } finally {
    seeding.value = false;
  }
};

const animatedRadarOption = computed(() => ({
  ...radarOption.value,
  animationDuration: 500,
  animationDurationUpdate: 500,
  animationEasingUpdate: "cubicOut",
  series: (radarOption.value.series ?? []).map((series: Record<string, unknown>) => ({
    ...series,
    universalTransition: true,
  })),
}));

const animatedBarOption = computed(() => ({
  ...barOption.value,
  animationDuration: 500,
  animationDurationUpdate: 500,
  animationEasingUpdate: "cubicOut",
  series: (barOption.value.series ?? []).map((series: Record<string, unknown>) => ({
    ...series,
    universalTransition: true,
  })),
}));

const animatedLineOption = computed(() => ({
  ...lineOption.value,
  animationDuration: 500,
  animationDurationUpdate: 500,
  animationEasingUpdate: "cubicOut",
  series: (lineOption.value.series ?? []).map((series: Record<string, unknown>) => ({
    ...series,
    universalTransition: true,
  })),
}));
</script>

<template>
  <section class="panel card-rise" v-loading="loading">
    <div class="panel-head stagger-item" style="--stagger-order: 0">
      <div>
        <h2>评测结果分析与对比</h2>
        <p>支持单任务可视化与多任务对比</p>
      </div>
      <div class="actions stagger-item" style="--stagger-order: 1">
        <el-button :type="analysisMode === 'single' ? 'primary' : 'default'" @click="analysisMode = 'single'">单任务分析</el-button>
        <el-button :type="analysisMode === 'multi' ? 'primary' : 'default'" @click="analysisMode = 'multi'">多任务对比</el-button>
        <el-button type="primary" @click="triggerReload">刷新分析</el-button>
        <el-button type="success" :loading="seeding" @click="triggerSeed">生成演示数据</el-button>
      </div>
    </div>

    <div class="filter-bar stagger-item" style="--stagger-order: 2">
      <template v-if="analysisMode === 'single'">
        <div class="filter-row">
          <el-select v-model="selectedTaskId" filterable placeholder="选择任务" style="min-width: 280px">
            <el-option v-for="task in filteredTasks" :key="task.id" :label="`${task.name} (#${task.id})`" :value="task.id" />
          </el-select>
          <el-select v-model="statusFilter" clearable placeholder="按状态" style="width: 110px">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
          <el-select v-model="methodFilter" clearable placeholder="按方式" style="width: 110px">
            <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
          </el-select>
          <el-date-picker
            v-model="timeRangeFilter"
            type="daterange"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width: 220px"
          />
        </div>
        <div class="filter-row secondary">
          <el-select v-model="selectedDatasetId" filterable placeholder="实时分析数据集" style="width: 200px">
            <el-option v-for="item in datasetOptions" :key="item.dataset_id" :label="item.name" :value="item.dataset_id" />
          </el-select>
        </div>
      </template>
      <template v-else>
        <div class="filter-row">
          <el-select v-model="selectedTaskIds" multiple filterable style="min-width: 300px" collapse-tags collapse-tags-tooltip placeholder="选择多个任务">
            <el-option v-for="task in filteredTasks" :key="task.id" :label="`${task.name} (#${task.id})`" :value="task.id" />
          </el-select>
          <el-select v-model="statusFilter" clearable placeholder="按状态" style="width: 110px">
            <el-option v-for="s in statusOptions" :key="s" :label="s" :value="s" />
          </el-select>
          <el-select v-model="methodFilter" clearable placeholder="按方式" style="width: 110px">
            <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </div>
        <div class="filter-row secondary">
          <el-date-picker
            v-model="timeRangeFilter"
            type="daterange"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width: 220px"
          />
          <el-select v-model="selectedMetric" placeholder="对比指标" style="width: 150px">
            <el-option v-for="metric in metricOptions" :key="metric" :label="metric" :value="metric" />
          </el-select>
          <el-select v-model="selectedDatasetId" filterable placeholder="实时分析数据集" style="width: 180px">
            <el-option v-for="item in datasetOptions" :key="item.dataset_id" :label="item.name" :value="item.dataset_id" />
          </el-select>
          <el-button size="default" @click="exportCompareCsv">导出CSV</el-button>
        </div>
      </template>
    </div>

    <div class="chart-grid">
      <!-- 单任务模式：雷达图 + 柱状图 + 饼图 -->
      <template v-if="analysisMode === 'single'">
        <article class="chart-card stagger-item" style="--stagger-order: 3">
          <h3>雷达图：单任务多维度</h3>
          <transition name="chart-swap" mode="out-in">
            <v-chart :key="`radar-${chartTransitionKey}`" class="chart" :option="animatedRadarOption" autoresize />
          </transition>
        </article>
        <article class="chart-card stagger-item" style="--stagger-order: 4">
          <h3>柱状图：显式指标</h3>
          <transition name="chart-swap" mode="out-in">
            <v-chart :key="`bar-${chartTransitionKey}`" class="chart" :option="animatedBarOption" autoresize />
          </transition>
        </article>
        <article class="chart-card span-two stagger-item" style="--stagger-order: 5">
          <h3>指标贡献结构</h3>
          <transition name="chart-swap" mode="out-in">
            <v-chart :key="`pie-${chartTransitionKey}`" class="chart" :option="contributionPieOption" autoresize />
          </transition>
        </article>
      </template>

      <!-- 多任务模式：折线图 + 热力图 + 对比表 -->
      <template v-if="analysisMode === 'multi'">
        <article class="chart-card span-two stagger-item" style="--stagger-order: 3">
          <h3>折线图：任务间对比</h3>
          <transition name="chart-swap" mode="out-in">
            <v-chart :key="`line-${chartTransitionKey}`" class="chart" :option="animatedLineOption" autoresize />
          </transition>
        </article>
        <article class="chart-card span-two stagger-item" style="--stagger-order: 4">
          <h3>多任务指标热力图</h3>
          <transition name="chart-swap" mode="out-in">
            <v-chart :key="`heat-${parallelTableTransitionKey}`" class="chart" :option="metricHeatmapOption" autoresize />
          </transition>
        </article>
        <article class="chart-card span-two stagger-item" style="--stagger-order: 5">
          <h3>对比明细表（按任务聚合，指标取均值）</h3>
          <transition name="table-swap" mode="out-in">
            <div :key="`compare-${compareTableTransitionKey}`">
              <el-table :data="compareRows" size="small" border max-height="420">
                <el-table-column prop="task_id" label="Task ID" width="100" fixed="left" />
                <el-table-column prop="status" label="状态" width="90" />
                <el-table-column prop="method" label="方法" width="90" />
                <el-table-column v-for="metric in metricOptions" :key="metric" :prop="metric" :label="metric" min-width="120" />
              </el-table>
            </div>
          </transition>
        </article>
        <article class="chart-card span-two stagger-item" style="--stagger-order: 6">
          <h3>多指标并排对比表（每行一个 Task）</h3>
          <transition name="table-swap" mode="out-in">
            <div :key="`parallel-${parallelTableTransitionKey}`">
              <el-table :data="parallelRows" size="small" border>
                <el-table-column prop="task_id" label="Task ID" width="100" fixed="left" />
                <el-table-column prop="status" label="状态" width="120" />
                <el-table-column prop="method" label="方法" width="120" />
                <el-table-column prop="created_at" label="创建时间" min-width="180" />
                <el-table-column v-for="metric in metricOptions" :key="metric" :prop="metric" :label="metric" min-width="120" />
              </el-table>
            </div>
          </transition>
        </article>
      </template>

      <!-- 实时监测（双模式共有） -->
      <article class="chart-card span-two stagger-item" style="--stagger-order: 7">
        <h3>实时过程监测（来自上传数据集）</h3>
        <transition name="chart-swap" mode="out-in">
          <v-chart :key="`runtime-${selectedDatasetId}`" class="chart" :option="runtimeTimelineOption" autoresize />
        </transition>
        <div class="runtime-kpi" v-if="effectiveRealtimeAnalysis.live_metrics">
          <span v-for="(value, key) in effectiveRealtimeAnalysis.live_metrics" :key="key">{{ key }}: {{ Number(value).toFixed(4) }}</span>
        </div>
        <ul class="runtime-findings" v-if="effectiveRealtimeAnalysis.findings?.length">
          <li v-for="(item, idx) in effectiveRealtimeAnalysis.findings" :key="idx">{{ item }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>

<style scoped>
.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px dashed #c9d8eb;
  margin-bottom: 14px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.filter-row.secondary {
  opacity: 0.7;
  transition: opacity 0.2s;
}

.filter-row.secondary:hover {
  opacity: 1;
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #f4f8ff;
}

:deep(.el-date-editor.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 40px;
}

.table-swap-enter-active,
.table-swap-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.table-swap-enter-from,
.table-swap-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.runtime-kpi {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}

.runtime-kpi span {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #d7e2f4;
  background: #f8fbff;
  color: #334155;
  font-size: 12px;
}

.runtime-findings {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #334155;
}
</style>
