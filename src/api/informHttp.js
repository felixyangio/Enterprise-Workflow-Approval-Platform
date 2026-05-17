import http from "./http";

const publishInform = (data) => {
  const path = "/inform/inform";
  return http.post(path, data);
};

const getInformList = (page = 1, params = {}) => {
  const path = "/inform/inform";
  return http.get(path, { ...params, page });
};

const deleteInform = (pk) => {
  const path = "/inform/inform/" + pk;
  return http.delete(path);
};

const getInformDetail = (pk) => {
  const path = "/inform/inform/" + pk;
  return http.get(path);
};

const readInform = (pk) => {
  const path = "/inform/inform/read";
  return http.post(path, { inform_pk: pk });
};

export default {
  publishInform,
  getInformList,
  deleteInform,
  getInformDetail,
  readInform,
};
