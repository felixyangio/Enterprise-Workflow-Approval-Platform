<script setup name="home">
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import timeFormatter from "@/utils/timeFormatter";
import OAMain from "@/components/OAMain.vue";
import homeHttp from "@/api/homeHttp";
import { PermissionChoices, useAuthStore } from "@/stores/auth";
import * as echarts from "echarts";

const router = useRouter();
const authStore = useAuthStore();
const informs = ref([]);
const workflows = ref([]);
const loading = ref(false);
const chartEl = ref();
let chart = null;

const summary = ref({
  todo: 0,
  my_pending: 0,
  my_approved: 0,
  my_rejected: 0,
  total_visible: 0,
});

const metricCards = computed(() => [
  {
    label: "Approval Todo",
    value: summary.value.todo,
    icon: "Stamp",
    route: { name: "subabsent" },
    tone: "blue",
    visible: authStore.has_permission([PermissionChoices.Superuser], "|"),
  },
  {
    label: "My Pending",
    value: summary.value.my_pending,
    icon: "Clock",
    route: { name: "myabsent", query: { status: "pending" } },
    tone: "amber",
    visible: true,
  },
  {
    label: "My Approved",
    value: summary.value.my_approved,
    icon: "CircleCheck",
    route: { name: "myabsent", query: { status: "approved" } },
    tone: "green",
    visible: true,
  },
  {
    label: "Visible Requests",
    value: summary.value.total_visible,
    icon: "DataAnalysis",
    route: { name: "myabsent" },
    tone: "violet",
    visible: true,
  },
].filter((item) => item.visible));

const quickActions = computed(() => [
  { label: "New Request", icon: "Plus", route: { name: "myabsent", query: { create: "1" } }, visible: true },
  {
    label: "Approval Todo",
    icon: "Finished",
    route: { name: "subabsent" },
    visible: authStore.has_permission([PermissionChoices.Superuser], "|"),
  },
  {
    label: "Publish Notification",
    icon: "Promotion",
    route: { name: "inform_publish" },
    visible: authStore.has_permission([PermissionChoices.Boarder, PermissionChoices.Leader], "|"),
  },
  {
    label: "Employee List",
    icon: "Avatar",
    route: { name: "staff_list" },
    visible: authStore.has_permission([PermissionChoices.Boarder, PermissionChoices.Leader, PermissionChoices.Superuser], "|"),
  },
].filter((item) => item.visible));

const statusTag = (status) => {
  const map = {
    pending: "warning",
    approved: "success",
    rejected: "danger",
    withdrawn: "info",
  };
  return map[status] || "info";
};

function goTo(route) {
  router.push(route);
}

function resizeChart() {
  chart?.resize();
}

function renderChart(rows) {
  if (!chartEl.value) return;
  chart = echarts.init(chartEl.value);
  chart.setOption({
    color: ["#2563eb"],
    tooltip: { trigger: "axis" },
    grid: { left: 36, right: 18, top: 24, bottom: 34 },
    xAxis: {
      type: "category",
      data: rows.map((row) => row.name),
      axisLine: { lineStyle: { color: "#d0d8e8" } },
      axisTick: { show: false },
      axisLabel: { color: "#667085" },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.24)" } },
      axisLabel: { color: "#667085" },
    },
    series: [
      {
        name: "Employees",
        type: "bar",
        barWidth: 28,
        data: rows.map((row) => row.staff_count),
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "#38bdf8" },
              { offset: 1, color: "#2563eb" },
            ],
          },
        },
      },
    ],
  });
}

onMounted(async () => {
  loading.value = true;
  try {
    const [latestInforms, latestWorkflows, workflowSummary, rows] = await Promise.all([
      homeHttp.getLatestInforms(),
      homeHttp.getLatestAbsents(),
      homeHttp.getWorkflowSummary(),
      homeHttp.getDepartmentStaffCount(),
    ]);
    informs.value = latestInforms;
    workflows.value = latestWorkflows;
    summary.value = workflowSummary;
    await nextTick();
    renderChart(rows);
    window.addEventListener("resize", resizeChart);
  } catch (detail) {
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener("resize", resizeChart);
  chart?.dispose();
});
</script>

<template>
  <OAMain title="Employee Workflow Portal" subtitle="A focused cockpit for approvals, announcements, and team operations.">
    <template #actions>
      <el-button
        v-for="action in quickActions"
        :key="action.label"
        type="primary"
        plain
        :icon="action.icon"
        @click="goTo(action.route)"
      >
        {{ action.label }}
      </el-button>
    </template>

    <div v-loading="loading">
      <div class="metric-grid">
        <button
          v-for="metric in metricCards"
          :key="metric.label"
          class="metric-card oa-panel"
          :class="`metric-card--${metric.tone}`"
          @click="goTo(metric.route)"
        >
          <span class="metric-card__icon">
            <el-icon><component :is="metric.icon" /></el-icon>
          </span>
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </button>
      </div>

      <el-card class="oa-panel chart-card">
        <template #header>
          <div class="oa-card-header">
            <h2>Department Staff Count</h2>
            <span class="oa-muted">Live team distribution</span>
          </div>
        </template>
        <div ref="chartEl" class="department-chart"></div>
      </el-card>

      <el-row :gutter="20">
        <el-col :xs="24" :lg="12">
          <el-card class="oa-panel">
            <template #header>
              <div class="oa-card-header">
                <h2>Latest Announcements</h2>
                <el-button text type="primary" @click="goTo({ name: 'inform_list' })">View all</el-button>
              </div>
            </template>
            <el-table :data="informs" empty-text="No announcements.">
              <el-table-column label="Title" min-width="180">
                <template #default="{ row }">
                  <router-link :to="{ name: 'inform_detail', params: { pk: row.id } }">{{ row.title }}</router-link>
                </template>
              </el-table-column>
              <el-table-column label="Publisher" width="130" prop="author.realname" />
              <el-table-column label="Read" width="90">
                <template #default="{ row }">
                  <el-tag v-if="row.reads.length > 0" type="success" effect="light">Read</el-tag>
                  <el-tag v-else type="danger" effect="light">Unread</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card class="oa-panel">
            <template #header>
              <div class="oa-card-header">
                <h2>Latest Workflow Requests</h2>
                <el-button text type="primary" @click="goTo({ name: 'myabsent' })">View mine</el-button>
              </div>
            </template>
            <el-table :data="workflows" empty-text="No workflow activity.">
              <el-table-column label="Title" min-width="180">
                <template #default="{ row }">
                  <router-link :to="{ name: 'workflow_detail', params: { id: row.id } }">{{ row.title }}</router-link>
                </template>
              </el-table-column>
              <el-table-column label="Type" width="130">
                <template #default="{ row }">{{ row.category?.name }}</template>
              </el-table-column>
              <el-table-column label="Status" width="110">
                <template #default="{ row }">
                  <el-tag :type="statusTag(row.status)" effect="light">{{ row.status_display }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="Created" width="120">
                <template #default="{ row }">
                  {{ timeFormatter.stringFromDate(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </OAMain>
</template>

<style scoped>
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.metric-card {
  position: relative;
  min-height: 136px;
  padding: 18px;
  text-align: left;
  border: 0;
  cursor: pointer;
  overflow: hidden;
}

.metric-card span {
  position: relative;
  display: block;
  color: #667085;
  font-size: 13px;
  font-weight: 700;
}

.metric-card strong {
  position: relative;
  display: block;
  margin-top: 12px;
  color: #102033;
  font-size: 34px;
  line-height: 1;
}

.metric-card__icon {
  width: 38px;
  height: 38px;
  display: grid !important;
  place-items: center;
  margin-bottom: 18px;
  border-radius: 8px;
  color: white !important;
  background: linear-gradient(135deg, #38bdf8, #2563eb);
}

.metric-card--amber .metric-card__icon {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}

.metric-card--green .metric-card__icon {
  background: linear-gradient(135deg, #14b8a6, #22c55e);
}

.metric-card--violet .metric-card__icon {
  background: linear-gradient(135deg, #6366f1, #2563eb);
}

.chart-card {
  margin-bottom: 18px;
}

.department-chart {
  width: 100%;
  height: 320px;
}

@media (max-width: 1180px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
