<script setup name="login">
import {computed, reactive, ref} from "vue"
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
const canSubmit = computed(() => Boolean(form.email.trim() && form.password) && !loading.value)

const onSubmit = async () => {
    const email = form.email.trim()
    const emailRgx = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
    if(!(emailRgx.test(email))){
        ElMessage.info('Please enter a valid business email address.')
        return;
    }
    if(form.password.length < 6 || form.password.length > 20){
        ElMessage.info("Password length must be between 6 and 20 characters.")
        return;
    }
    // asynchronous call
    loading.value = true
    try{
        let data = await authHttp.login(email, form.password)
        let token = data.token;
        let user = data.user;
        authStore.setUserToken(user, token);
        // Jump to the homepage of the OA system
        router.push({name: "frame"})
    }catch(detail){
        ElMessage.error(typeof detail === "string" ? detail : "Unable to sign in. Please check your credentials.")
    } finally {
        loading.value = false
    }
  }

</script>
<template>
  <div class="login-page">
    <div class="container-login100">
      <div class="wrap-login100">
        <div class="login-hero" aria-hidden="true">
          <div class="hero-badge">EW</div>
          <div>
            <p class="hero-kicker">Enterprise Workflow</p>
            <h1>Approval Operations Platform</h1>
          </div>
          <p class="hero-copy">
            A secure workspace for employee requests, approvals, notifications, and workforce administration.
          </p>
          <div class="hero-grid">
            <span>Workflow Center</span>
            <span>Role Permissions</span>
            <span>Team Notices</span>
            <span>Staff Directory</span>
          </div>
        </div>

        <form class="login100-form validate-form" @submit.prevent="onSubmit">
          <div class="login100-form-title">
            <span>Welcome Back</span>
            <strong>Sign in to manage enterprise approvals.</strong>
          </div>

          <!-- email -->
          <div class="wrap-input100 validate-input">
            <input
              class="input100"
              type="email"
              name="email"
              placeholder="Business email"
              v-model="form.email"
              autocomplete="username"
            />
            <span class="focus-input100"></span>
            <span class="symbol-input100">
              <i class="iconfont icon-fa-envelope" aria-hidden="true"></i>
            </span>
          </div>
          
          <!-- password -->
          <div class="wrap-input100">
            <input
              class="input100"
              type="password"
              placeholder="Password"
              v-model="form.password"
              autocomplete="current-password"
            />
            <span class="focus-input100"></span>
            <span class="symbol-input100">
              <i class="iconfont icon-fa-lock" aria-hidden="true"></i>
            </span>
          </div>

          <!-- button -->
          <div class="container-login100-form-btn" >
            <button class="login100-form-btn" type="submit" :disabled="!canSubmit">
              {{ loading ? "Signing in..." : "Sign In" }}
            </button>
          </div>

          <p class="login-footnote">Protected access for authorized employees only.</p>
        </form>

      </div>
    </div>
  </div>
</template>
<style src="@/assets/css/login.css"></style>
<style scoped src="@/assets/iconfont/iconfont.css"></style>
