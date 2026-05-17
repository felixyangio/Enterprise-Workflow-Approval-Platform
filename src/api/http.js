import axios from "axios";
import { useAuthStore } from "@/stores/auth";

class Http {
  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_BASE_URL,
      timeout: 6000,
    });

    this.instance.interceptors.request.use((config) => {
      const authStore = useAuthStore();
      const token = authStore.token;
      if (token) {
        config.headers.Authorization = "JWT " + token;
      }
      return config;
    });
  }

  post(path, data) {
    // path: /auth/login
    // url: http://127.0.0.1:8000/auth/login
    // return this.instance.post(path, data)
    return new Promise(async (resolve, reject) => {
      try {
        let result = await this.instance.post(path, data);
        resolve(result.data);
      } catch (err) {
        reject(this.getErrorMessage(err));
      }
    });
  }

  get(path, params) {
    return new Promise(async (resolve, reject) => {
      try {
        let result = await this.instance.get(path, { params });
        resolve(result.data);
      } catch (err) {
        reject(this.getErrorMessage(err));
      }
    });
  }

  put(path, data) {
    return new Promise(async (resolve, reject) => {
      try {
        let result = await this.instance.put(path, data);
        resolve(result.data);
      } catch (err) {
        reject(this.getErrorMessage(err));
      }
    });
  }

  delete(path) {
    return new Promise(async (resolve, reject) => {
      try {
        let result = await this.instance.delete(path);
        resolve(result);
      } catch (err) {
        reject(this.getErrorMessage(err));
      }
    });
  }

  downloadFile(path, params) {
    return new Promise(async (resolve, reject) => {
      try {
        let result = await this.instance.get(path, {
          params,
          responseType: "blob",
        });
        resolve(result);
      } catch (err) {
        reject(this.getErrorMessage(err));
      }
    });
  }

  getErrorMessage(err) {
    if (err?.response?.status === 401) {
      const authStore = useAuthStore();
      authStore.clearUserToken();
      return "Login expired. Please sign in again.";
    }
    const data = err?.response?.data;
    if (!data) return "Server Error";
    if (typeof data === "string") return data;
    if (data.detail) return data.detail;
    const firstKey = Object.keys(data)[0];
    const firstValue = data[firstKey];
    if (Array.isArray(firstValue)) return firstValue[0];
    if (typeof firstValue === "string") return firstValue;
    return "Server Error";
  }
}

export default new Http();
