import apiClient from "./axios";

// User API functions
export const getAllUsers = async () => {
  const response = await apiClient.get("/users");
  return response.data;
};

export const createUser = async (name, email) => {
  const response = await apiClient.post("/users", { name, email });
  return response.data;
};

export const getUserById = async (userId) => {
  const response = await apiClient.get(`/users/${userId}`);
  return response.data;
};

export const getUserJobs = async (userId) => {
  const response = await apiClient.get(`/users/${userId}/jobs`);
  return response.data;
};

// Job API functions
export const uploadFile = async (userId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post(`/jobs?user_id=${userId}`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const startJob = async (jobId) => {
  const response = await apiClient.post(`/jobs/${jobId}/start`);
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await apiClient.get(`/jobs/${jobId}`);
  return response.data;
};

export const getJobTransactions = async (
  jobId,
  page = 1,
  size = 20,
  filter = null,
) => {
  const params = { page, size };
  if (filter) {
    params.filter = filter;
  }

  const response = await apiClient.get(`/jobs/${jobId}/transactions`, {
    params,
  });
  return response.data;
};

// Export all as a service object (for backward compatibility if needed)
export const apiService = {
  getAllUsers,
  createUser,
  getUserById,
  getUserJobs,
  uploadFile,
  startJob,
  getJobStatus,
  getJobTransactions,
};

export default apiService;
