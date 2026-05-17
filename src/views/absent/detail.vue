<script setup name="workflowdetail">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import OAMain from "@/components/OAMain.vue";
import OADialog from "@/components/OADialog.vue";
import workflowHttp from "@/api/workflowHttp";
import timeFormatter from "@/utils/timeFormatter";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const submitting = ref(false);
const decisionVisible = ref(false);
const decisionRef = ref();
const decisionForm = reactive({
  action: "approve",
  comment: "",
});
const request = reactive({
  id: null,
  title: "",
  category: {},
  applicant: { department: {} },
  approver: {},
  status: "",
  status_display: "",
  priority_display: "",
  content: "",
  amount: null,
  start_date: "",
  end_date: "",
  attachment_url: "",
  response_content: "",
  created_at: "",
  updated_at: "",
  logs: [],
});

const rules = reactive({
  action: [{ required: true, message: "Please select a decision.", trigger: "change" }],
  comment: [{ required: true, message: "Please provide a comment.", trigger: "blur" }],
});

const canProcess = computed(() =>
  request.status === "pending"
  && request.applicant?.id !== authStore.user.id
  && (authStore.user.is_superuser || request.approver?.id === authStore.user.id),
);

const canWithdraw = computed(() =>
  request.status === "pending" && request.applicant?.id === authStore.user.id,
);

const statusTag = (status) => {
  const map = {
    pending: "warning",
    approved: "success",
    rejected: "danger",
    withdrawn: "info",
  };
  return map[status] || "info";
};

const actionTag = (action) => {
  const map = {
    submit: "primary",
    approve: "success",
    reject: "danger",
    withdraw: "warning",
  };
  return map[action] || "info";
};

async function fetchDetail() {
  loading.value = true;
  try {
    const data = await workflowHttp.getRequestDetail(route.params.id);
    Object.assign(request, data);
  } catch (detail) {
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
}

function openDecision(action) {
  decisionForm.action = action;
  decisionForm.comment = "";
  decisionVisible.value = true;
}

async function submitDecision() {
  await decisionRef.value.validate(async (valid) => {
    if (!valid) return;
    submitting.value = true;
    try {
      if (decisionForm.action === "approve") {
        await workflowHttp.approveRequest(request.id, decisionForm.comment);
      } else {
        await workflowHttp.rejectRequest(request.id, decisionForm.comment);
      }
      ElMessage.success("Workflow request processed.");
      decisionVisible.value = false;
      fetchDetail();
    } catch (detail) {
      ElMessage.error(detail);
    } finally {
      submitting.value = false;
    }
  });
}

async function withdrawRequest() {
  try {
    await ElMessageBox.confirm(`Withdraw "${request.title}"?`, "Confirm Withdraw", { type: "warning" });
    await workflowHttp.withdrawRequest(request.id, "Withdrawn by applicant.");
    ElMessage.success("Request withdrawn.");
    fetchDetail();
  } catch (err) {
    if (err !== "cancel") ElMessage.error(err);
  }
}

onMounted(fetchDetail);
</script>

<template>
  <OAMain title="Workflow Request Detail" subtitle="Review request metadata, content, and approval timeline.">
    <template #actions>
      <el-button icon="Back" @click="router.go(-1)">Back</el-button>
      <template v-if="canProcess">
        <el-button type="success" icon="CircleCheck" @click="openDecision('approve')">Approve</el-button>
        <el-button type="danger" icon="CircleClose" @click="openDecision('reject')">Reject</el-button>
      </template>
      <el-button v-if="canWithdraw" type="warning" icon="RefreshLeft" @click="withdrawRequest">Withdraw</el-button>
    </template>

    <el-card class="oa-panel" v-loading="loading">
      <template #header>
        <div class="detail-header">
          <div>
            <h2>{{ request.title }}</h2>
            <p>{{ request.category?.name }} / {{ timeFormatter.stringFromDateTime(request.created_at) }}</p>
          </div>
          <el-tag :type="statusTag(request.status)" size="large" effect="light">{{ request.status_display }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="Applicant">{{ request.applicant?.realname }}</el-descriptions-item>
        <el-descriptions-item label="Department">{{ request.applicant?.department?.name || "-" }}</el-descriptions-item>
        <el-descriptions-item label="Approver">{{ request.approver?.realname || "-" }}</el-descriptions-item>
        <el-descriptions-item label="Priority">{{ request.priority_display }}</el-descriptions-item>
        <el-descriptions-item v-if="request.start_date || request.end_date" label="Date Range">
          {{ request.start_date || "-" }} to {{ request.end_date || "-" }}
        </el-descriptions-item>
        <el-descriptions-item v-if="request.amount" label="Amount">{{ request.amount }}</el-descriptions-item>
        <el-descriptions-item v-if="request.attachment_url" label="Attachment">
          <a :href="request.attachment_url" target="_blank">Open attachment</a>
        </el-descriptions-item>
        <el-descriptions-item label="Last Response">{{ request.response_content || "-" }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />
      <h3>Request Content</h3>
      <p class="content">{{ request.content || "-" }}</p>

      <el-divider />
      <h3>Approval Timeline</h3>
      <el-timeline>
        <el-timeline-item
          v-for="log in request.logs"
          :key="log.id"
          :timestamp="timeFormatter.stringFromDateTime(log.created_at)"
        >
          <el-tag :type="actionTag(log.action)" effect="light">{{ log.action_display }}</el-tag>
          <span class="log-actor">{{ log.actor?.realname || "System" }}</span>
          <p class="log-comment">{{ log.comment || "-" }}</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </OAMain>

  <OADialog title="Process Workflow Request" v-model="decisionVisible" :submitting="submitting" @submit="submitDecision">
    <el-form ref="decisionRef" :model="decisionForm" :rules="rules" label-width="100px">
      <el-form-item label="Decision" prop="action">
        <el-segmented
          v-model="decisionForm.action"
          :options="[
            { label: 'Approve', value: 'approve' },
            { label: 'Reject', value: 'reject' },
          ]"
        />
      </el-form-item>
      <el-form-item label="Comment" prop="comment">
        <el-input v-model="decisionForm.comment" type="textarea" :rows="4" placeholder="Add a clear audit comment" />
      </el-form-item>
    </el-form>
  </OADialog>
</template>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.detail-header h2 {
  margin: 0 0 8px;
}

.detail-header p,
.log-comment {
  margin: 0;
  color: #667085;
}

.content {
  white-space: pre-wrap;
  line-height: 1.7;
}

.log-actor {
  margin-left: 8px;
  font-weight: 700;
}

@media (max-width: 768px) {
  .detail-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
