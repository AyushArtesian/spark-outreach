/**
 * API Client Service
 * Connects to the backend API at http://localhost:8000/api/v1
 */

const API_BASE = "http://localhost:8000/api/v1";

// Get token from localStorage
const getToken = () => localStorage.getItem("auth_token");

// Fetch helper with automatic Authorization header
async function apiCall(
  endpoint: string,
  options: RequestInit & { requiresAuth?: boolean } = {}
) {
  const { requiresAuth = false, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...fetchOptions.headers,
  };

  if (requiresAuth) {
    const token = getToken();
    if (!token) {
      throw new Error("No authentication token found");
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.statusText}`);
  }

  return response.json();
}

// Auth API
export const authAPI = {
  register: async (data: {
    email: string;
    username: string;
    full_name: string;
    password: string;
  }) => {
    return apiCall("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  login: async (email: string, password: string) => {
    return apiCall("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  getCurrentUser: async () => {
    return apiCall("/auth/me", {
      requiresAuth: true,
    });
  },
};

// Campaigns API
export const campaignsAPI = {
  create: async (data: {
    title: string;
    description: string;
    content: string;
    target_audience: string;
    ai_model?: string;
    temperature?: number;
    max_tokens?: number;
    custom_instructions?: string;
  }) => {
    return apiCall("/campaigns", {
      method: "POST",
      body: JSON.stringify(data),
      requiresAuth: true,
    });
  },

  list: async (skip = 0, limit = 10) => {
    return apiCall(`/campaigns?skip=${skip}&limit=${limit}`, {
      requiresAuth: true,
    });
  },

  get: async (campaignId: string) => {
    return apiCall(`/campaigns/${campaignId}`, {
      requiresAuth: true,
    });
  },

  update: async (campaignId: string, data: Record<string, any>) => {
    return apiCall(`/campaigns/${campaignId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      requiresAuth: true,
    });
  },

  start: async (campaignId: string) => {
    return apiCall(`/campaigns/${campaignId}/start`, {
      method: "POST",
      requiresAuth: true,
    });
  },

  delete: async (campaignId: string) => {
    return apiCall(`/campaigns/${campaignId}`, {
      method: "DELETE",
      requiresAuth: true,
    });
  },
};

// Leads API
export const leadsAPI = {
  create: async (data: {
    name: string;
    email: string;
    company?: string;
    phone?: string;
    job_title?: string;
    industry?: string;
    campaign_id: string;
    raw_data?: Record<string, any>;
  }) => {
    return apiCall("/leads", {
      method: "POST",
      body: JSON.stringify(data),
      requiresAuth: true,
    });
  },

  bulkCreate: async (campaignId: string, leads: Array<any>) => {
    return apiCall("/leads/bulk", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, leads }),
      requiresAuth: true,
    });
  },

  list: async (campaignId: string, skip = 0, limit = 100, status?: string) => {
    let url = `/leads/campaign/${campaignId}?skip=${skip}&limit=${limit}`;
    if (status) url += `&status=${status}`;
    return apiCall(url, { requiresAuth: true });
  },

  get: async (leadId: string) => {
    return apiCall(`/leads/${leadId}`, {
      requiresAuth: true,
    });
  },

  update: async (leadId: string, data: Record<string, any>) => {
    return apiCall(`/leads/${leadId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      requiresAuth: true,
    });
  },

  contact: async (leadId: string) => {
    return apiCall(`/leads/${leadId}/contact`, {
      method: "POST",
      requiresAuth: true,
    });
  },

  delete: async (leadId: string) => {
    return apiCall(`/leads/${leadId}`, {
      method: "DELETE",
      requiresAuth: true,
    });
  },

  search: async (data: {
    query: string;
    campaign_id?: string;
    filters?: Record<string, any>;
    top_k?: number;
    sort_by?: string;
  }) => {
    return apiCall("/leads/search", {
      method: "POST",
      body: JSON.stringify(data),
      requiresAuth: true,
    });
  },

  all: async (skip = 0, limit = 200, status?: string) => {
    let url = `/leads/all?skip=${skip}&limit=${limit}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    return apiCall(url, { requiresAuth: true });
  },
};

// AI API
export const aiAPI = {
  generateMessage: async (leadId: string, campaignId: string) => {
    return apiCall("/ai/generate-message", {
      method: "POST",
      body: JSON.stringify({ lead_id: leadId, campaign_id: campaignId }),
      requiresAuth: true,
    });
  },

  ragSearch: async (query: string, campaignId: string, topK = 3) => {
    return apiCall("/ai/rag-search", {
      method: "POST",
      body: JSON.stringify({ query, campaign_id: campaignId, top_k: topK }),
      requiresAuth: true,
    });
  },

  createEmbeddings: async (campaignId: string) => {
    return apiCall("/ai/create-embeddings", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId }),
      requiresAuth: true,
    });
  },
};

// Company API
export const companyAPI = {
  queryProfile: async (query: string, topK = 3) => {
    return apiCall("/company/profile/query", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
      requiresAuth: true,
    });
  },
};
