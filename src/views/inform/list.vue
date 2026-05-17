<script setup name="informlist">
import { onMounted, reactive, ref, watch } from "vue";
import OAMain from "@/components/OAMain.vue";
import OADialog from "@/components/OADialog.vue";
import OAPagination from "@/components/OAPagination.vue";
import timeFormatter from "@/utils/timeFormatter";
import { useAuthStore } from "@/stores/auth";
import informHttp from "@/api/informHttp";
import { ElMessage } from "element-plus";

const authStore = useAuthStore();
const informs = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const activeInform = ref(null);

const pagination = reactive({
  page: 1,
  total: 0,
  size: 10,
});

const filters = reactive({
  keyword: "",
  read: "",
});

async function fetchInforms(page = pagination.page) {
  loading.value = true;
  try {
    const data = await informHttp.getInformList(page, {
      size: pagination.size,
      keyword: filters.keyword,
      read: filters.read,
    });
    pagination.total = data.total;
    pagination.page = data.page;
    pagination.size = data.size || pagination.size;
    informs.value = data.items;
  } catch (detail) {
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.keyword = "";
  filters.read = "";
  fetchInforms(1);
}

const onShowDialog = (row) => {
  activeInform.value = row;
  dialogVisible.value = true;
};

const onDeleteInform = async () => {
  if (!activeInform.value) return;
  try {
    await informHttp.deleteInform(activeInform.value.id);
    dialogVisible.value = false;
    ElMessage.success("Notification deleted successfully.");
    fetchInforms(pagination.page);
  } catch (detail) {
    ElMessage.error(detail);
  }
};

watch(() => pagination.page, (newPage) => fetchInforms(newPage));

onMounted(() => fetchInforms(1));
</script>

<template>
  <OADialog v-model="dialogVisible" title="Delete Notification" @submit="onDeleteInform">
    <span>Delete "{{ activeInform?.title }}"? This action cannot be undone.</span>
  </OADialog>

  <OAMain title="Notification List" subtitle="Search, read, and manage visible announcements.">
    <template #actions>
      <el-button type="primary" icon="Promotion" @click="$router.push({ name: 'inform_publish' })">
        Publish Notification
      </el-button>
    </template>

    <el-card class="oa-panel oa-filter-card">
      <el-form class="oa-filter-form" :inline="true">
        <el-form-item label="Keyword">
          <el-input v-model="filters.keyword" clearable placeholder="Title, content, or publisher" style="width: 260px" @keyup.enter="fetchInforms(1)" />
        </el-form-item>
        <el-form-item label="Read State">
          <el-select v-model="filters.read" clearable style="width: 160px">
            <el-option label="Read" value="read" />
            <el-option label="Unread" value="unread" />
          </el-select>
        </el-form-item>
        <el-form-item label="Page Size">
          <el-select v-model="pagination.size" style="width: 130px" @change="fetchInforms(1)">
            <el-option label="10 / page" :value="10" />
            <el-option label="20 / page" :value="20" />
            <el-option label="50 / page" :value="50" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="fetchInforms(1)">Search</el-button>
          <el-button icon="RefreshLeft" @click="resetFilters">Reset</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="oa-panel">
      <el-table v-loading="loading" :data="informs" empty-text="No notifications found.">
        <el-table-column label="Title" min-width="240">
          <template #default="{ row }">
            <div class="title-cell">
              <el-tag v-if="row.is_top" type="danger" effect="dark" size="small">Top</el-tag>
              <el-badge v-if="row.reads.length === 0" is-dot>
                <RouterLink :to="{ name: 'inform_detail', params: { pk: row.id } }">{{ row.title }}</RouterLink>
              </el-badge>
              <RouterLink v-else :to="{ name: 'inform_detail', params: { pk: row.id } }">{{ row.title }}</RouterLink>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Publisher" min-width="170">
          <template #default="{ row }">
            {{ "[" + (row.author.department?.name || "-") + "] " + row.author.realname }}
          </template>
        </el-table-column>
        <el-table-column label="Published" width="170">
          <template #default="{ row }">
            {{ timeFormatter.stringFromDateTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="Visibility" min-width="180">
          <template #default="{ row }">
            <el-tag v-if="row.public" type="success" effect="light">All Departments</el-tag>
            <el-tag v-else v-for="department in row.departments" :key="department.id" type="info" effect="light" class="dept-tag">
              {{ department.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Read" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.reads.length > 0" type="success" effect="light">Read</el-tag>
            <el-tag v-else type="danger" effect="light">Unread</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Action" width="130" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.author.id === authStore.user.id || authStore.user.is_superuser"
              @click="onShowDialog(row)"
              type="danger"
              icon="Delete"
              circle
            />
            <el-button v-else disabled type="default" size="small">None</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <OAPagination v-model="pagination.page" :total="pagination.total" :page-size="pagination.size" />
      </template>
    </el-card>
  </OAMain>
</template>

<style scoped>
.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.dept-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}
</style>
