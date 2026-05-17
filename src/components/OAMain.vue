<script setup name="OAMain">
let props = defineProps({
  title: {
    type: String,
    default: "",
  },
  subtitle: {
    type: String,
    default: "",
  },
});

</script>

<template>
  <section class="oa-main">
    <div class="oa-main__header">
      <div>
        <p class="oa-main__eyebrow">Employee Workflow</p>
        <h1>{{ props.title }}</h1>
        <p v-if="props.subtitle" class="oa-main__subtitle">{{ props.subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="oa-main__actions">
        <slot name="actions"></slot>
      </div>
    </div>
    <slot></slot>
  </section>
</template>
<style scoped>
.oa-main {
  width: 100%;
}

.oa-main__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 20px;
}

.oa-main__eyebrow {
  margin: 0 0 6px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.oa-main h1 {
  margin: 0;
  color: #102033;
  font-size: 28px;
  line-height: 1.2;
}

.oa-main__subtitle {
  margin: 8px 0 0;
  color: #667085;
}

.oa-main__actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .oa-main__header {
    display: block;
  }

  .oa-main h1 {
    font-size: 23px;
  }

  .oa-main__actions {
    justify-content: flex-start;
    margin-top: 14px;
  }
}

</style>
