<script setup></script>

<template>
  <RouterView />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  color: #102033;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    Arial, sans-serif;
  --oa-primary: #2563eb;
  --oa-primary-2: #14b8a6;
  --oa-ink: #102033;
  --oa-muted: #667085;
  --oa-border: rgba(37, 99, 235, 0.14);
  --oa-card: rgba(255, 255, 255, 0.86);
}

html,
body,
#app {
  min-height: 100%;
}

body {
  background: #edf4ff;
}

a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}

a:hover {
  color: #0f766e;
}

.oa-panel {
  background: var(--oa-card);
  border: 1px solid var(--oa-border);
  border-radius: 8px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.oa-filter-card {
  margin-bottom: 16px;
}

.oa-filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.oa-filter-form .el-form-item {
  margin: 0;
}

.oa-table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.oa-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.oa-card-header h2 {
  margin: 0;
  font-size: 16px;
  color: var(--oa-ink);
}

.oa-muted {
  color: var(--oa-muted);
}

.el-card {
  border-radius: 8px;
}

.el-card__header {
  padding: 16px 18px;
}

.el-table {
  --el-table-header-bg-color: rgba(239, 246, 255, 0.92);
  --el-table-row-hover-bg-color: rgba(37, 99, 235, 0.06);
}

.el-table th.el-table__cell {
  color: #102033;
  font-weight: 700;
}

.el-button {
  border-radius: 7px;
}

.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner {
  border-radius: 7px;
}

@media (max-width: 768px) {
  .oa-filter-form {
    display: block;
  }

  .oa-filter-form .el-form-item {
    margin-bottom: 12px;
    width: 100%;
  }

  .oa-filter-form .el-input,
  .oa-filter-form .el-select,
  .oa-filter-form .el-date-editor {
    width: 100% !important;
  }
}
</style>
