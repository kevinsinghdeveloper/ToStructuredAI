const apiService = {
  // Auth
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  respondToChallenge: jest.fn(),
  requestPasswordReset: jest.fn(),
  resetPassword: jest.fn(),
  verifyEmail: jest.fn(),
  acceptInvitation: jest.fn(),
  getOAuthUrl: jest.fn(),
  oauthCallback: jest.fn(),

  // Users
  getCurrentUser: jest.fn(),
  listUsers: jest.fn(),
  updateUserRole: jest.fn(),
  updateUser: jest.fn(),
  deleteUser: jest.fn(),
  updatePreferences: jest.fn(),

  // Organizations
  getCurrentOrg: jest.fn(),
  updateOrg: jest.fn(),
  createOrg: jest.fn(),
  listOrgInvitations: jest.fn(),
  createOrgInvitation: jest.fn(),
  deleteOrgInvitation: jest.fn(),
  listOrgMembers: jest.fn(),
  updateMemberRole: jest.fn(),
  removeMember: jest.fn(),

  // Projects
  listProjects: jest.fn(),
  createProject: jest.fn(),
  getProject: jest.fn(),
  updateProject: jest.fn(),
  deleteProject: jest.fn(),
  listProjectTasks: jest.fn(),
  createProjectTask: jest.fn(),
  updateProjectTask: jest.fn(),
  deleteProjectTask: jest.fn(),
  getProjectBudget: jest.fn(),

  // Clients
  listClients: jest.fn(),
  createClient: jest.fn(),
  getClient: jest.fn(),
  updateClient: jest.fn(),
  deleteClient: jest.fn(),
  getClientProjects: jest.fn(),

  // Time Entries
  listTimeEntries: jest.fn(),
  createTimeEntry: jest.fn(),
  bulkCreateTimeEntries: jest.fn(),
  getTimeEntry: jest.fn(),
  updateTimeEntry: jest.fn(),
  deleteTimeEntry: jest.fn(),
  startTimer: jest.fn(),
  stopTimer: jest.fn(),
  getCurrentTimer: jest.fn(),
  discardTimer: jest.fn(),
  getDayEntries: jest.fn(),
  getWeekEntries: jest.fn(),
  getMonthEntries: jest.fn(),
  listNarratives: jest.fn(),
  createNarrative: jest.fn(),
  updateNarrative: jest.fn(),
  deleteNarrative: jest.fn(),

  // Timesheets
  listTimesheets: jest.fn(),
  getTimesheet: jest.fn(),
  submitTimesheet: jest.fn(),
  unsubmitTimesheet: jest.fn(),
  getPendingTimesheets: jest.fn(),
  approveTimesheet: jest.fn(),
  rejectTimesheet: jest.fn(),
  getTeamTimesheets: jest.fn(),

  // Reports
  getReportSummary: jest.fn(),
  getReportByProject: jest.fn(),
  getReportByUser: jest.fn(),
  getReportByClient: jest.fn(),
  getReportByDate: jest.fn(),
  getUtilizationReport: jest.fn(),
  getBudgetReport: jest.fn(),
  exportReport: jest.fn(),

  // Dashboard
  getPersonalDashboard: jest.fn(),
  getTeamDashboard: jest.fn(),
  getOrgDashboard: jest.fn(),

  // AI Chat
  listChatSessions: jest.fn(),
  createChatSession: jest.fn(),
  getChatSession: jest.fn(),
  deleteChatSession: jest.fn(),
  listChatMessages: jest.fn(),
  sendChatMessage: jest.fn(),
  suggestTimeEntry: jest.fn(),
  categorizeEntry: jest.fn(),
  listAIModels: jest.fn(),
  updateAIModel: jest.fn(),
  deleteAIModelConfig: jest.fn(),

  // Billing
  getPlans: jest.fn(),
  getCurrentSubscription: jest.fn(),
  createCheckout: jest.fn(),
  createBillingPortal: jest.fn(),

  // Notifications
  listNotifications: jest.fn(),
  markNotificationRead: jest.fn(),
  markAllNotificationsRead: jest.fn(),
  getUnreadNotificationCount: jest.fn(),

  // Super Admin
  superAdminListOrgs: jest.fn(),
  superAdminListUsers: jest.fn(),
  superAdminGetStats: jest.fn(),
  superAdminUpdateOrg: jest.fn(),
  superAdminToggleUser: jest.fn(),

  // Config
  getThemeConfig: jest.fn(),
  saveThemeConfig: jest.fn(),
  getSettings: jest.fn(),
  saveSettings: jest.fn(),

  // Audit
  getAuditLogs: jest.fn(),
};

export default apiService;
