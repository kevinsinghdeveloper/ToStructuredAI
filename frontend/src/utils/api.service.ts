import axios, { AxiosInstance } from 'axios';
import { API_CONFIG } from '../configs/api.config';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_CONFIG.API_BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: { 'Content-Type': 'application/json' },
    });

    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      const orgId = localStorage.getItem('currentOrgId');
      if (orgId) {
        config.headers['X-Org-Id'] = orgId;
      }
      return config;
    });

    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && localStorage.getItem('authToken')) {
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
          localStorage.removeItem('currentOrgId');
          window.location.href = '/login';
        }
        const message =
          error.response?.data?.error ||
          error.response?.data?.message ||
          error.message ||
          'An unexpected error occurred';
        return Promise.reject(new Error(message));
      }
    );
  }

  // ==================== Auth ====================
  async login(email: string, password: string) {
    const response = await this.api.post('/api/auth/login', { email, password });
    return response.data;
  }

  async register(data: { email: string; password: string; firstName: string; lastName: string; invitationToken?: string }) {
    const response = await this.api.post('/api/auth/register', data);
    return response.data;
  }

  async logout() {
    const response = await this.api.post('/api/auth/logout');
    return response.data;
  }

  async respondToChallenge(email: string, newPassword: string, session: string) {
    const response = await this.api.post('/api/auth/challenge', { email, newPassword, session });
    return response.data;
  }

  async requestPasswordReset(email: string) {
    const response = await this.api.post('/api/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(email: string, code: string, newPassword: string) {
    const response = await this.api.post('/api/auth/reset-password', { email, code, newPassword });
    return response.data;
  }

  async verifyEmail(email: string, code: string) {
    const response = await this.api.post('/api/auth/verify-email', { email, code });
    return response.data;
  }

  async acceptInvitation(token: string) {
    const response = await this.api.post('/api/auth/accept-invitation', { token });
    return response.data;
  }

  // OAuth
  async getOAuthUrl(provider: string, redirectUri: string) {
    const response = await this.api.get(`/api/auth/oauth/${provider}/authorize`, { params: { redirect_uri: redirectUri } });
    return response.data;
  }

  async oauthCallback(provider: string, code: string, redirectUri: string) {
    const response = await this.api.post(`/api/auth/oauth/${provider}/callback`, { code, redirect_uri: redirectUri });
    return response.data;
  }

  // ==================== Users ====================
  async getCurrentUser() {
    const response = await this.api.get('/api/users/me');
    return response.data;
  }

  async listUsers(page: number = 1, perPage: number = 20) {
    const response = await this.api.get('/api/users', { params: { page, per_page: perPage } });
    return response.data;
  }

  async updateUser(userId: string, data: any) {
    const response = await this.api.put(`/api/users/${userId}`, data);
    return response.data;
  }

  async deleteUser(userId: string) {
    const response = await this.api.delete(`/api/users/${userId}`);
    return response.data;
  }

  async updatePreferences(data: any) {
    const response = await this.api.put('/api/users/me/preferences', data);
    return response.data;
  }

  // ==================== Organizations ====================
  async getCurrentOrg() {
    const response = await this.api.get('/api/organizations/current');
    return response.data;
  }

  async updateOrg(data: any) {
    const response = await this.api.put('/api/organizations/current', data);
    return response.data;
  }

  async createOrg(data: { name: string }) {
    const response = await this.api.post('/api/organizations', data);
    return response.data;
  }

  async listOrgInvitations() {
    const response = await this.api.get('/api/organizations/invitations');
    return response.data;
  }

  async createOrgInvitation(email: string, role: string = 'member') {
    const response = await this.api.post('/api/organizations/invitations', { email, role });
    return response.data;
  }

  async deleteOrgInvitation(invitationId: string) {
    const response = await this.api.delete(`/api/organizations/invitations/${invitationId}`);
    return response.data;
  }

  async listOrgMembers() {
    const response = await this.api.get('/api/organizations/members');
    return response.data;
  }

  async updateMemberRole(memberId: string, role: string) {
    const response = await this.api.put(`/api/organizations/members/${memberId}/role`, { role });
    return response.data;
  }

  async removeMember(memberId: string) {
    const response = await this.api.delete(`/api/organizations/members/${memberId}`);
    return response.data;
  }

  async listMyOrgs() {
    const response = await this.api.get('/api/users/me/orgs');
    return response.data;
  }

  // ==================== Documents ====================
  async getAllDocuments() {
    const response = await this.api.get('/api/documents');
    return response.data;
  }

  async getDocument(id: string) {
    const response = await this.api.get(`/api/documents/${id}`);
    return response.data;
  }

  async uploadDocument(file: File, embeddingModelId: string, overwrite: boolean = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('embedding_model_id', embeddingModelId);
    if (overwrite) formData.append('overwrite', 'true');
    const response = await this.api.post('/api/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async deleteDocument(id: string) {
    const response = await this.api.delete(`/api/documents/${id}`);
    return response.data;
  }

  async downloadDocument(id: string) {
    const response = await this.api.get(`/api/documents/${id}/download`, { responseType: 'blob' });
    return response.data;
  }

  async getDocumentsByEmbeddingModel(embeddingModelId: string) {
    const response = await this.api.get('/api/documents/by-embedding-model', {
      params: { embedding_model_id: embeddingModelId },
    });
    return response.data;
  }

  // ==================== Models ====================
  async getAllModels(modelType?: string) {
    const response = await this.api.get('/api/models', { params: modelType ? { model_type: modelType } : {} });
    return response.data;
  }

  async getModel(id: string) {
    const response = await this.api.get(`/api/models/${id}`);
    return response.data;
  }

  async createModel(data: any) {
    const response = await this.api.post('/api/models', data);
    return response.data;
  }

  async updateModel(id: string, data: any) {
    const response = await this.api.put(`/api/models/${id}`, data);
    return response.data;
  }

  async deleteModel(id: string) {
    const response = await this.api.delete(`/api/models/${id}`);
    return response.data;
  }

  // ==================== Pipelines ====================
  async getAllPipelines() {
    const response = await this.api.get('/api/pipelines');
    return response.data;
  }

  async getPipeline(id: string) {
    const response = await this.api.get(`/api/pipelines/${id}`);
    return response.data;
  }

  async createPipeline(data: any) {
    const response = await this.api.post('/api/pipelines', data);
    return response.data;
  }

  async updatePipeline(id: string, data: any) {
    const response = await this.api.put(`/api/pipelines/${id}`, data);
    return response.data;
  }

  async deletePipeline(id: string) {
    const response = await this.api.delete(`/api/pipelines/${id}`);
    return response.data;
  }

  async runPipeline(id: string, data?: any) {
    const response = await this.api.post(`/api/pipelines/${id}/run`, data || {});
    return response.data;
  }

  // ==================== Pipeline Types ====================
  async getAllPipelineTypes() {
    const response = await this.api.get('/api/pipeline-types');
    return response.data;
  }

  async getPipelineType(id: string) {
    const response = await this.api.get(`/api/pipeline-types/${id}`);
    return response.data;
  }

  // ==================== Outputs ====================
  async getOutputs(pipelineId?: string) {
    const response = await this.api.get('/api/outputs', { params: pipelineId ? { pipeline_id: pipelineId } : {} });
    return response.data;
  }

  async downloadOutput(outputId: string, pipelineId: string) {
    const response = await this.api.get(`/api/outputs/${outputId}/download`, {
      params: { pipeline_id: pipelineId },
      responseType: 'blob',
    });
    return response.data;
  }

  async deleteOutput(outputId: string, pipelineId: string) {
    const response = await this.api.delete(`/api/outputs/${outputId}`, {
      params: { pipeline_id: pipelineId },
    });
    return response.data;
  }

  // ==================== Queries (Q&A) ====================
  async getQueries(pipelineId?: string) {
    const response = await this.api.get('/api/queries', { params: pipelineId ? { pipeline_id: pipelineId } : {} });
    return response.data;
  }

  async askQuestion(pipelineId: string, question: string) {
    const response = await this.api.post('/api/queries', { pipeline_id: pipelineId, question });
    return response.data;
  }

  async deleteQuery(queryId: string) {
    const response = await this.api.delete(`/api/queries/${queryId}`);
    return response.data;
  }

  // ==================== Database Connections ====================
  async getConnections() {
    const response = await this.api.get('/api/connections');
    return response.data;
  }

  async getConnection(id: string) {
    const response = await this.api.get(`/api/connections/${id}`);
    return response.data;
  }

  async createConnection(data: Record<string, any>) {
    const response = await this.api.post('/api/connections', data);
    return response.data;
  }

  async updateConnection(id: string, data: Record<string, any>) {
    const response = await this.api.put(`/api/connections/${id}`, data);
    return response.data;
  }

  async deleteConnection(id: string) {
    const response = await this.api.delete(`/api/connections/${id}`);
    return response.data;
  }

  async testConnection(id: string) {
    const response = await this.api.post(`/api/connections/${id}/test`);
    return response.data;
  }

  async getConnectionTables(id: string) {
    const response = await this.api.get(`/api/connections/${id}/tables`);
    return response.data;
  }

  async getConnectionTableSchema(connectionId: string, tableName: string) {
    const response = await this.api.get(`/api/connections/${connectionId}/tables/${tableName}/schema`);
    return response.data;
  }

  async createSourceFromTable(connectionId: string, tableName: string, data?: Record<string, any>) {
    const response = await this.api.post(`/api/connections/${connectionId}/tables/${tableName}/create-source`, data || {});
    return response.data;
  }

  // ==================== Sources ====================
  async getSources() {
    const response = await this.api.get('/api/sources');
    return response.data;
  }

  async getSource(id: string) {
    const response = await this.api.get(`/api/sources/${id}`);
    return response.data;
  }

  async createSource(data: Record<string, any>) {
    const response = await this.api.post('/api/sources', data);
    return response.data;
  }

  async updateSource(id: string, data: Record<string, any>) {
    const response = await this.api.put(`/api/sources/${id}`, data);
    return response.data;
  }

  async deleteSource(id: string) {
    const response = await this.api.delete(`/api/sources/${id}`);
    return response.data;
  }

  // ==================== Billing ====================
  async getPlans() {
    const response = await this.api.get('/api/billing/plans');
    return response.data;
  }

  async getCurrentSubscription() {
    const response = await this.api.get('/api/billing/current');
    return response.data;
  }

  async createCheckout(priceId: string, successUrl: string, cancelUrl: string) {
    const response = await this.api.post('/api/billing/checkout', { priceId, successUrl, cancelUrl });
    return response.data;
  }

  async createBillingPortal(returnUrl: string) {
    const response = await this.api.post('/api/billing/portal', { returnUrl });
    return response.data;
  }

  // ==================== Notifications ====================
  async listNotifications() {
    const response = await this.api.get('/api/notifications');
    return response.data;
  }

  async markNotificationRead(notificationId: string) {
    const response = await this.api.put(`/api/notifications/${notificationId}/read`);
    return response.data;
  }

  async markAllNotificationsRead() {
    const response = await this.api.post('/api/notifications/read-all');
    return response.data;
  }

  async getUnreadNotificationCount() {
    const response = await this.api.get('/api/notifications/unread-count');
    return response.data;
  }
}

const apiService = new ApiService();
export default apiService;
