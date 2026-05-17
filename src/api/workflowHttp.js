import http from "./http";

const getCategories = () => http.get("/workflow/categories");

const getRequests = (params = {}) => http.get("/workflow/requests", params);

const createRequest = (data) => http.post("/workflow/requests", data);

const getRequestDetail = (id) => http.get(`/workflow/requests/${id}`);

const getRequestLogs = (id) => http.get(`/workflow/requests/${id}/logs`);

const approveRequest = (id, comment = "") => http.put(`/workflow/requests/${id}/approve`, { comment });

const rejectRequest = (id, comment = "") => http.put(`/workflow/requests/${id}/reject`, { comment });

const withdrawRequest = (id, comment = "") => http.put(`/workflow/requests/${id}/withdraw`, { comment });

const getSummary = () => http.get("/workflow/summary");

export default {
  getCategories,
  getRequests,
  createRequest,
  getRequestDetail,
  getRequestLogs,
  approveRequest,
  rejectRequest,
  withdrawRequest,
  getSummary,
};
