<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import TaskModeLaunchDialog, { type LaunchMode } from "../components/TaskModeLaunchDialog.vue";
import RealtimeModeView from "./RealtimeModeView.vue";
import OfflineTraceModeView from "./OfflineTraceModeView.vue";
import DatasetBatchModeView from "./DatasetBatchModeView.vue";
import type { TaskEntity } from "../api/task";
import { getLlmJudgeResult, listTaskResults, triggerLlmJudge, type LlmJudgeReport, type ResultEntity } from "../api/result";
import { useTaskWebSocket } from "../composables/useTaskWebSocket";
import { useTaskStore } from "../stores/taskStore";

const store = useTaskStore();
const launchDialogVisible = ref(false);
const modeWorkbenchVisible = ref(false);
const workspaceMode = ref<LaunchMode>("realtime");
const searchKeyword = ref("");
const statusFilter = ref("all");
const modeFilter = ref("all");
const methodFilter = ref("all");
const page = ref(1);
const pageSize = ref(8);
const autoRefresh = ref(false);
const isNarrowScreen = ref(false);
const firstLoadRowAnimation = ref(true);
let refreshTimer: ReturnType<typeof setInterval> | null = null;
const taskWs = useTaskWebSocket();
const updateViewport = () => {
  isNarrowScreen.value = window.innerWidth <= 1280;
};

const selectedTask = ref<TaskEntity | null>(null);
const taskResults = ref<ResultEntity[]>([]);
const resultsLoading = ref(false);

// LLM Judge
const llmJudgeReport = ref<LlmJudgeReport | null>(null);
const llmJudgeDialogVisible = ref(false);
const llmJudgeLoading = ref(false);
const llmJudgeTriggering = ref(false);
const llmJudgeTaskId = ref<number | null>(null);

const loadTaskResults = async (taskId: number) => {
  resultsLoading.value = true;
  try {
    taskResults.value = await listTaskResults(taskId);
  } catch {
    taskResults.value = [];
  } finally {
    resultsLoading.value = false;
  }
};

const onTaskRowClick = (row: TaskEntity) => {
  selectedTask.value = row;
  void loadTaskResults(row.id);
};

onMounted(async () => {
  updateViewport();
  window.addEventListener("resize", updateViewport);
  await store.refresh();
  if (store.tasks.length) {
    selectedTask.value = store.tasks[0];
    await loadTaskResults(store.tasks[0].id);
  }
});

const onTaskWsUpdate = (payload: { task?: Partial<TaskEntity> }) => {
  const t = payload?.task;
  if (!t || !selectedTask.value || t.id !== selectedTask.value.id) return;
  selectedTask.value = { ...selectedTask.value, ...t };
  void store.refresh();
  if (t.status === "completed" || t.status === "failed") {
    void loadTaskResults(selectedTask.value.id);
  }
};

taskWs.on("task_init", onTaskWsUpdate);
taskWs.on("task_queued", onTaskWsUpdate);
taskWs.on("task_started", onTaskWsUpdate);
taskWs.on("task_progress", onTaskWsUpdate);
taskWs.on("task_completed", onTaskWsUpdate);
taskWs.on("task_failed", onTaskWsUpdate);
taskWs.on("task_cancelled", onTaskWsUpdate);

watch(
  () => selectedTask.value?.id,
  (taskId) => {
    if (!taskId) {
      taskWs.disconnect();
      return;
    }
    taskWs.connect(taskId);
  },
  { immediate: true }
);

watch(autoRefresh, (enabled) => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  if (enabled) {
    refreshTimer = setInterval(() => {
      void store.refresh().then(() => {
        if (selectedTask.value) {
          const latest = store.tasks.find((t) => t.id === selectedTask.value!.id);
          if (latest) selectedTask.value = latest;
          if (selectedTask.value?.status === "running" || selectedTask.value?.status === "pending") {
            void loadTaskResults(selectedTask.value.id);
          }
        }
      });
    }, 5000);
  }
});

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
  window.removeEventListener("resize", updateViewport);
  taskWs.disconnect();
});

const statusTagType = (status: string) => {
  if (status === "completed") return "success";
  if (status === "running") return "warning";
  if (status === "failed") return "danger";
  return "info";
};

const openModeWorkbench = (mode: LaunchMode) => {
  workspaceMode.value = mode;
  modeWorkbenchVisible.value = true;
};

const handleLaunch = (mode: LaunchMode) => {
  openModeWorkbench(mode);
};

const runTask = async (taskId: number) => {
  await store.runTask(taskId);
  ElMessage.success("评测已触发");
  await store.refresh();
  if (selectedTask.value?.id === taskId) {
    await loadTaskResults(taskId);
  }
};

const removeTask = async (taskId: number) => {
  await ElMessageBox.confirm("确认删除该任务？", "提示", { type: "warning" });
  await store.removeTask(taskId);
  ElMessage.success("任务已删除");
};

const cancelTask = async (taskId: number) => {
  await ElMessageBox.confirm("确认取消该任务？", "提示", { type: "warning" });
  await store.cancelTask(taskId);
  ElMessage.success("任务已取消");
};

const cloneTask = async (taskId: number) => {
  await store.cloneTask(taskId);
  ElMessage.success("任务已克隆");
};

const openLlmJudgeDialog = async (taskId: number) => {
  llmJudgeTaskId.value = taskId;
  llmJudgeDialogVisible.value = true;
  llmJudgeReport.value = null;
  llmJudgeLoading.value = true;
  try {
    llmJudgeReport.value = await getLlmJudgeResult("task", taskId);
  } catch {
    llmJudgeReport.value = null;
  } finally {
    llmJudgeLoading.value = false;
  }
};

const handleTriggerLlmJudgeForTask = async (taskId: number) => {
  llmJudgeTriggering.value = true;
  try {
    await triggerLlmJudge(taskId);
    ElMessage.success("评估报告已触发");
    setTimeout(() => {
      if (llmJudgeTaskId.value === taskId) {
        llmJudgeLoading.value = true;
        getLlmJudgeResult("task", taskId).then((data) => {
          llmJudgeReport.value = data;
        }).catch(() => {}).finally(() => {
          llmJudgeLoading.value = false;
        });
      }
    }, 2000);
  } catch {
    ElMessage.error("触发评估报告失败");
  } finally {
    llmJudgeTriggering.value = false;
  }
};

const countDone = computed(() =>
  store.tasks.filter((t: { status: string }) => t.status === "completed").length
);

const countRunning = computed(() => store.tasks.filter((t) => t.status === "running").length);
const countFailed = computed(() => store.tasks.filter((t) => t.status === "failed").length);

const filteredTasks = computed(() =>
  store.tasks.filter((task) => {
    const keywordOk = !searchKeyword.value || task.name.toLowerCase().includes(searchKeyword.value.toLowerCase());
    const statusOk = statusFilter.value === "all" || task.status === statusFilter.value;
    const modeOk = modeFilter.value === "all" || task.mode === modeFilter.value;
    const methodOk = methodFilter.value === "all" || task.method === methodFilter.value;
    return keywordOk && statusOk && modeOk && methodOk;
  })
);

const pagedTasks = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return filteredTasks.value.slice(start, start + pageSize.value);
});

watch([searchKeyword, statusFilter, modeFilter, methodFilter], () => {
  page.value = 1;
});

watch(
  pagedTasks,
  (rows) => {
    if (firstLoadRowAnimation.value && rows.length) {
      setTimeout(() => {
        firstLoadRowAnimation.value = false;
      }, 900);
    }
  },
  { immediate: true }
);

const taskRowClassName = ({ rowIndex }: { rowIndex: number }) => {
  if (!firstLoadRowAnimation.value) return "";
  return `task-row-intro row-intro-${Math.min(rowIndex, 9)}`;
};

const modeWorkbenchTitle = computed(() => {
  if (workspaceMode.value === "realtime") {
    return "模式1 在线实时评估 - 初始化与观测";
  }
  if (workspaceMode.value === "offline-trace") {
    return "模式2 轨迹离线评估 - 初始化与观测";
  }
  return "模式3 数据集批量评估 - 初始化与观测";
});

const modeWorkbenchComponent = computed(() => {
  if (workspaceMode.value === "realtime") return RealtimeModeView;
  if (workspaceMode.value === "offline-trace") return OfflineTraceModeView;
  return DatasetBatchModeView;
});
</script>

<template>
  <section class="panel card-rise task-page">
    <div class="panel-head stagger-item" style="--stagger-order: 0">
      <div>
        <h2>评测任务管理</h2>
        <p>总任务 {{ store.tasks.length }}，已完成 {{ countDone }}</p>
      </div>
      <div class="actions">
        <el-switch v-model="autoRefresh" inline-prompt active-text="自动刷新" inactive-text="手动" />
        <el-button @click="store.refresh" :loading="store.loading">刷新</el-button>
        <el-button type="primary" @click="launchDialogVisible = true">新建任务</el-button>
      </div>
    </div>

    <div class="task-kpis">
      <article class="stagger-item" style="--stagger-order: 1"><strong>{{ store.tasks.length }}</strong><span>总任务</span></article>
      <article class="stagger-item" style="--stagger-order: 2"><strong>{{ countDone }}</strong><span>已完成</span></article>
      <article class="stagger-item" style="--stagger-order: 3"><strong>{{ countRunning }}</strong><span>执行中</span></article>
      <article class="stagger-item" style="--stagger-order: 4"><strong>{{ countFailed }}</strong><span>失败</span></article>
    </div>

    <div class="task-filters stagger-item" style="--stagger-order: 5">
      <el-input v-model="searchKeyword" clearable placeholder="按任务名搜索" class="filter-control filter-keyword" />
      <el-select v-model="statusFilter" class="filter-control">
        <el-option label="全部状态" value="all" />
        <el-option label="pending" value="pending" />
        <el-option label="running" value="running" />
        <el-option label="completed" value="completed" />
        <el-option label="failed" value="failed" />
      </el-select>
      <el-select v-model="modeFilter" class="filter-control">
        <el-option label="全部模式" value="all" />
        <el-option label="result" value="result" />
        <el-option label="process" value="process" />
        <el-option label="dataset-batch" value="dataset-batch" />
      </el-select>
      <el-select v-model="methodFilter" class="filter-control">
        <el-option label="全部方式" value="all" />
        <el-option label="explicit" value="explicit" />
        <el-option label="fuzzy" value="fuzzy" />
      </el-select>
    </div>

    <div class="table-shell stagger-item" style="--stagger-order: 6">
      <el-table
        class="task-main-table"
        :data="pagedTasks"
        :row-class-name="taskRowClassName"
        highlight-current-row
        stripe
        size="small"
        v-loading="store.loading"
        @row-click="onTaskRowClick"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="任务名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="agent_version" label="Agent版本" width="120" show-overflow-tooltip />
        <el-table-column prop="dataset_id" label="数据集" width="160" show-overflow-tooltip />
        <el-table-column prop="mode" label="模式" width="110" />
        <el-table-column prop="method" label="方式" width="110" />
        <el-table-column label="进度" width="140">
          <template #default="scope">
            <span>{{ scope.row.progress ?? 0 }}%</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="scope">
            <el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" :width="isNarrowScreen ? 360 : 430" :fixed="isNarrowScreen ? undefined : 'right'">
          <template #default="scope">
            <el-button size="small" type="success" plain class="op-btn" @click="runTask(scope.row.id)" :disabled="scope.row.status === 'running'">执行</el-button>
            <el-button size="small" type="warning" plain class="op-btn" @click="cancelTask(scope.row.id)" :disabled="scope.row.status !== 'running' && scope.row.status !== 'pending'">取消</el-button>
            <el-button size="small" plain class="op-btn" @click="cloneTask(scope.row.id)">克隆</el-button>
            <el-button size="small" type="danger" plain class="op-btn" @click="removeTask(scope.row.id)">删除</el-button>
            <el-button v-if="scope.row.status === 'completed'" size="small" type="warning" plain class="op-btn" @click="openLlmJudgeDialog(scope.row.id)">评估报告</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pager-wrap stagger-item" style="--stagger-order: 7">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[8, 12, 20, 30]"
        layout="total, sizes, prev, pager, next"
        :total="filteredTasks.length"
      />
    </div>

    <section v-if="selectedTask" class="task-results-preview stagger-item" style="--stagger-order: 8">
      <div class="task-results-head">
        <h3>选中任务结果预览</h3>
        <p>
          任务 #{{ selectedTask.id }} {{ selectedTask.name }}
          <el-tag size="small" :type="statusTagType(selectedTask.status)">{{ selectedTask.status }}</el-tag>
        </p>
        <el-button size="small" type="primary" plain @click="loadTaskResults(selectedTask.id)">刷新结果</el-button>
      </div>
      <div class="table-shell results-table-shell">
        <el-table v-loading="resultsLoading" :data="taskResults" stripe size="small" empty-text="暂无评测结果，请先执行该任务">
          <el-table-column prop="id" label="结果ID" width="90" />
          <el-table-column label="指标得分" min-width="240">
            <template #default="{ row }">
              <el-tag v-for="(v, k) in row.scores" :key="k" size="small" class="score-chip">{{ k }}: {{ v }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="说明" min-width="220">
            <template #default="{ row }">
              <span v-if="row.stats?.finished_at">完成于 {{ row.stats.finished_at }}</span>
              <span v-else>—</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <TaskModeLaunchDialog v-model="launchDialogVisible" @launch="handleLaunch" />

    <el-dialog
      v-model="llmJudgeDialogVisible"
      title="评估报告"
      width="720px"
      top="5vh"
      append-to-body
      destroy-on-close
    >
      <div v-loading="llmJudgeLoading" style="min-height: 200px">
        <el-empty v-if="!llmJudgeReport && !llmJudgeLoading" description="暂无评估报告">
          <template #description>
            <p style="margin-bottom: 12px">暂无评估报告</p>
            <el-button type="warning" :loading="llmJudgeTriggering" @click="handleTriggerLlmJudgeForTask(llmJudgeTaskId!)">
              {{ llmJudgeTriggering ? '评估中...' : '触发评估' }}
            </el-button>
          </template>
        </el-empty>

        <template v-if="llmJudgeReport">
          <div class="judge-overall">
            <div class="judge-score-ring">
              <span class="score-value">{{ llmJudgeReport.assessment.overall_score.toFixed(2) }}</span>
              <span class="score-label">综合评分</span>
            </div>
            <div class="judge-confidence" :class="llmJudgeReport.assessment.confidence">
              置信度: {{ llmJudgeReport.assessment.confidence }}
            </div>
            <div style="margin-left: auto">
              <el-button type="warning" plain size="small" :loading="llmJudgeTriggering" @click="handleTriggerLlmJudgeForTask(llmJudgeTaskId!)">
                {{ llmJudgeTriggering ? '评估中...' : '重新评估' }}
              </el-button>
            </div>
          </div>

          <div class="judge-dimensions" v-if="Object.keys(llmJudgeReport.assessment.dimension_scores).length">
            <h4>维度评分</h4>
            <div class="dimension-grid">
              <div
                v-for="(score, dim) in llmJudgeReport.assessment.dimension_scores"
                :key="dim"
                class="dimension-item"
              >
                <span class="dim-label">{{ dim }}</span>
                <el-progress
                  :percentage="Number(Number(score).toFixed(0))"
                  :stroke-width="16"
                  :text-inside="true"
                  :status="Number(score) >= 80 ? 'success' : Number(score) >= 50 ? 'warning' : 'exception'"
                >
                  <span>{{ Number(score).toFixed(2) }} / 100</span>
                </el-progress>
              </div>
            </div>
          </div>

          <div class="judge-analysis">
            <h4>分析总结</h4>
            <p>{{ llmJudgeReport.assessment.analysis }}</p>
          </div>

          <div class="judge-lists">
            <div class="judge-list-block" v-if="llmJudgeReport.assessment.strengths.length">
              <h4>优势</h4>
              <ul>
                <li v-for="(item, idx) in llmJudgeReport.assessment.strengths" :key="idx">{{ item }}</li>
              </ul>
            </div>
            <div class="judge-list-block" v-if="llmJudgeReport.assessment.weaknesses.length">
              <h4>不足</h4>
              <ul>
                <li v-for="(item, idx) in llmJudgeReport.assessment.weaknesses" :key="idx">{{ item }}</li>
              </ul>
            </div>
          </div>

          <div class="judge-recommendations" v-if="llmJudgeReport.assessment.recommendations.length">
            <h4>改进建议</h4>
            <ol>
              <li v-for="(item, idx) in llmJudgeReport.assessment.recommendations" :key="idx">{{ item }}</li>
            </ol>
          </div>

          <div class="judge-meta">
            <span>评估时间: {{ new Date(llmJudgeReport.created_at).toLocaleString() }}</span>
          </div>
        </template>
      </div>
    </el-dialog>

    <el-dialog
      v-model="modeWorkbenchVisible"
      :title="modeWorkbenchTitle"
      width="96vw"
      top="2vh"
      class="mode-workbench-dialog"
      append-to-body
      destroy-on-close
    >
      <div class="mode-workbench-host">
        <component :is="modeWorkbenchComponent" />
      </div>
    </el-dialog>
  </section>
</template>

<style scoped>
.task-kpis {
  margin: 10px 0 14px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.task-kpis article {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #d6e1f1;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(247, 250, 255, 0.86));
  display: flex;
  align-items: baseline;
  gap: 8px;
  box-shadow: 0 8px 18px rgba(19, 34, 58, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.task-kpis article:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 20px rgba(19, 34, 58, 0.12);
}

.task-kpis strong {
  font-size: 24px;
  color: #0f766e;
}

.task-kpis span {
  color: #4b5563;
}

.task-page {
  width: 100%;
  min-width: 0;
  overflow: hidden;
}

.task-filters {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px dashed #c9d8eb;
}

.filter-control {
  width: 150px;
}

.filter-keyword {
  width: 260px;
}

.table-shell {
  width: 100%;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  border-radius: 12px;
}

.task-main-table {
  min-width: 1220px;
}

.op-btn {
  margin: 2px 6px 2px 0;
}

.pager-wrap {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #f4f8ff;
}

:deep(.el-table .task-row-intro) {
  opacity: 0;
  transform: translateY(8px);
  animation: task-row-fade-in 0.45s ease forwards;
}

:deep(.el-table .row-intro-0) { animation-delay: 0ms; }
:deep(.el-table .row-intro-1) { animation-delay: 60ms; }
:deep(.el-table .row-intro-2) { animation-delay: 120ms; }
:deep(.el-table .row-intro-3) { animation-delay: 180ms; }
:deep(.el-table .row-intro-4) { animation-delay: 240ms; }
:deep(.el-table .row-intro-5) { animation-delay: 300ms; }
:deep(.el-table .row-intro-6) { animation-delay: 360ms; }
:deep(.el-table .row-intro-7) { animation-delay: 420ms; }
:deep(.el-table .row-intro-8) { animation-delay: 480ms; }
:deep(.el-table .row-intro-9) { animation-delay: 540ms; }

@keyframes task-row-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .task-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .task-filters {
    gap: 8px;
  }

  .filter-control,
  .filter-keyword {
    width: 100%;
  }

  .task-main-table {
    min-width: 980px;
  }

  .pager-wrap {
    justify-content: flex-start;
  }
}

.task-results-preview {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid #d6e1f1;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(247, 250, 255, 0.88));
}

.task-results-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.task-results-head h3 {
  margin: 0;
  font-size: 16px;
}

.task-results-head p {
  margin: 0;
  flex: 1;
  color: #4b5563;
}

.score-chip {
  margin: 2px 4px 2px 0;
}

:deep(.mode-workbench-dialog .el-dialog__body) {
  max-height: calc(100vh - 126px);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 14px 14px;
}

:deep(.mode-workbench-dialog .el-dialog__header) {
  border-bottom: 1px solid #e2e8f0;
  padding: 12px 16px 10px;
}

:deep(.mode-workbench-dialog) {
  width: min(1520px, 96vw) !important;
}

:deep(.mode-workbench-dialog .el-dialog__title) {
  font-size: 19px;
  font-weight: 600;
}

.mode-workbench-host {
  min-width: 0;
}

.mode-workbench-host :deep(.panel) {
  margin: 0;
  padding: 16px;
}

@media (max-width: 1200px) {
  .mode-workbench-host :deep(.panel) {
    padding: 14px;
  }
}

/* LLM Judge dialog styles */
.judge-overall {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
}

.judge-score-ring {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f59e0b, #ef6c2f);
  color: #fff;
  flex-shrink: 0;
}

.judge-score-ring .score-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.judge-score-ring .score-label {
  font-size: 11px;
  opacity: 0.9;
  margin-top: 2px;
}

.judge-confidence {
  font-size: 13px;
  padding: 4px 14px;
  border-radius: 20px;
  font-weight: 600;
}

.judge-confidence.high {
  background: #dcfce7;
  color: #166534;
}

.judge-confidence.medium {
  background: #fef3c7;
  color: #92400e;
}

.judge-confidence.low {
  background: #fee2e2;
  color: #991b1b;
}

.judge-dimensions {
  margin-bottom: 18px;
}

.judge-dimensions h4,
.judge-analysis h4,
.judge-lists h4,
.judge-recommendations h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #1e293b;
}

.dimension-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.dimension-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dim-label {
  font-size: 13px;
  color: #475569;
  min-width: 70px;
  flex-shrink: 0;
  text-transform: capitalize;
}

.dimension-item :deep(.el-progress) {
  flex: 1;
}

.judge-analysis {
  margin-bottom: 18px;
}

.judge-analysis p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #334155;
  background: #f8fafc;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.judge-lists {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 18px;
}

.judge-list-block ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.8;
  color: #334155;
}

.judge-recommendations {
  margin-bottom: 16px;
}

.judge-recommendations ol {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.8;
  color: #334155;
}

.judge-meta {
  font-size: 12px;
  color: #94a3b8;
  border-top: 1px solid #e2e8f0;
  padding-top: 10px;
  margin-top: 10px;
}
</style>
