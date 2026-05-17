import http from "./http"

const getDepartmentStaffCount = () => {
    const path = "/home/department/staff/count"
    return http.get(path)
}

const getLatestInforms = () => {
    const path = "/home/latest/inform"
    return http.get(path)
}

const getLatestAbsents = () => {
    const path = "/home/latest/workflow"
    return http.get(path)
}

const getWorkflowSummary = () => {
    const path = "/home/workflow/summary"
    return http.get(path)
}


export default {
    getDepartmentStaffCount,
    getLatestInforms,
    getLatestAbsents,
    getWorkflowSummary
}
