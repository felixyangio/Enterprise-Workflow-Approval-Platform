<script setup name="approvaltodo">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import OAMain from "@/components/OAMain.vue";
import OADialog from "@/components/OADialog.vue";
import OAPagination from "@/components/OAPagination.vue";
import workflowHttp from "@/api/workflowHttp";
import timeFormatter from "@/utils/timeFormatter";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const requests = ref([]);
const categories = ref([]);
const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const decisionFormRef = ref();
let activeRequest = null;

const pagination = reactive({
  page: 1,
  total: 0,
  size: 10,
});

const filters = reactive({
  scope: "todo",
  status: "",
  category: "",
  keyword: "",
});

const decisionForm = reactive({
  action: "approve",
  comment: "",
});

const rules = reactive({
  action: [{ required: true, message: "Please select a decision.", trigger: "change" }],
  comment: [{ required: true, message: "Please provide an approval comment.", trigger: "blur" }],
});

const statusOptions = [
  { label: "All", value: "" },
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
  { label: "Withdrawn", value: "withdrawn" },
];

const statusTag = (status) => {
  const map = {
    pending: "warning",
    approved: "success",
    rejected: "danger",
    withdrawn: "info",
  };
  return map[status] || "info";
};

async function fetchRequests(page = pagination.page) {
  loading.value = true;
  try {
    const data = await workflowHttp.getRequests({
      scope: filters.scope,
      page,
      size: pagination.size,
      status: filters.status,
      category: filters.category,
      keyword: filters.keyword,
    });
    requests.value = data.items || data.results || [];
    pagination.total = data.total || data.count || 0;
    pagination.page = data.page || page;
  } catch (detail) {
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  fetchRequests(1);
}

function resetFilters() {
  filters.status = "";
  filters.category = "";
  filters.keyword = "";
  fetchRequests(1);
}

function showDecisionDialog(row, action = "approve") {
  activeRequest = row;
  decisionForm.action = action;
  decisionForm.comment = "";
  dialogVisible.value = true;
}

async function submitDecision() {
  await decisionFormRef.value.validate(async (valid) => {
    if (!valid || !activeRequest) return;
    submitting.value = true;
    try {
      if (decisionForm.action === "approve") {
        await workflowHttp.approveRequest(activeRequest.id, decisionForm.comment);
      } else {
        await workflowHttp.rejectRequest(activeRequest.id, decisionForm.comment);
      }
      ElMessage.success("Workflow request processed.");
      dialogVisible.value = false;
      fetchRequests();
    } catch (detail) {
      ElMessage.error(detail);
    } finally {
      submitting.value = false;
    }
  });
}

watch(() => pagination.page, (page) => fetchRequests(page));

onMounted(async () => {
  try {
    categories.value = await workflowHttp.getCategories();
    await fetchRequests(1);
  } catch (detail) {
    ElMessage.error(detail);
  }
});
</script>

<template>
  <OAMain title="Approval Todo" subtitle="Review pending workflow requests and audit processed items.">
    <el-card class="oa-panel oa-filter-card">
      <el-form class="oa-filter-form" :inline="true">
        <el-form-item label="View">
          <el-select v-model="filters.scope" style="width: 160px" @change="onSearch">
            <el-option label="Todo" value="todo" />
            <el-option v-if="authStore.user.is_superuser" label="All Requests" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="Status">
          <el-select v-model="filters.status" clearable style="width: 150px">
            <el-option v-for="item in statusOptions.slice(1)" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="Type">
          <el-select v-model="filters.category" clearable style="width: 190px">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Keyword">
          <el-input v-model="filters.keyword" clearable placeholder="Title or applicant" @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="onSearch">Search</el-button>
          <el-button icon="RefreshLeft" @click="resetFilters">Reset</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="oa-panel">
      <el-table v-loading="loading" :data="requests" empty-text="No approval work items.">
        <el-table-column label="Title" min-width="190">
          <template #default="{ row }">
            <router-link :to="{ name: 'workflow_detail', params: { id: row.id } }">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column label="Applicant" min-width="170">
          <template #default="{ row }">
            {{ "[" + (row.applicant?.department?.name || "-") + "] " + row.applicant?.realname }}
          </template>
        </el-table-column>
        <el-table-column label="Type" min-width="150">
          <template #default="{ row }">{{ row.category?.name }}</template>
        </el-table-column>
        <el-table-column label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="light">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Created" width="170">
          <template #default="{ row }">{{ timeFormatter.stringFromDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="Action" width="230" fixed="right">
          <template #default="{ row }">
            <div class="oa-table-actions">
              <el-button type="primary" size="small" plain @click="$router.push({ name: 'workflow_detail', params: { id: row.id } })">
                View
              </el-button>
              <template v-if="row.status === 'pending'">
                <el-button type="success" size="small" @click="showDecisionDialog(row, 'approve')">Approve</el-button>
                <el-button type="danger" size="small" @click="showDecisionDialog(row, 'reject')">Reject</el-button>
              </template>
              <el-button v-else disabled size="small">Closed</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <OAPagination v-model="pagination.page" :total="pagination.total" :page-size="pagination.size" />
      </template>
    </el-card>
  </OAMain>

  <OADialog
    title="Process Workflow Request"
    v-model="dialogVisible"
    :submitting="submitting"
    @submit="submitDecision"
  >
    <el-form ref="decisionFormRef" :model="decisionForm" :rules="rules" label-width="100px">
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
.el-card {
  margin-bottom: 16px;
}
</style>
