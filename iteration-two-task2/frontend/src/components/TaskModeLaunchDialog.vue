<script setup lang="ts">
import { computed, ref } from "vue";

export type LaunchMode = "realtime" | "offline-trace" | "dataset-batch";

defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "launch", mode: LaunchMode): void;
}>();

const selectedMode = ref<LaunchMode>("realtime");

const modeOptions: Array<{ mode: LaunchMode; title: string; subtitle: string; tags: string[] }> = [
  {
    mode: "realtime",
    title: "模式1 在线实时评估",
    subtitle: "运行中监控、告警与拦截",
    tags: ["实时告警", "阈值拦截", "低延迟"],
  },
  {
    mode: "offline-trace",
    title: "模式2 轨迹离线评估",
    subtitle: "提交完整 Trace 进行异步统一评估",
    tags: ["能力评分", "根因分析", "优化建议"],
  },
  {
    mode: "dataset-batch",
    title: "模式3 数据集批量评估",
    subtitle: "导入历史数据批量评测和版本对比",
    tags: ["批量任务", "回归测试", "摘要报表"],
  },
];

const selectedDetail = computed(() => modeOptions.find((item) => item.mode === selectedMode.value));

const confirmLaunch = () => {
  emit("launch", selectedMode.value);
  emit("update:modelValue", false);
};
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="新建任务 - 选择评估模式"
    width="860px"
    @update:model-value="(v: boolean) => emit('update:modelValue', v)"
  >
    <div class="launch-layout">
      <div class="mode-list">
        <button
          v-for="item in modeOptions"
          :key="item.mode"
          type="button"
          class="mode-item"
          :class="{ active: selectedMode === item.mode }"
          @click="selectedMode = item.mode"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.subtitle }}</span>
        </button>
      </div>

      <div class="mode-detail" v-if="selectedDetail">
        <h3>{{ selectedDetail.title }}</h3>
        <p>{{ selectedDetail.subtitle }}</p>
        <div class="tag-wrap">
          <el-tag v-for="tag in selectedDetail.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="confirmLaunch">进入初始化页面</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.launch-layout {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 14px;
}

.mode-list {
  display: grid;
  gap: 10px;
}

.mode-item {
  border: 1px solid #d8e4f5;
  background: #f8fbff;
  border-radius: 12px;
  text-align: left;
  padding: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.mode-item strong {
  display: block;
  color: #1e293b;
  margin-bottom: 4px;
}

.mode-item span {
  color: #64748b;
  font-size: 13px;
}

.mode-item:hover {
  transform: translateY(-1px);
  border-color: #95b4e6;
}

.mode-item.active {
  border-color: #3b82f6;
  box-shadow: 0 8px 18px rgba(59, 130, 246, 0.18);
  background: linear-gradient(145deg, #f8fbff, #eef5ff);
}

.mode-detail {
  border: 1px dashed #c7d7ee;
  border-radius: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.75);
}

.mode-detail h3 {
  margin: 0;
  font-size: 18px;
  color: #0f172a;
}

.mode-detail p {
  margin: 8px 0 12px;
  color: #475569;
}

.tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 900px) {
  .launch-layout {
    grid-template-columns: 1fr;
  }
}
</style>
