<script setup name="myworkflow">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import OAMain from "@/components/OAMain.vue";
import OADialog from "@/components/OADialog.vue";
import OAPagination from "@/components/OAPagination.vue";
import workflowHttp from "@/api/workflowHttp";
import timeFormatter from "@/utils/timeFormatter";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const requests = ref([]);
const categories = ref([]);
const loading = ref(false);
const submitting = ref(false);
const uploading = ref(false);
const dialogVisible = ref(false);
const formRef = ref();

const pagination = reactive({
  page: 1,
  total: 0,
  size: 10,
});

const filters = reactive({
  status: "",
  category: "",
  keyword: "",
});

const requestForm = reactive({
  title: "",
  category_id: null,
  priority: "normal",
  content: "",
  amount: null,
  date_range: [],
  attachment_url: "",
});

const selectedCategory = computed(() =>
  categories.value.find((item) => item.id === requestForm.category_id),
);

const needsAmount = computed(() => selectedCategory.value?.field_schema === "amount");
const needsDateRange = computed(() => selectedCategory.value?.field_schema === "date_range");

const rules = reactive({
  title: [{ required: true, message: "Please enter the request title.", trigger: "blur" }],
  category_id: [{ required: true, message: "Please select a workflow type.", trigger: "change" }],
  content: [{ required: true, message: "Please describe the request.", trigger: "blur" }],
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
    draft: "info",
    pending: "warning",
    approved: "success",
    rejected: "danger",
    withdrawn: "info",
  };
  return map[status] || "info";
};

const priorityTag = (priority) => {
  const map = {
    low: "info",
    normal: "primary",
    high: "warning",
    urgent: "danger",
  };
  return map[priority] || "info";
};

async function fetchRequests(page = pagination.page) {
  loading.value = true;
  try {
    const data = await workflowHttp.getRequests({
      scope: "mine",
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

function resetForm() {
  requestForm.title = "";
  requestForm.category_id = null;
  requestForm.priority = "normal";
  requestForm.content = "";
  requestForm.amount = null;
  requestForm.date_range = [];
  requestForm.attachment_url = "";
}

function showCreateDialog() {
  resetForm();
  dialogVisible.value = true;
}

function resetFilters() {
  filters.status = "";
  filters.category = "";
  filters.keyword = "";
  fetchRequests(1);
}

async function uploadAttachment({ file }) {
  if (file.size > 25 * 1024 * 1024) {
    ElMessage.error("File size cannot exceed 25MB.");
    return;
  }
  uploading.value = true;
  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await fetch(`${import.meta.env.VITE_BASE_URL}/inform/file/upload`, {
      method: "POST",
      headers: { Authorization: "JWT " + authStore.token },
      body: formData,
    });
    const data = await res.json();
    if (data.errno !== 0) {
      ElMessage.error(data.message || "Attachment upload failed.");
      return;
    }
    requestForm.attachment_url = import.meta.env.VITE_BASE_URL + data.data.url;
    ElMessage.success("Attachment uploaded.");
  } catch {
    ElMessage.error("Attachment upload failed.");
  } finally {
    uploading.value = false;
  }
}

async function submitRequest() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    if (needsAmount.value && !requestForm.amount) {
      ElMessage.error("Amount is required for this request type.");
      return;
    }
    if (needsDateRange.value && requestForm.date_range.length !== 2) {
      ElMessage.error("Start date and end date are required.");
      return;
    }

    submitting.value = true;
    try {
      await workflowHttp.createRequest({
        title: requestForm.title,
        category_id: requestForm.category_id,
        priority: requestForm.priority,
        content: requestForm.content,
        amount: needsAmount.value ? requestForm.amount : null,
        start_date: needsDateRange.value ? requestForm.date_range[0] : null,
        end_date: needsDateRange.value ? requestForm.date_range[1] : null,
        attachment_url: requestForm.attachment_url,
      });
      ElMessage.success("Workflow request submitted.");
      dialogVisible.value = false;
      fetchRequests(1);
    } catch (detail) {
      ElMessage.error(detail);
    } finally {
      submitting.value = false;
    }
  });
}

async function withdrawRequest(row) {
  try {
    await ElMessageBox.confirm(`Withdraw "${row.title}"?`, "Confirm Withdraw", {
      type: "warning",
    });
    await workflowHttp.withdrawRequest(row.id, "Withdrawn by applicant.");
    ElMessage.success("Request withdrawn.");
    fetchRequests();
  } catch (err) {
    if (err !== "cancel") ElMessage.error(err);
  }
}

function onSearch() {
  fetchRequests(1);
}

function onStatusTab(value) {
  filters.status = value;
  fetchRequests(1);
}

watch(() => pagination.page, (page) => fetchRequests(page));

onMounted(async () => {
  try {
    categories.value = await workflowHttp.getCategories();
    if (route.query.status) {
      filters.status = route.query.status;
    }
    await fetchRequests(1);
    if (route.query.create === "1") {
      showCreateDialog();
      router.replace({ name: "myabsent", query: { ...route.query, create: undefined } });
    }
  } catch (detail) {
    ElMessage.error(detail);
  }
});
</script>

<template>
  <OAMain title="My Requests" subtitle="Create, track, and withdraw your workflow submissions.">
    <template #actions>
      <el-button type="primary" icon="Plus" @click="showCreateDialog">New Request</el-button>
    </template>

    <el-card class="oa-panel oa-filter-card">
      <el-tabs v-model="filters.status" @tab-change="onStatusTab">
        <el-tab-pane v-for="item in statusOptions" :key="item.value" :label="item.label" :name="item.value" />
      </el-tabs>
      <el-form class="oa-filter-form" :inline="true">
        <el-form-item label="Type">
          <el-select v-model="filters.category" clearable style="width: 190px">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Keyword">
          <el-input v-model="filters.keyword" clearable placeholder="Title" @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="onSearch">Search</el-button>
          <el-button icon="RefreshLeft" @click="resetFilters">Reset</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="oa-panel">
      <el-table v-loading="loading" :data="requests" empty-text="No workflow requests yet.">
        <el-table-column prop="title" label="Title" min-width="200">
          <template #default="{ row }">
            <router-link :to="{ name: 'workflow_detail', params: { id: row.id } }">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column label="Type" min-width="150">
          <template #default="{ row }">{{ row.category?.name }}</template>
        </el-table-column>
        <el-table-column label="Priority" width="110">
          <template #default="{ row }">
            <el-tag :type="priorityTag(row.priority)" effect="light">{{ row.priority_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="light">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Approver" min-width="150">
          <template #default="{ row }">{{ row.approver?.realname || "-" }}</template>
        </el-table-column>
        <el-table-column label="Created" width="170">
          <template #default="{ row }">{{ timeFormatter.stringFromDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="Action" width="170" fixed="right">
          <template #default="{ row }">
            <div class="oa-table-actions">
              <el-button type="primary" size="small" plain @click="$router.push({ name: 'workflow_detail', params: { id: row.id } })">
                View
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                type="warning"
                size="small"
                @click="withdrawRequest(row)"
              >
                Withdraw
              </el-button>
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
    title="New Workflow Request"
    v-model="dialogVisible"
    width="680"
    :submitting="submitting"
    @submit="submitRequest"
  >
    <el-form ref="formRef" :model="requestForm" :rules="rules" label-width="130px">
      <el-form-item label="Title" prop="title">
        <el-input v-model="requestForm.title" placeholder="Please enter a clear request title" />
      </el-form-item>
      <el-form-item label="Type" prop="category_id">
        <el-select v-model="requestForm.category_id" style="width: 100%" placeholder="Select workflow type">
          <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="Priority">
        <el-select v-model="requestForm.priority" style="width: 100%">
          <el-option label="Low" value="low" />
          <el-option label="Normal" value="normal" />
          <el-option label="High" value="high" />
          <el-option label="Urgent" value="urgent" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="needsDateRange" label="Date Range">
        <el-date-picker
          v-model="requestForm.date_range"
          type="daterange"
          start-placeholder="Start date"
          end-placeholder="End date"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item v-if="needsAmount" label="Amount">
        <el-input-number v-model="requestForm.amount" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item label="Attachment">
        <div class="attachment-row">
          <el-upload :show-file-list="false" :http-request="uploadAttachment">
            <el-button :loading="uploading" icon="Upload">Upload File</el-button>
          </el-upload>
          <a v-if="requestForm.attachment_url" :href="requestForm.attachment_url" target="_blank">Open uploaded file</a>
          <span v-else class="oa-muted">Optional, up to 25MB</span>
        </div>
      </el-form-item>
      <el-form-item label="Description" prop="content">
        <el-input v-model="requestForm.content" type="textarea" :rows="5" placeholder="Describe the business reason and details" />
      </el-form-item>
    </el-form>
  </OADialog>
</template>

<style scoped>
.el-card {
  margin-bottom: 16px;
}

.attachment-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

:deep(.el-tabs__header) {
  margin-bottom: 14px;
}
</style>
