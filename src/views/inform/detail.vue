<script setup name="informdetail">
import informHttp from "@/api/informHttp";
import { reactive, onMounted } from "vue"
import { ElMessage } from "element-plus"
import timeFormatter from "@/utils/timeFormatter";
import OAMain from "@/components/OAMain.vue"
import { useRoute, useRouter } from "vue-router";

const route = useRoute()
const router = useRouter()

let inform = reactive({
    title: "",
    content: "",
    create_time: "",
    author: {
        realname: "",
        department: {
            name: ""
        }
    }
})

onMounted(async () => {
    const pk = route.params.pk
    try{
        let data = await informHttp.getInformDetail(pk)
        Object.assign(inform, data)
        await informHttp.readInform(pk)
    } catch(detail) {
        ElMessage.error(detail)
    }
})

</script>

<template>
<OAMain title="Notification Details" subtitle="Read the full announcement and attached rich content.">
  <template #actions>
    <el-button icon="Back" @click="router.push({ name: 'inform_list' })">Back to List</el-button>
  </template>
    <el-card class="oa-panel">
        <template #header>
            <div class="detail-heading">
                <h2>{{ inform.title }}</h2>
                <div class="oa-muted">
                    <span>Author: {{ inform.author.realname }}</span>
                    <span>Published: {{ timeFormatter.stringFromDateTime(inform.create_time) }}</span>
                </div>
            </div>
        </template>
        <template #default>
            <div v-html="inform.content" class="content"></div>
        </template>
        <template #footer>Views: {{ inform.read_count }}</template>
    </el-card>
</OAMain>
</template>

<style scoped>
.detail-heading {
  text-align: center;
}

.detail-heading h2 {
  margin: 0 0 14px;
  font-size: 24px;
  color: #102033;
}

.detail-heading div {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.content {
  min-height: 240px;
  line-height: 1.7;
}

.content :deep(img){
    max-width: 100%;
}
</style>
