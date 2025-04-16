import axios from "axios";
import { API_URL, getAuthToken } from "./utils";

// Create axios instance with base URL and default headers
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to attach auth token
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication APIs
export const login = async (username: string, password: string) => {
  try {
    const response = await api.post("/auth/login", { username, password });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const refreshToken = async (refreshToken: string) => {
  try {
    const response = await api.post("/auth/refresh", {}, {
      headers: {
        "Authorization": `Bearer ${refreshToken}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const revokeToken = async () => {
  try {
    const response = await api.post("/auth/revoke");
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const validateToken = async () => {
  try {
    const response = await api.get("/auth/validate");
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Query APIs
export const generateQuery = async (query: string, db_id: string = "default") => {
  try {
    const response = await api.post("/query/generate", { query, db_id });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const generateMultiDbQuery = async (query: string) => {
  try {
    const response = await api.post("/query/multi-db", { query });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const executeQuery = async (sql: string, parameters = {}, db_id: string = "default") => {
  try {
    const response = await api.post("/query/execute", { sql, parameters, db_id });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const listDatabases = async () => {
  try {
    const response = await api.get("/databases");
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Agent APIs
export const listAgents = async () => {
  try {
    const response = await api.get("/agents");
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAgent = async (agentId: string) => {
  try {
    const response = await api.get(`/agents/${agentId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const configureAgent = async (agentId: string, config: any) => {
  try {
    const response = await api.post(`/agents/${agentId}/config`, { config });
    return response.data;
  } catch (error) {
    throw error;
  }
}; 