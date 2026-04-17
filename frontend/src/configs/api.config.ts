export const API_CONFIG = {
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  USE_MOCK_DATA: false,
};

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
    VERIFY: '/api/auth/verify',
    REGISTER: '/api/auth/register',
    VERIFY_EMAIL: '/api/auth/verify-email',
    RESEND_VERIFICATION: '/api/auth/resend-verification',
    FORGOT_PASSWORD: '/api/auth/forgot-password',
    RESET_PASSWORD: '/api/auth/reset-password',
    CHALLENGE: '/api/auth/challenge',
  },

  // Users
  USERS: {
    GET_CURRENT: '/api/users/me',
    UPDATE: '/api/users/update',
    GET_ALL: '/api/users',
    GET_COUNT: '/api/users/count',
  },

  // Documents
  DOCUMENTS: {
    UPLOAD: '/api/documents',
    GET_ALL: '/api/documents',
    GET_BY_ID: '/api/documents/:id',
    DELETE: '/api/documents/:id',
    DOWNLOAD: '/api/documents/:id/download',
    GET_BY_EMBEDDING_MODEL: '/api/documents/by-embedding-model',
  },

  // Models (AI model configuration)
  MODELS: {
    GET_ALL: '/api/models',
    GET_BY_ID: '/api/models/:id',
    CREATE: '/api/models',
    UPDATE: '/api/models/:id',
    DELETE: '/api/models/:id',
  },

  // RAG Pipelines
  PIPELINES: {
    GET_ALL: '/api/pipelines',
    GET_BY_ID: '/api/pipelines/:id',
    CREATE: '/api/pipelines',
    UPDATE: '/api/pipelines/:id',
    DELETE: '/api/pipelines/:id',
    RUN: '/api/pipelines/:id/run',
  },

  // Pipeline Types
  PIPELINE_TYPES: {
    GET_ALL: '/api/pipeline-types',
    GET_BY_ID: '/api/pipeline-types/:id',
  },

  // Structured Outputs
  OUTPUTS: {
    GET_ALL: '/api/outputs',
    DOWNLOAD: '/api/outputs/:id/download',
    DELETE: '/api/outputs/:id',
  },

  // Queries (Q&A)
  QUERIES: {
    ASK: '/api/queries',
    GET_ALL: '/api/queries',
    DELETE: '/api/queries/:id',
  },

  // Billing
  BILLING: {
    GET_PLANS: '/api/billing/plans',
    GET_CURRENT: '/api/billing/current',
    CREATE_CHECKOUT: '/api/billing/checkout',
    CREATE_PORTAL: '/api/billing/portal',
  },

  // Notifications
  NOTIFICATIONS: {
    GET_ALL: '/api/notifications',
    MARK_READ: '/api/notifications/:id/read',
    READ_ALL: '/api/notifications/read-all',
    UNREAD_COUNT: '/api/notifications/unread-count',
  },

  // Organizations
  ORGANIZATIONS: {
    GET_CURRENT: '/api/organizations/current',
    UPDATE: '/api/organizations/current',
    CREATE: '/api/organizations',
    MEMBERS: '/api/organizations/members',
    INVITATIONS: '/api/organizations/invitations',
  },
};

export default API_CONFIG;
