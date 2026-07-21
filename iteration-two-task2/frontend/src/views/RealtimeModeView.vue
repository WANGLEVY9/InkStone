<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import {
  endRealtimeSession,
  getRealtimeSessionDetail,
  ingestRealtimeStreamEvent,
  listRealtimeSessions,
  realtimeStepEnd,
  realtimeStepStart,
  realtimeToolCall,
  RealtimeAlert,
  RealtimeSession,
  RealtimeStreamEvent,
  startRealtimeSession,
} from "../api/modeEval";
import { useRealtimeWebSocket } from "../composables/useRealtimeWebSocket";

const creating = ref(false);
const actionLoading = ref(false);
const loading = ref(false);
const loadError = ref("");
const controlTab = ref("hook");

const sessionForm = reactive({
  session_id: "",
  agent_name: "langgraph-supervisor",
  task: "多Agent协作生成网络小说章节",
  max_tool_calls: 15,
  max_duration_sec: 30,
  max_same_action: 3,
  max_steps: 80,
  max_same_node: 5,
  max_node_switches: 8,
});

const stepForm = reactive({
  step: 1,
  thought: "",
  action: "query_order",
  duration_sec: 1,
  tool_name: "query_order",
  dangerous: false,
  step_result: "订单已查询",
});

const streamForm = reactive({
  step: 1,
  event_type: "node_execution",
  node: "supervisor",
  agent_type: "supervisor",
  thought: "",
  message: "",
  next_agent: "writer-agent",
  duration_sec: 0.8,
  tool_calls_json: "[]",
  state_json: "{}",
  source: "langgraph-stream",
});

const sessions = ref<RealtimeSession[]>([]);
const activeSessionId = ref("");
const activeSession = ref<RealtimeSession | null>(null);
const latestAlerts = ref<RealtimeAlert[]>([]);
const latestEvents = ref<RealtimeStreamEvent[]>([]);
let fallbackPollTimer: ReturnType<typeof setInterval> | null = null;
let wsFallbackMode = false;

// WebSocket composable
const wsClient = useRealtimeWebSocket();

// Register WebSocket event handlers
wsClient.on("session_init", (data: any) => {
  if (data.session) {
    activeSession.value = data.session;
    latestAlerts.value = data.latest_alerts || [];
    latestEvents.value = data.latest_events || [];
  }
});

wsClient.on("session_created", (data: any) => {
  void refreshSessionsList();
});

wsClient.on("session_ended", (data: any) => {
  if (data.session) {
    activeSession.value = data.session;
  }
  void refreshSessionsList();
});

wsClient.on("step_start", (data: any) => {
  if (data.session) activeSession.value = data.session;
});

wsClient.on("tool_call", (data: any) => {
  if (data.session) activeSession.value = data.session;
});

wsClient.on("step_end", (data: any) => {
  if (data.session) activeSession.value = data.session;
});

wsClient.on("stream_event", (data: any) => {
  if (data.session) activeSession.value = data.session;
  if (data.event) {
    latestEvents.value = [data.event as RealtimeStreamEvent, ...latestEvents.value].slice(0, 40);
  }
});

wsClient.on("session_stopped", (data: any) => {
  if (data.session) activeSession.value = data.session;
  if (data.decision) {
    ElMessage.warning(`规则触发: ${data.decision}${data.reason ? ` (${data.reason})` : ""}`);
  }
  void refreshSessionsList();
  void refreshAlerts();
});

// Watch activeSessionId changes → reconnect WebSocket
watch(activeSessionId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    wsClient.connect(newId);
    wsFallbackMode = false;
    stopFallbackPoll();
  }
});

const refreshSessionsList = async () => {
  try {
    const data = await listRealtimeSessions();
    sessions.value = data.items;
    loadError.value = "";
  } catch {
    loadError.value = "会话列表加载失败";
  }
};

const refreshAlerts = async () => {
  if (!activeSessionId.value) return;
  try {
    const data = await getRealtimeSessionDetail(activeSessionId.value);
    activeSession.value = data.session;
    latestAlerts.value = data.latest_alerts;
    latestEvents.value = data.latest_events || [];
    loadError.value = "";
  } catch {
    loadError.value = "会话详情加载失败";
  }
};

const initialLoad = async () => {
  loading.value = true;
  try {
    await refreshSessionsList();
    if (!activeSessionId.value && sessions.value.length) {
      activeSessionId.value = sessions.value[0].session_id;
    }
    if (activeSessionId.value) {
      wsClient.connect(activeSessionId.value);
      wsFallbackMode = false;
    }
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await initialLoad();
});

onBeforeUnmount(() => {
  wsClient.disconnect();
  stopFallbackPoll();
});

// Fallback polling when WebSocket is unavailable
const startFallbackPoll = () => {
  stopFallbackPoll();
  wsFallbackMode = true;
  fallbackPollTimer = setInterval(() => {
    void refreshAlerts();
  }, 5000);
};

const stopFallbackPoll = () => {
  if (fallbackPollTimer) {
    clearInterval(fallbackPollTimer);
    fallbackPollTimer = null;
  }
};

// Monitor WebSocket connection and fall back to polling
watch(() => wsClient.connected.value, (isConnected) => {
  if (!isConnected && activeSessionId.value) {
    startFallbackPoll();
  } else {
    stopFallbackPoll();
  }
});

const sessionStatusType = (status: string) => {
  if (status === "completed") return "success";
  if (status === "running") return "warning";
  if (status === "blocked" || status === "timeout" || status === "stopped") return "danger";
  return "info";
};

const alertTagType = (severity: string) => {
  if (severity === "critical") return "danger";
  if (severity === "warning") return "warning";
  return "info";
};

const decisionTagType = (decision: string) => {
  if (decision === "BLOCK") return "danger";
  if (decision === "STOP" || decision === "TIMEOUT") return "warning";
  return "success";
};

const startSession = async () => {
  creating.value = true;
  try {
    const session = await startRealtimeSession({
      session_id: sessionForm.session_id || undefined,
      agent_name: sessionForm.agent_name,
      task: sessionForm.task,
      thresholds: {
        max_tool_calls: Number(sessionForm.max_tool_calls),
        max_duration_sec: Number(sessionForm.max_duration_sec),
        max_same_action: Number(sessionForm.max_same_action),
        max_steps: Number(sessionForm.max_steps),
        max_same_node: Number(sessionForm.max_same_node),
        max_node_switches: Number(sessionForm.max_node_switches),
      },
    });
    activeSessionId.value = session.session_id;
    ElMessage.success("实时评估会话已启动");
    await refreshSessionsList();
  } finally {
    creating.value = false;
  }
};

const sendStepStart = async () => {
  if (!activeSessionId.value) {
    ElMessage.warning("请先启动会话");
    return;
  }
  actionLoading.value = true;
  try {
    await realtimeStepStart(activeSessionId.value, {
      step: Number(stepForm.step),
      thought: stepForm.thought,
      action: stepForm.action,
    });
    ElMessage.success("已上报 step-start");
  } finally {
    actionLoading.value = false;
  }
};

const sendToolCall = async () => {
  if (!activeSessionId.value) {
    ElMessage.warning("请先启动会话");
    return;
  }
  actionLoading.value = true;
  try {
    await realtimeToolCall(activeSessionId.value, {
      tool_name: stepForm.tool_name,
      params: { from: "dashboard" },
      dangerous: stepForm.dangerous,
    });
    ElMessage.success("已上报 tool-call");
  } finally {
    actionLoading.value = false;
  }
};

const sendStepEnd = async () => {
  if (!activeSessionId.value) {
    ElMessage.warning("请先启动会话");
    return;
  }
  actionLoading.value = true;
  try {
    await realtimeStepEnd(activeSessionId.value, {
      step: Number(stepForm.step),
      action: stepForm.action,
      duration_sec: Number(stepForm.duration_sec),
      step_result: stepForm.step_result,
    });
    ElMessage.success("已上报 step-end");
  } finally {
    actionLoading.value = false;
  }
};

const sendLangGraphEvent = async () => {
  if (!activeSessionId.value) {
    ElMessage.warning("请先启动会话");
    return;
  }
  actionLoading.value = true;
  try {
    const parsedToolCalls = JSON.parse(streamForm.tool_calls_json || "[]");
    const parsedState = JSON.parse(streamForm.state_json || "{}");
    const data = await ingestRealtimeStreamEvent(activeSessionId.value, {
      step: Number(streamForm.step),
      event_type: streamForm.event_type,
      node: streamForm.node,
      agent_type: streamForm.agent_type,
      thought: streamForm.thought,
      message: streamForm.message,
      next_agent: streamForm.next_agent,
      duration_sec: Number(streamForm.duration_sec),
      tool_calls: Array.isArray(parsedToolCalls) ? parsedToolCalls : [],
      state: parsedState && typeof parsedState === "object" ? parsedState : {},
      source: streamForm.source,
    });
    // WebSocket will push event, but also handle immediate response
    latestEvents.value = [data.event as RealtimeStreamEvent, ...latestEvents.value].slice(0, 40);
    if (data.session) activeSession.value = data.session;
    if (data.should_stop) {
      ElMessage.warning(`规则触发: ${data.decision}${data.reason ? ` (${data.reason})` : ""}`);
    } else {
      ElMessage.success("已上报 LangGraph 流事件");
    }
    streamForm.step += 1;
  } catch {
    ElMessage.error("上报失败，请检查 tool_calls_json / state_json 是否为合法 JSON");
  } finally {
    actionLoading.value = false;
  }
};

const stopSession = async () => {
  if (!activeSessionId.value) return;
  actionLoading.value = true;
  try {
    await endRealtimeSession(activeSessionId.value);
    ElMessage.success("会话已结束");
    await refreshSessionsList();
  } finally {
    actionLoading.value = false;
  }
};

const fillLangGraphExample = () => {
  streamForm.event_type = "node_execution";
  streamForm.node = "supervisor";
  streamForm.agent_type = "supervisor";
  streamForm.thought = "根据章节提纲将任务派发给 writer-agent";
  streamForm.message = "路由到 writer-agent 产出章节草稿";
  streamForm.next_agent = "writer-agent";
  streamForm.duration_sec = 0.7;
  streamForm.tool_calls_json = JSON.stringify(
    [
      {
        name: "outline_search",
        params: { chapter: 3, style: "xianxia" },
        dangerous: false,
      },
    ],
    null,
    2
  );
  streamForm.state_json = JSON.stringify(
    {
      chapter_id: "ch_003",
      memory_window: 12,
      target_words: 3000,
    },
    null,
    2
  );
};

const manualRefresh = async () => {
  loading.value = true;
  try {
    await refreshSessionsList();
    await refreshAlerts();
  } finally {
    loading.value = false;
  }
};

const kpi = computed(() => {
  const total = sessions.value.length;
  const running = sessions.value.filter((item) => item.status === "running").length;
  const blocked = sessions.value.filter((item) => ["blocked", "timeout", "stopped"].includes(item.status)).length;
  const alerts = sessions.value.reduce((sum, item) => sum + item.alert_count, 0);
  return { total, running, blocked, alerts };
});

const wsConnected = computed(() => wsClient.connected.value);

// Node topology: extract nodes and edges from latest events
const nodeColors = ["#0f766e", "#ef6c2f", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6", "#f59e0b", "#6366f1"];

const topologyOption = computed(() => {
  const nodesMap = new Map<string, { name: string; itemStyle: { color: string }; symbolSize: number }>();
  const edgeKeySet = new Set<string>();
  const edges: { source: string; target: string; lineStyle: Record<string, unknown> }[] = [];

  for (const evt of latestEvents.value) {
    if (!evt.node) continue;

    // Add source node
    if (!nodesMap.has(evt.node)) {
      nodesMap.set(evt.node, {
        name: evt.node,
        itemStyle: { color: nodeColors[nodesMap.size % nodeColors.length] },
        symbolSize: evt.node === "supervisor" ? 58 : 46,
      });
    }

    // Add target node from next_agent
    const target = evt.next_agent;
    if (target && target !== evt.node) {
      if (!nodesMap.has(target)) {
        nodesMap.set(target, {
          name: target,
          itemStyle: { color: nodeColors[nodesMap.size % nodeColors.length] },
          symbolSize: 46,
        });
      }
      const ek = `${evt.node}->${target}`;
      if (edgeKeySet.has(ek)) continue;
      edgeKeySet.add(ek);
      edges.push({ source: evt.node, target, lineStyle: { color: "#94a3b8", width: 2 } });
    }

    // Add tool calls as leaf nodes
    if (evt.tool_calls && evt.tool_calls.length > 0) {
      for (const tc of evt.tool_calls) {
        const toolName = tc.name;
        if (!toolName || nodesMap.has(toolName)) continue;
        nodesMap.set(toolName, {
          name: toolName,
          itemStyle: { color: "#94a3b8" },
          symbolSize: 32,
        });
        const ek = `${evt.node}->${toolName}`;
        if (edgeKeySet.has(ek)) continue;
        edgeKeySet.add(ek);
        edges.push({ source: evt.node, target: toolName, lineStyle: { color: "#cbd5e1", width: 1.5, type: "dashed" } });
      }
    }
  }

  if (nodesMap.size === 0 && activeSession.value?.current_node) {
    nodesMap.set(activeSession.value.current_node, {
      name: activeSession.value.current_node,
      itemStyle: { color: nodeColors[0] },
      symbolSize: 52,
    });
  }

  return {
    tooltip: {},
    series: [
      {
        type: "graph",
        layout: "force",
        force: { repulsion: 400, edgeLength: 180, friction: 0.1 },
        roam: true,
        draggable: true,
        data: Array.from(nodesMap.values()),
        edges,
        label: {
          show: true,
          position: "bottom",
          fontSize: 11,
          color: "#334155",
          formatter: (p: { name: string }) => p.name,
        },
        edgeLabel: { show: false },
        lineStyle: { opacity: 0.7, curveness: 0.2 },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 3 },
        },
        itemStyle: { borderColor: "#fff", borderWidth: 2 },
        animation: true,
      },
    ],
  };
});
</script>

<template>
  <section class="panel card-rise" v-loading="loading">
    <div class="panel-head">
      <div>
        <h2>模式1：在线实时评估（运行中实时监控）</h2>
        <p>兼容传统 Hook 与 LangGraph + MultiAgent 流事件采集，支持实时告警/拦截</p>
      </div>
      <div class="actions">
        <el-tag v-if="wsConnected" type="success" size="small" effect="dark" class="ws-tag">WebSocket 已连接</el-tag>
        <el-tag v-else type="warning" size="small" effect="dark" class="ws-tag">轮询回退</el-tag>
        <el-button @click="manualRefresh">刷新</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" :title="loadError" type="error" show-icon :closable="true" class="load-error" @close="loadError = ''" />

    <div class="kpi-grid">
      <article><strong>{{ kpi.total }}</strong><span>总会话</span></article>
      <article><strong>{{ kpi.running }}</strong><span>运行中</span></article>
      <article><strong>{{ kpi.blocked }}</strong><span>拦截/终止</span></article>
      <article><strong>{{ kpi.alerts }}</strong><span>告警总数</span></article>
    </div>

    <div class="two-col">
      <el-card shadow="never" class="card-block">
        <template #header>创建实时会话</template>
        <el-form label-width="120px">
          <el-form-item label="Session ID"><el-input v-model="sessionForm.session_id" placeholder="可留空自动生成" /></el-form-item>
          <el-form-item label="Agent 名称"><el-input v-model="sessionForm.agent_name" /></el-form-item>
          <el-form-item label="任务描述"><el-input v-model="sessionForm.task" /></el-form-item>
          <el-form-item label="工具次数阈值"><el-input-number v-model="sessionForm.max_tool_calls" :min="1" /></el-form-item>
          <el-form-item label="超时阈值(s)"><el-input-number v-model="sessionForm.max_duration_sec" :min="1" /></el-form-item>
          <el-form-item label="重复动作阈值"><el-input-number v-model="sessionForm.max_same_action" :min="2" /></el-form-item>
          <el-form-item label="最大步数"><el-input-number v-model="sessionForm.max_steps" :min="10" /></el-form-item>
          <el-form-item label="同节点阈值"><el-input-number v-model="sessionForm.max_same_node" :min="3" /></el-form-item>
          <el-form-item label="切换震荡阈值"><el-input-number v-model="sessionForm.max_node_switches" :min="3" /></el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="startSession">启动会话</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never" class="card-block">
        <template #header>实时上报控制台（Hook / LangGraph）</template>
        <el-form label-width="120px" class="session-selector-form">
          <el-form-item label="目标会话">
            <el-select v-model="activeSessionId" filterable style="width: 100%" placeholder="选择会话">
              <el-option v-for="item in sessions" :key="item.session_id" :label="`${item.session_id} (${item.status})`" :value="item.session_id" />
            </el-select>
          </el-form-item>
        </el-form>

        <el-tabs v-model="controlTab">
          <el-tab-pane label="传统 Hook" name="hook">
            <el-form label-width="120px">
              <el-form-item label="Step"><el-input-number v-model="stepForm.step" :min="1" /></el-form-item>
              <el-form-item label="Action"><el-input v-model="stepForm.action" /></el-form-item>
              <el-form-item label="Thought"><el-input v-model="stepForm.thought" /></el-form-item>
              <el-form-item label="Tool Name"><el-input v-model="stepForm.tool_name" /></el-form-item>
              <el-form-item label="Dangerous"><el-switch v-model="stepForm.dangerous" /></el-form-item>
              <el-form-item label="Duration(s)"><el-input-number v-model="stepForm.duration_sec" :min="0" :step="0.5" /></el-form-item>
              <el-form-item>
                <el-button :loading="actionLoading" @click="sendStepStart">on_step_start</el-button>
                <el-button :loading="actionLoading" @click="sendToolCall">on_tool_call</el-button>
                <el-button :loading="actionLoading" @click="sendStepEnd">on_step_end</el-button>
                <el-button type="danger" plain :loading="actionLoading" @click="stopSession">on_agent_end</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="LangGraph 流" name="langgraph">
            <el-form label-width="120px">
              <el-form-item label="Step"><el-input-number v-model="streamForm.step" :min="1" /></el-form-item>
              <el-form-item label="Node"><el-input v-model="streamForm.node" placeholder="supervisor / writer-agent / critic-agent" /></el-form-item>
              <el-form-item label="Agent Type">
                <el-select v-model="streamForm.agent_type" style="width: 100%">
                  <el-option label="supervisor" value="supervisor" />
                  <el-option label="worker" value="worker" />
                </el-select>
              </el-form-item>
              <el-form-item label="Event Type">
                <el-select v-model="streamForm.event_type" style="width: 100%">
                  <el-option label="node_execution" value="node_execution" />
                  <el-option label="tool_call" value="tool_call" />
                  <el-option label="state_update" value="state_update" />
                </el-select>
              </el-form-item>
              <el-form-item label="Thought"><el-input v-model="streamForm.thought" /></el-form-item>
              <el-form-item label="Message"><el-input v-model="streamForm.message" /></el-form-item>
              <el-form-item label="Next Agent"><el-input v-model="streamForm.next_agent" /></el-form-item>
              <el-form-item label="Duration(s)"><el-input-number v-model="streamForm.duration_sec" :min="0" :step="0.1" /></el-form-item>
              <el-form-item label="Tool Calls JSON">
                <el-input v-model="streamForm.tool_calls_json" type="textarea" :rows="4" class="json-editor" />
              </el-form-item>
              <el-form-item label="State JSON">
                <el-input v-model="streamForm.state_json" type="textarea" :rows="4" class="json-editor" />
              </el-form-item>
              <el-form-item label="Source"><el-input v-model="streamForm.source" /></el-form-item>
              <el-form-item>
                <el-button plain @click="fillLangGraphExample">填充 LangGraph 示例</el-button>
                <el-button type="primary" :loading="actionLoading" @click="sendLangGraphEvent">上报流事件</el-button>
                <el-button type="danger" plain :loading="actionLoading" @click="stopSession">结束会话</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <div class="two-col">
      <el-card shadow="never" class="card-block">
        <template #header>会话状态</template>
        <div v-if="activeSession" class="status-grid">
          <div><label>状态</label><el-tag :type="sessionStatusType(activeSession.status)">{{ activeSession.status }}</el-tag></div>
          <div><label>step 数</label><strong>{{ activeSession.step_count }}</strong></div>
          <div><label>tool 调用</label><strong>{{ activeSession.tool_call_count }}</strong></div>
          <div><label>连续动作</label><strong>{{ activeSession.consecutive_same_action }}</strong></div>
          <div><label>节点切换</label><strong>{{ activeSession.node_switch_count }}</strong></div>
          <div><label>事件总数</label><strong>{{ activeSession.event_count }}</strong></div>
          <div><label>当前节点</label><strong>{{ activeSession.current_node || "-" }}</strong></div>
          <div><label>当前角色</label><strong>{{ activeSession.current_agent_type || "-" }}</strong></div>
          <div><label>最近决策</label><strong>{{ activeSession.latest_decision }}</strong></div>
          <div><label>告警数</label><strong>{{ activeSession.alert_count }}</strong></div>
        </div>
        <el-empty v-else description="暂无会话" />
      </el-card>

      <el-card shadow="never" class="card-block">
        <template #header>实时告警流</template>
        <el-table :data="latestAlerts" size="small" height="320" v-if="latestAlerts.length > 0">
          <el-table-column prop="created_at" label="时间" width="180" />
          <el-table-column prop="rule" label="规则" width="130" />
          <el-table-column label="级别" width="100">
            <template #default="scope">
              <el-tag size="small" :type="alertTagType(scope.row.severity)">{{ scope.row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="decision" label="决策" width="100" />
          <el-table-column prop="message" label="消息" min-width="240" />
        </el-table>
        <el-empty v-else description="暂无告警" />
      </el-card>
    </div>

    <el-card shadow="never" class="card-block">
      <template #header>Agent 节点拓扑</template>
      <div class="topology-hint" v-if="latestEvents.length === 0">暂无事件数据，上报流事件后将自动生成节点关系图</div>
      <v-chart class="topology-chart" :option="topologyOption" autoresize />
    </el-card>

    <el-card shadow="never" class="card-block">
      <template #header>实时事件流（LangGraph / MultiAgent）</template>
      <el-table :data="latestEvents" size="small" height="360" v-if="latestEvents.length > 0">
        <el-table-column type="expand" width="40">
          <template #default="scope">
            <div class="event-detail">
              <div v-if="scope.row.thought"><label>推理过程：</label><p>{{ scope.row.thought }}</p></div>
              <div v-if="scope.row.tool_calls && scope.row.tool_calls.length">
                <label>工具调用：</label>
                <ul>
                  <li v-for="(tc, idx) in scope.row.tool_calls" :key="idx">
                    <code>{{ tc.name }}</code>
                    <span v-if="tc.dangerous" class="danger-badge">危险</span>
                  </li>
                </ul>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column prop="step" label="Step" width="60" />
        <el-table-column prop="node" label="Node" min-width="150" />
        <el-table-column prop="agent_type" label="角色" width="100" />
        <el-table-column prop="event_type" label="事件类型" width="130" />
        <el-table-column label="决策" width="100">
          <template #default="scope">
            <el-tag size="small" :type="decisionTagType(scope.row.decision)">{{ scope.row.decision }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="120" />
        <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-empty v-else description="暂无事件数据，上报流事件后将在此显示" />
    </el-card>

    <el-alert type="info" show-icon :closable="false" class="hook-note">
      <template #title>
        推荐接入方式：LangGraph graph.stream(..., stream_mode='updates') 每步调用 /mode-realtime/sessions/{session_id}/events，上报 node/agent_type/next_agent/tool_calls/state/duration，平台实时返回 CONTINUE/STOP/BLOCK/TIMEOUT。
        <span v-if="!wsConnected"> WebSocket 未连接，使用 5s 轮询回退。</span>
      </template>
    </el-alert>
  </section>
</template>

<style scoped>
.ws-tag {
  margin-right: 8px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kpi-grid article {
  border: 1px solid #d8e4f5;
  border-radius: 12px;
  padding: 12px;
  background: #f8fbff;
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.kpi-grid strong {
  font-size: 24px;
  color: #0f766e;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.two-col > * {
  min-width: 0;
}

.card-block {
  border-radius: 14px;
}

.session-selector-form {
  margin-bottom: 4px;
}

.json-editor :deep(textarea) {
  font-family: Consolas, "Courier New", monospace;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.status-grid div {
  border: 1px solid #d8e4f5;
  border-radius: 10px;
  padding: 10px;
  background: #fbfdff;
  min-width: 0;
}

.status-grid label {
  color: #64748b;
  display: block;
  margin-bottom: 4px;
}

.hook-note {
  margin-top: 6px;
}

.topology-chart {
  height: 340px;
}

.topology-hint {
  text-align: center;
  color: #94a3b8;
  padding: 20px 0;
  font-size: 13px;
}

.load-error {
  margin-bottom: 12px;
}

.event-detail {
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.event-detail label {
  color: #64748b;
  font-weight: 600;
  display: block;
  margin-top: 6px;
}

.event-detail p {
  margin: 4px 0;
  color: #334155;
}

.event-detail ul {
  margin: 4px 0;
  padding-left: 16px;
}

.event-detail code {
  background: #e2e8f0;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.danger-badge {
  display: inline-block;
  background: #fee2e2;
  color: #dc2626;
  font-size: 11px;
  padding: 0 6px;
  border-radius: 4px;
  margin-left: 4px;
}

@media (max-width: 1200px) {
  .two-col,
  .status-grid {
    grid-template-columns: 1fr;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
