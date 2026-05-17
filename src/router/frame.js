import frame from "@/views/main/frame.vue";
import myabsent from "@/views/absent/my.vue";
import subabsent from "@/views/absent/sub.vue";
import workflow_detail from "@/views/absent/detail.vue";
import publish from "@/views/inform/publish.vue";
import inform_detail from "@/views/inform/detail.vue";
import inform_list from "@/views/inform/list.vue";
import staffadd from "@/views/staff/add.vue";
import stafflist from "@/views/staff/list.vue";
import home from "@/views/home/home.vue";
import absent from "@/views/absent/index.vue";
import inform from "@/views/inform/index.vue";
import staff from "@/views/staff/index.vue";
import { PermissionChoices } from "@/stores/auth";

const routes = [
  {
    path: "/",
    name: "frame",
    component: frame,
    redirect: "/home",
    children: [
      {
        path: "home",
        name: "home",
        component: home,
        meta: {
          icon: "HomeFilled",
          text: "Home",
          permissions: [PermissionChoices.Staff],
          opt: "|",
        },
      },
      {
        path: "/absent",
        name: "absent",
        component: absent,
        meta: {
          icon: "Checked",
          text: "Workflow Center",
          permissions: [PermissionChoices.Staff],
          opt: "|",
        },
        children: [
          {
            path: "my",
            name: "myabsent",
            component: myabsent,
            meta: {
              icon: "UserFilled",
              text: "My Requests",
              permissions: [PermissionChoices.Staff],
              opt: "|",
            },
          },
          {
            path: "sub",
            name: "subabsent",
            component: subabsent,
            meta: {
              icon: "User",
              text: "Approval Todo",
              permissions: [
                PermissionChoices.Superuser,
              ],
              opt: "|",
            },
          },
          {
            path: "detail/:id",
            name: "workflow_detail",
            component: workflow_detail,
            meta: {
              hidden: true,
              permissions: [PermissionChoices.Staff],
              opt: "|",
            },
          },
        ],
      },
      {
        path: "/inform",
        name: "inform",
        component: inform,
        meta: {
          icon: "BellFilled",
          text: "Notification Management",
          permissions: [PermissionChoices.Staff],
          opt: "|",
        },
        children: [
          {
            path: "publish",
            name: "inform_publish",
            component: publish,
            meta: {
              icon: "CirclePlusFilled",
              text: "Publish Notification",
              permissions: [
                PermissionChoices.Boarder,
                PermissionChoices.Leader,
              ],
              opt: "|",
            },
          },
          {
            path: "list",
            name: "inform_list",
            component: inform_list,
            meta: {
              icon: "List",
              text: "Notification List",
              permissions: [PermissionChoices.Staff],
              opt: "|",
            },
          },
          {
            path: "detail/:pk",
            name: "inform_detail",
            component: inform_detail,
            meta: {
              hidden: true,
              permissions: [PermissionChoices.Staff],
              opt: "|",
            },
          },
        ],
      },
      {
        path: "/staff",
        name: "staff",
        component: staff,
        meta: {
          icon: "Avatar",
          text: "Employee Management",
          permissions: [PermissionChoices.Boarder, PermissionChoices.Leader, PermissionChoices.Superuser],
          opt: "|",
        },
        children: [
          {
            path: "add",
            name: "staff_add",
            component: staffadd,
            meta: {
              icon: "CirclePlusFilled",
              text: "Add Employee",
              permissions: [
                PermissionChoices.Superuser,
              ],
              opt: "|",
            },
          },
          {
            path: "list",
            name: "staff_list",
            component: stafflist,
            meta: {
              icon: "List",
              text: "Employee List",
              permissions: [
                PermissionChoices.Boarder,
                PermissionChoices.Leader,
                PermissionChoices.Superuser,
              ],
              opt: "|",
            },
          },
        ],
      },
    ],
  },
];

export default routes;
