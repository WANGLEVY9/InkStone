import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, GraphChart, HeatmapChart, LineChart, PieChart, RadarChart } from "echarts/charts";
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent, VisualMapComponent } from "echarts/components";

import App from "./App.vue";
import router from "./router";
import "./styles.css";

use([CanvasRenderer, BarChart, GraphChart, HeatmapChart, LineChart, PieChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, RadarComponent, VisualMapComponent]);

const app = createApp(App);
app.component("v-chart", VChart);
app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.mount("#app");
