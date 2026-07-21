<template>
  <div class="app-shell">
    <div class="ambient-bg" aria-hidden="true">
      <span class="blob blob-a"></span>
      <span class="blob blob-b"></span>
      <span class="blob blob-c"></span>
      <span class="grid-overlay"></span>
    </div>

    <aside class="side-nav">
      <div class="side-brand">
        <p class="eyebrow">Agent Intelligence Workbench</p>
        <h1>Agent Eval Hub</h1>
        <p>全生命周期智能体评测平台</p>
      </div>

      <el-menu router class="side-menu" :default-active="$route.path">
        <el-menu-item index="/tasks">任务管理</el-menu-item>
        <el-menu-item index="/config">评测配置</el-menu-item>
        <el-menu-item index="/results">结果分析</el-menu-item>
      </el-menu>

      <div class="side-bottom">
        <el-button class="style-btn" type="primary" plain @click="styleDrawerVisible = true">风格设置</el-button>
      </div>
    </aside>

    <main class="content-wrap">
      <router-view v-slot="{ Component }">
        <transition name="route-shift" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <el-drawer
      v-model="styleDrawerVisible"
      title="视觉风格设置"
      size="360px"
      class="style-drawer"
      append-to-body
    >
      <div class="style-form">
        <el-form label-position="top">
          <el-form-item label="风格主题">
            <el-segmented v-model="uiSettings.theme" :options="themeOptions" />
          </el-form-item>

          <el-form-item label="界面密度">
            <el-radio-group v-model="uiSettings.density">
              <el-radio-button label="compact">紧凑</el-radio-button>
              <el-radio-button label="balanced">均衡</el-radio-button>
              <el-radio-button label="airy">舒展</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="动效节奏">
            <el-slider
              v-model="uiSettings.motionLevel"
              :min="0"
              :max="2"
              :step="1"
              show-stops
              :format-tooltip="formatMotionTip"
            />
          </el-form-item>

          <el-form-item label="玻璃拟态">
            <el-switch
              v-model="uiSettings.glassmorphism"
              inline-prompt
              active-text="开"
              inactive-text="关"
            />
          </el-form-item>
        </el-form>

        <div class="style-preview">
          <h4>风格预览</h4>
          <p>你可以实时预览，设置会自动保存到本地。</p>
          <div class="preview-tags">
            <el-tag type="primary">层次感</el-tag>
            <el-tag type="success">对比度</el-tag>
            <el-tag type="warning">动效</el-tag>
          </div>
        </div>

        <div class="style-actions">
          <el-button @click="resetStyle">恢复默认</el-button>
          <el-button type="primary" @click="styleDrawerVisible = false">完成</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

type ThemeName = "aurora" | "midnight" | "minimal" | "neon";
type DensityName = "compact" | "balanced" | "airy";

type UiSettings = {
  theme: ThemeName;
  density: DensityName;
  motionLevel: 0 | 1 | 2;
  glassmorphism: boolean;
};

const STORAGE_KEY = "agent_eval_ui_settings";
const styleDrawerVisible = ref(false);
const uiSettings = ref<UiSettings>({
  theme: "aurora",
  density: "balanced",
  motionLevel: 1,
  glassmorphism: true,
});

const themeOptions = [
  { label: "琥珀清透", value: "aurora" },
  { label: "深空暗影", value: "midnight" },
  { label: "极简素雅", value: "minimal" },
  { label: "霓虹未来", value: "neon" },
];

const appToneClass = computed(() => [
  `theme-${uiSettings.value.theme}`,
  `density-${uiSettings.value.density}`,
  `motion-${uiSettings.value.motionLevel}`,
  uiSettings.value.glassmorphism ? "glass-on" : "glass-off",
]);

const applyBodyClasses = () => {
  document.body.classList.remove(
    "theme-aurora",
    "theme-midnight",
    "theme-minimal",
    "theme-neon",
    "density-compact",
    "density-balanced",
    "density-airy",
    "motion-0",
    "motion-1",
    "motion-2",
    "glass-on",
    "glass-off"
  );
  document.body.classList.add(...appToneClass.value);
};

const loadSettings = () => {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw) as Partial<UiSettings>;
    uiSettings.value = {
      theme: parsed.theme ?? "aurora",
      density: parsed.density ?? "balanced",
      motionLevel: parsed.motionLevel ?? 1,
      glassmorphism: parsed.glassmorphism ?? true,
    };
  } catch {
    uiSettings.value = {
      theme: "aurora",
      density: "balanced",
      motionLevel: 1,
      glassmorphism: true,
    };
  }
};

const resetStyle = () => {
  uiSettings.value = {
    theme: "aurora",
    density: "balanced",
    motionLevel: 1,
    glassmorphism: true,
  };
};

const formatMotionTip = (value: number) => {
  if (value === 0) return "克制";
  if (value === 1) return "均衡";
  return "灵动";
};

onMounted(() => {
  loadSettings();
  applyBodyClasses();
});

watch(
  uiSettings,
  (nextValue) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextValue));
    applyBodyClasses();
  },
  { deep: true }
);
</script>
