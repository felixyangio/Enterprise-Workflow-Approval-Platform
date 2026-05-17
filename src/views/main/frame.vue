<script setup name="frame">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { Expand, Fold } from "@element-plus/icons-vue";
import { useAuthStore } from "@/stores/auth";
import { useRoute, useRouter } from "vue-router";
import authHttp from "@/api/authHttp";
import { ElMessage } from "element-plus";
import routes from "@/router/frame";

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const displayUser = reactive({
  department: {},
  realname: "",
});
const defaultActive = ref("home");
const isCollapse = ref(false);
const isMobile = ref(false);
const dialogVisible = ref(false);
const formLabelWidth = "120px";
const resetPwdForm = reactive({
  oldpwd: "",
  pwd1: "",
  pwd2: "",
});
const formTag = ref();
const rules = reactive({
  oldpwd: [
    { required: true, message: "Please enter the old password.", trigger: "blur" },
    { min: 6, max: 20, message: "Password length must be between 6 and 20 characters.", trigger: "blur" },
  ],
  pwd1: [
    { required: true, message: "Please enter the new password.", trigger: "blur" },
    { min: 6, max: 20, message: "Password length must be between 6 and 20 characters.", trigger: "blur" },
  ],
  pwd2: [
    { required: true, message: "Please confirm the password.", trigger: "blur" },
    { min: 6, max: 20, message: "Password length must be between 6 and 20 characters.", trigger: "blur" },
  ],
});

const asideWidth = computed(() => (isCollapse.value ? "72px" : "260px"));

const visibleRoutes = computed(() =>
  routes[0].children.filter((item) => authStore.has_permission(item.meta.permissions, item.meta.opt)),
);

const breadcrumbs = computed(() =>
  route.matched
    .filter((item) => item.meta?.text)
    .map((item) => ({ name: item.name, text: item.meta.text })),
);

const currentTitle = computed(() => breadcrumbs.value[breadcrumbs.value.length - 1]?.text || "Home");

function syncActive() {
  defaultActive.value = route.name || "home";
}

function onResize() {
  isMobile.value = window.innerWidth <= 900;
  isCollapse.value = isMobile.value;
}

onMounted(() => {
  syncActive();
  displayUser.department = authStore.user.department || {};
  displayUser.realname = authStore.user.realname || "";
  onResize();
  window.addEventListener("resize", onResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", onResize);
});

watch(() => route.name, syncActive);

const onCollapseAside = () => {
  isCollapse.value = !isCollapse.value;
};

const onExit = () => {
  authStore.clearUserToken();
  router.push({ name: "login" });
};

const onControlResetPwdDialog = () => {
  resetPwdForm.oldpwd = "";
  resetPwdForm.pwd1 = "";
  resetPwdForm.pwd2 = "";
  dialogVisible.value = true;
};

const onSubmit = () => {
  formTag.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.info("Please fill in the required fields.");
      return;
    }
    if (resetPwdForm.pwd1 !== resetPwdForm.pwd2) {
      ElMessage.error("The new passwords do not match.");
      return;
    }
    try {
      await authHttp.resetPwd(resetPwdForm.oldpwd, resetPwdForm.pwd1, resetPwdForm.pwd2);
      ElMessage.success("Password updated successfully.");
      dialogVisible.value = false;
    } catch (detail) {
      ElMessage.error(detail);
    }
  });
};
</script>

<template>
  <el-container class="layout-shell">
    <el-aside class="aside" :width="asideWidth">
      <router-link to="/" class="brand">
        <span class="brand-mark">EW</span>
        <span v-show="!isCollapse" class="brand-copy">
          <strong>Workflow</strong>
          <small>Operations Console</small>
        </span>
      </router-link>

      <el-menu
        :router="true"
        class="nav-menu"
        :default-active="defaultActive"
        :collapse="isCollapse"
        :collapse-transition="false"
      >
        <template v-for="menuRoute in visibleRoutes" :key="menuRoute.name">
          <el-menu-item v-if="!menuRoute.children" :index="menuRoute.name" :route="{ name: menuRoute.name }">
            <el-icon><component :is="menuRoute.meta.icon" /></el-icon>
            <span>{{ menuRoute.meta.text }}</span>
          </el-menu-item>

          <el-sub-menu v-else :index="menuRoute.name">
            <template #title>
              <el-icon><component :is="menuRoute.meta.icon" /></el-icon>
              <span>{{ menuRoute.meta.text }}</span>
            </template>
            <template v-for="child in menuRoute.children" :key="child.name">
              <el-menu-item
                v-if="!child.meta.hidden && authStore.has_permission(child.meta.permissions, child.meta.opt)"
                :index="child.name"
                :route="{ name: child.name }"
              >
                <el-icon><component :is="child.meta.icon" /></el-icon>
                <span>{{ child.meta.text }}</span>
              </el-menu-item>
            </template>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <el-container class="content-shell">
      <el-header class="header">
        <div class="header-left">
          <el-button class="icon-button" :icon="isCollapse ? Expand : Fold" @click="onCollapseAside" />
          <div class="route-meta">
            <strong>{{ currentTitle }}</strong>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.name">{{ item.text }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>

        <el-dropdown>
          <span class="user-chip">
            <el-avatar :size="32" icon="UserFilled" />
            <span class="user-copy">
              <strong>{{ displayUser.realname }}</strong>
              <small>{{ displayUser.department?.name || "No department" }}</small>
            </span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="onControlResetPwdDialog">Change Password</el-dropdown-item>
              <el-dropdown-item divided @click="onExit">Log Out</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>

  <el-dialog v-model="dialogVisible" title="Change Password" width="520">
    <el-form :model="resetPwdForm" :rules="rules" ref="formTag">
      <el-form-item label="Old Password" :label-width="formLabelWidth" prop="oldpwd">
        <el-input v-model="resetPwdForm.oldpwd" autocomplete="off" type="password" show-password />
      </el-form-item>
      <el-form-item label="New Password" :label-width="formLabelWidth" prop="pwd1">
        <el-input v-model="resetPwdForm.pwd1" autocomplete="off" type="password" show-password />
      </el-form-item>
      <el-form-item label="Confirm" :label-width="formLabelWidth" prop="pwd2">
        <el-input v-model="resetPwdForm.pwd2" autocomplete="off" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="onSubmit">Confirm</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.layout-shell {
  height: 100vh;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(37, 99, 235, 0.08) 1px, transparent 1px),
    linear-gradient(180deg, rgba(20, 184, 166, 0.08) 1px, transparent 1px),
    linear-gradient(135deg, #edf4ff 0%, #f8fbff 45%, #eef2ff 100%);
  background-size: 44px 44px, 44px 44px, auto;
}

.aside {
  position: relative;
  z-index: 2;
  background: rgba(9, 22, 45, 0.94);
  border-right: 1px solid rgba(125, 211, 252, 0.18);
  box-shadow: 18px 0 45px rgba(15, 23, 42, 0.24);
  transition: width 0.2s ease;
}

.brand {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-mark {
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #38bdf8, #2563eb 55%, #14b8a6);
  font-weight: 900;
  letter-spacing: 0;
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.35);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-copy strong {
  line-height: 1.1;
}

.brand-copy small {
  margin-top: 4px;
  color: rgba(226, 232, 240, 0.72);
  font-size: 11px;
}

.nav-menu {
  border-right: none;
  background: transparent;
  padding: 12px 10px;
}

:deep(.el-menu) {
  background: transparent;
  border-right: none;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  height: 46px;
  margin: 5px 0;
  border-radius: 8px;
  color: rgba(226, 232, 240, 0.82);
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(59, 130, 246, 0.14);
  color: #ffffff;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.92), rgba(20, 184, 166, 0.76));
  color: white;
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.28);
}

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 46px !important;
}

.content-shell {
  min-width: 0;
}

.header {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.68);
  border-bottom: 1px solid rgba(37, 99, 235, 0.12);
  backdrop-filter: blur(18px);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.icon-button {
  width: 36px;
  height: 36px;
}

.route-meta {
  min-width: 0;
}

.route-meta strong {
  display: block;
  color: #102033;
  font-size: 16px;
}

.route-meta :deep(.el-breadcrumb) {
  margin-top: 5px;
  font-size: 12px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 7px 10px 7px 7px;
  border: 1px solid rgba(37, 99, 235, 0.14);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
  cursor: pointer;
}

.user-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.user-copy strong {
  color: #102033;
  font-size: 13px;
}

.user-copy small {
  margin-top: 4px;
  color: #667085;
  font-size: 11px;
}

.main {
  min-width: 0;
  padding: 24px;
  overflow: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 900px) {
  .aside {
    width: 72px !important;
  }

  .header {
    padding: 0 14px;
  }

  .route-meta :deep(.el-breadcrumb),
  .user-copy {
    display: none;
  }

  .main {
    padding: 16px;
  }
}
</style>
