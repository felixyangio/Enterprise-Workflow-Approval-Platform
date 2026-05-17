<script setup name="OAPagination">
let props = defineProps({
  total: {
    type: Number,
    default: 0
  },
  pageSize: {
    type: Number,
    default: 10
  },
  layout: {
    type: String,
    default: "total, prev, pager, next"
  }
})

let page = defineModel({required: true})

</script>

<template>
  <div class="oa-pagination">
    <el-pagination
      background
      :layout="props.layout"
      :total="props.total"
      :page-size="props.pageSize"
      v-model:current-page="page"
    />
  </div>
</template>
<style scoped>
.oa-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 4px 0;
}

@media (max-width: 768px) {
  .oa-pagination {
    justify-content: center;
  }
}
</style>
