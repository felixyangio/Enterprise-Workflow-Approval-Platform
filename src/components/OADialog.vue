<script setup name="OADialog">
let dialogVisible = defineModel({required: true});
let props = defineProps({
  title: {
    type: String,
    default: ""
  },
  width: {
    type: String,
    default: "560"
  },
  confirmText: {
    type: String,
    default: "Confirm"
  },
  cancelText: {
    type: String,
    default: "Cancel"
  },
  submitting: {
    type: Boolean,
    default: false
  }
})

const emits = defineEmits(['cancel', 'submit'])

const onCancel = () => {
  dialogVisible.value = false
  emits('cancel');
}

const onSubmit = () => {
  emits('submit');
}


</script>

<template>
  <el-dialog v-model="dialogVisible" :title="props.title" :width="props.width" class="oa-dialog">
    <slot></slot>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="onCancel">{{ props.cancelText }}</el-button>
        <el-button type="primary" :loading="props.submitting" @click="onSubmit">
          {{ props.confirmText }}
        </el-button>
      </div>
    </template>

  </el-dialog>
 
</template>
<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

</style>
