<script setup name="login">
import login_img from "@/assets/image/login.png"
import {reactive, ref} from "vue"
import {useAuthStore} from "@/stores/auth"
import {useRouter} from "vue-router"
import authHttp from "@/api/authHttp"
import {ElMessage} from "element-plus"

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: "",
  password: ""
})
const loading = ref(false)

const onSubmit = async () => {
    let emailRgx = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
    if(!(emailRgx.test(form.email))){
        ElMessage.info('The email format is not satisfactory!')
        return;
    }
    if(form.password.length < 6 || form.password.length > 20){
        ElMessage.info("Password length must be between 6 and 20 characters.")
        return;
    }
    // asynchronous call
    loading.value = true
    try{
        let data = await authHttp.login(form.email, form.password)
        let token = data.token;
        let user = data.user;
        authStore.setUserToken(user, token);
        // Jump to the homepage of the OA system
        router.push({name: "frame"})
    }catch(detail){
        ElMessage.error(detail)
    } finally {
        loading.value = false
    }
  }

</script>
<template>
  <div class="dowebok">
    <div class="container-login100">
      <div class="wrap-login100">
        <div class="login100-pic js-tilt" data-tilt>
          <img :src="login_img" alt="IMG" />
        </div>


        <div class="login100-form validate-form">
          <span class="login100-form-title">EMPLOYEE LOGIN</span>

          <!-- email -->
          <div class="wrap-input100 validate-input">
            <input class="input100" type="text" name="email" placeholder="Email" v-model="form.email" @keyup.enter="onSubmit"/>
            <span class="focus-input100"></span>
            <span class="symbol-input100">
              <i class="iconfont icon-fa-envelope" aria-hidden="true"></i>
            </span>
          </div>
          
          <!-- password -->
          <div class="wrap-input100">
            <input class="input100" type="password" placeholder="Password"  v-model="form.password" @keyup.enter="onSubmit"/>
            <span class="focus-input100"></span>
            <span class="symbol-input100">
              <i class="iconfont icon-fa-lock" aria-hidden="true"></i>
            </span>
          </div>

          <!-- button -->
          <div class="container-login100-form-btn" >
            <button class="login100-form-btn" :disabled="loading" @click="onSubmit">
              {{ loading ? "Signing in..." : "Login" }}
            </button>
          </div>

        </div>

      </div>
    </div>
  </div>
</template>
<style src="@/assets/css/login.css"></style>
<style scoped src="@/assets/iconfont/iconfont.css"></style>
