import { ref, computed } from "vue";
import { defineStore } from "pinia";

const USER_KEY = "OA_USER_KEY";
const TOKEN_KEY = "OA_TOKEN_KEY";

export const PermissionChoices = {
  All: 0b111,
  Staff: 0b000,
  Boarder: 0b001,
  Leader: 0b010,
  Superuser: 0b100,
};

export const useAuthStore = defineStore("auth", () => {
  let _user = ref({});
  let _token = ref("");

  function setUserToken(user, token) {
    _user.value = user;
    _token.value = token;

    localStorage.setItem(USER_KEY, JSON.stringify(user));
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearUserToken() {
    _user.value = {};
    _token.value = "";
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
  }

  let user = computed(() => {
    // _user.value = {}
    if (Object.keys(_user.value).length == 0) {
      let user_str = localStorage.getItem(USER_KEY);
      if (user_str) {
        _user.value = JSON.parse(user_str);
      }
    }
    return _user.value;
  });

  let token = computed(() => {
    if (!_token.value) {
      let token_str = localStorage.getItem(TOKEN_KEY);
      if (token_str) {
        _token.value = token_str;
      }
    }
    return _token.value;
  });

  let is_logined = computed(() => {
    if (Object.keys(user.value).length > 0 && token.value) {
      return true;
    }
    return false;
  });

  let own_permissions = computed(() => {
    // 0b000
    let _permissions = PermissionChoices.Staff;
    if (is_logined.value) {
      // Check whether the user is a board member
      if (user.value.department?.name == "Board of Directors") {
        // 0b000 | 0b001 = 0b001
        _permissions |= PermissionChoices.Boarder;
      }

      // Check whether the user is a leader
      if (
        user.value.department?.leader_id != null
        && user.value.uid != null
        && user.value.department.leader_id === user.value.uid
      ) {
        _permissions |= PermissionChoices.Leader;
      }

      // Check whether the user is a superuser
      if (user.value.is_superuser) {
        _permissions |= PermissionChoices.Superuser;
      }
    }
    return _permissions;
  });

  function has_permission(permissions, opt = "|") {
    // opt：
    // 1. |
    // 2. &
    // own_permissions: 0b001
    // permissions: [0b010, 0b001]
    let results = permissions.map(
      (permission) => (permission & own_permissions.value) == permission,
    );
    // results = [true, false, false, true]
    if (opt == "|") {
      if (results.indexOf(true) >= 0) {
        return true;
      } else {
        return false;
      }
    } else {
      if (results.indexOf(false) >= 0) {
        return false;
      } else {
        return true;
      }
    }
  }

  return {
    setUserToken,
    user,
    token,
    is_logined,
    clearUserToken,
    has_permission,
  };
});
