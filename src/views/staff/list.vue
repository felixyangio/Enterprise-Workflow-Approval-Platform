<script setup name="stafflist">
import OAMain from "@/components/OAMain.vue";
import { ref, reactive, onMounted, watch } from "vue";
import timeFormatter from "@/utils/timeFormatter";
import staffHttp from "@/api/staffHttp";
import { ElMessage } from "element-plus";
import OADialog from "@/components/OADialog.vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const staffs = ref([]);
const selectedStaffs = ref([]);
const departments = ref([]);
const loading = ref(false);
const exporting = ref(false);
const dialogVisible = ref(false);
const deleteDialogVisible = ref(false);
const activeStaff = ref(null);

const pagination = reactive({
  page: 1,
  total: 0,
});
const pageSize = ref(10);
const staffForm = reactive({
  status: 1,
});
const filterForm = reactive({
  department_id: null,
  status: "",
  realname: "",
  date_joined: [],
});

async function fetchStaffList(page = pagination.page, size = pageSize.value) {
  loading.value = true;
  try {
    const data = await staffHttp.getStaffList(page, size, filterForm);
    pagination.total = data.total;
    pagination.page = page;
    staffs.value = data.items;
  } catch (detail) {
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  fetchStaffList(1, pageSize.value);
  try {
    departments.value = await staffHttp.getAllDepartment();
  } catch (detail) {
    ElMessage.error(detail);
  }
});

watch(() => pagination.page, (value) => fetchStaffList(value, pageSize.value));

watch(pageSize, (value) => {
  if (pagination.page === 1) {
    fetchStaffList(1, value);
  } else {
    pagination.page = 1;
  }
});

const onEditStaff = (row) => {
  activeStaff.value = row;
  dialogVisible.value = true;
  staffForm.status = row.status;
};

const onSubmitEditStaff = async () => {
  if (!activeStaff.value) return;
  try {
    const newStaff = await staffHttp.updateStaffStatus(activeStaff.value.id, staffForm.status);
    ElMessage.success("Employee status updated successfully.");
    dialogVisible.value = false;
    const index = staffs.value.findIndex((item) => item.id === activeStaff.value.id);
    if (index >= 0) staffs.value.splice(index, 1, newStaff);
  } catch (detail) {
    ElMessage.error(detail);
  }
};

const onSearch = () => {
  fetchStaffList(1, pageSize.value);
};

const onReset = () => {
  filterForm.department_id = null;
  filterForm.status = "";
  filterForm.realname = "";
  filterForm.date_joined = [];
  fetchStaffList(1, pageSize.value);
};

const onShowDeleteDialog = (row) => {
  activeStaff.value = row;
  deleteDialogVisible.value = true;
};

const onDeleteStaff = async () => {
  if (!activeStaff.value) return;
  try {
    await staffHttp.deleteStaff(activeStaff.value.id);
    deleteDialogVisible.value = false;
    ElMessage.success("Employee deleted successfully.");
    fetchStaffList(pagination.page, pageSize.value);
  } catch (detail) {
    ElMessage.error(detail);
  }
};

const onSelectionChange = (rows) => {
  selectedStaffs.value = rows;
};

async function exportSelectedStaffs() {
  if (!selectedStaffs.value.length) {
    ElMessage.info("Please select at least one employee.");
    return;
  }
  exporting.value = true;
  try {
    const response = await staffHttp.downloadStaffs(selectedStaffs.value.map((item) => item.id));
    const blob = new Blob([response.data], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "employees.csv";
    link.click();
    URL.revokeObjectURL(url);
    ElMessage.success("Employee CSV exported.");
  } catch (detail) {
    ElMessage.error(detail);
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <OADialog title="Update Employee Status" v-model="dialogVisible" @submit="onSubmitEditStaff">
    <el-form :model="staffForm" label-width="100px">
      <el-form-item label="Status">
        <el-radio-group v-model="staffForm.status">
          <el-radio :value="1">Active</el-radio>
          <el-radio :value="3">Locked</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </OADialog>

  <OADialog title="Confirm Delete" v-model="deleteDialogVisible" @submit="onDeleteStaff">
    <span>Delete "{{ activeStaff?.realname }}"? This action cannot be undone.</span>
  </OADialog>

  <OAMain title="Employee List" subtitle="Search staff records, manage status, and export selected employees.">
    <template #actions>
      <el-button type="primary" icon="Plus" @click="$router.push({ name: 'staff_add' })">Add Employee</el-button>
      <el-button
        v-if="authStore.user.is_superuser"
        icon="Download"
        :loading="exporting"
        :disabled="selectedStaffs.length === 0"
        @click="exportSelectedStaffs"
      >
        Export Selected
      </el-button>
    </template>

    <el-card class="oa-panel oa-filter-card">
      <el-form class="oa-filter-form" :inline="true">
        <el-form-item label="Department">
          <el-select v-model="filterForm.department_id" clearable style="width: 170px">
            <el-option v-for="department in departments" :label="department.name" :value="department.id" :key="department.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Status">
          <el-select v-model="filterForm.status" clearable style="width: 140px">
            <el-option label="Active" :value="1" />
            <el-option label="Inactive" :value="0" />
            <el-option label="Locked" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="Name">
          <el-input v-model="filterForm.realname" placeholder="Employee name" style="width: 170px" @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="Join Date">
          <el-date-picker
            v-model="filterForm.date_joined"
            type="daterange"
            range-separator="to"
            start-placeholder="Start Date"
            end-placeholder="End Date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="onSearch">Search</el-button>
          <el-button icon="RefreshLeft" @click="onReset">Reset</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="oa-panel">
      <el-table v-loading="loading" :data="staffs" empty-text="No employees found." @selection-change="onSelectionChange">
        <el-table-column v-if="authStore.user.is_superuser" type="selection" width="55" />
        <el-table-column label="No." width="70">
          <template #default="{ $index }">{{ (pagination.page - 1) * pageSize + $index + 1 }}</template>
        </el-table-column>
        <el-table-column prop="realname" label="Name" min-width="140" />
        <el-table-column prop="email" label="Email" min-width="220" />
        <el-table-column label="Join Date" width="130">
          <template #default="{ row }">
            {{ row.date_joined ? timeFormatter.stringFromDate(row.date_joined) : "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="department.name" label="Department" min-width="150" />
        <el-table-column label="Status" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="success" effect="light">Active</el-tag>
            <el-tag v-else-if="row.status === 0" type="warning" effect="light">Inactive</el-tag>
            <el-tag v-else type="danger" effect="light">Locked</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="130" fixed="right">
          <template #default="{ row }">
            <div class="oa-table-actions">
              <el-button v-if="authStore.user.is_superuser" type="primary" icon="Edit" circle @click="onEditStaff(row)" />
              <el-button v-if="authStore.user.is_superuser" type="danger" icon="Delete" circle @click="onShowDeleteDialog(row)" />
            </div>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <div class="table-footer">
          <el-form-item label="Items per page:">
            <el-select v-model="pageSize" size="small" style="width: 120px">
              <el-option label="10 / page" :value="10" />
              <el-option label="20 / page" :value="20" />
              <el-option label="50 / page" :value="50" />
            </el-select>
          </el-form-item>
          <el-pagination background layout="total, prev, pager, next" :total="pagination.total" v-model:currentPage="pagination.page" :page-size="pageSize" />
        </div>
      </template>
    </el-card>
  </OAMain>
</template>

<style scoped>
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.table-footer .el-form-item {
  margin-bottom: 0;
}
</style>
