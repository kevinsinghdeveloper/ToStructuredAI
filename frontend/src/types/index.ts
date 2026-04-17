// ==================== Enums & Constants ====================
export type OrgRole = 'owner' | 'admin' | 'manager' | 'member';
export type GlobalRole = 'global_admin' | 'user';
export type UserStatus = 'invited' | 'active' | 'deactivated';
export type PlanTier = 'free' | 'starter' | 'professional' | 'enterprise';
export type NotificationType = 'document_processed' | 'pipeline_completed' | 'pipeline_failed' | 'usage_limit' | 'org_invitation' | 'member_joined' | 'system';

export const ORG_ROLE_HIERARCHY: OrgRole[] = ['member', 'manager', 'admin', 'owner'];

export const ORG_ROLE_PERMISSIONS: Record<OrgRole, string[]> = {
  member: ['upload_documents', 'view_own_documents', 'run_pipelines', 'ask_questions'],
  manager: ['upload_documents', 'view_own_documents', 'run_pipelines', 'ask_questions', 'view_team_documents', 'manage_models'],
  admin: ['upload_documents', 'view_own_documents', 'run_pipelines', 'ask_questions', 'view_team_documents', 'manage_models', 'manage_pipelines', 'manage_users', 'view_usage'],
  owner: ['upload_documents', 'view_own_documents', 'run_pipelines', 'ask_questions', 'view_team_documents', 'manage_models', 'manage_pipelines', 'manage_users', 'view_usage', 'manage_billing', 'manage_org'],
};

// ==================== User Types ====================
export interface User {
  id: string;
  email: string;
  username?: string;
  firstName: string;
  lastName: string;
  orgId?: string;
  orgRole: OrgRole;
  isSuperAdmin: boolean;
  isActive: boolean;
  isVerified: boolean;
  status: UserStatus;
  avatarUrl?: string;
  phone?: string;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
  currentPlanId?: string;
  subscriptionStatus?: string;
  notificationPreferences?: NotificationPreferences;
  oauthProviders?: Record<string, { provider_user_id: string; linked_at: string }>;
  mustResetPassword?: boolean;
  orgMemberships?: OrgMembership[];
  createdAt: string;
  updatedAt: string;
}

export interface OrgMembership {
  orgId: string;
  roles: OrgRole[];
  grantedAt: string;
}

export interface NotificationPreferences {
  emailDocumentProcessed: boolean;
  emailPipelineCompleted: boolean;
  inAppNotifications: boolean;
  desktopNotifications: boolean;
}

export interface UserPreferences {
  notificationPreferences: NotificationPreferences;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  refreshToken?: string;
  accessToken?: string;
  user: User;
  challengeName?: string;
  session?: string;
  email?: string;
}

// ==================== Organization Types ====================
export interface Organization {
  id: string;
  name: string;
  slug: string;
  ownerId: string;
  planTier: PlanTier;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
  logoUrl?: string;
  settings?: OrgSettings;
  memberCount: number;
  isActive: boolean;
  userRoles?: OrgRole[];
  createdAt: string;
  updatedAt: string;
}

export interface OrgSettings {
  defaultEmbeddingModel?: string;
  maxFileSizeMb: number;
}

export interface OrgInvite {
  id: string;
  orgId: string;
  email: string;
  role: OrgRole;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  invitedBy: string;
  expiresAt: string;
  acceptedAt?: string;
  createdAt: string;
}

// ==================== Document Types ====================
export interface Document {
  id: string;
  userId: string;
  embeddingModelId?: string;
  fileName: string;
  originalFileName: string;
  fileType: string;
  fileSize: number;
  status: DocumentStatus;
  chunkCount?: number;
  metadata?: Record<string, any>;
  uploadedAt: string;
  processingStartedAt?: string;
  processingCompletedAt?: string;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
}

export enum DocumentStatus {
  UPLOADED = 'UPLOADED',
  EXTRACTING = 'EXTRACTING',
  EMBEDDING = 'EMBEDDING',
  READY = 'READY',
  ERROR = 'ERROR',
}

// ==================== Model Types ====================
export interface ModelConfig {
  id: string;
  userId: string;
  name: string;
  modelId: string;
  modelType: ModelType;
  provider: ModelProvider;
  temperature: number;
  maxTokens: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  isActive?: boolean;
  hasApiKey?: boolean;
  config?: string;
  createdAt: string;
  updatedAt: string;
}

export enum ModelType {
  CHAT = 'chat',
  EMBEDDING = 'embedding',
}

export enum ModelProvider {
  OPENAI = 'OPENAI',
  ANTHROPIC = 'ANTHROPIC',
  CUSTOM = 'CUSTOM',
}

// ==================== Pipeline Types ====================
export interface PipelineType {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  supports_chat: boolean;
  supports_extraction: boolean;
  default_fields?: PipelineField[];
  prompt_template?: string;
  output_schema?: any;
}

export interface PipelineField {
  id: string;
  name: string;
  description: string;
  field_type: 'text' | 'number' | 'date' | 'datetime' | 'boolean' | 'array' | 'object' | 'code';
  required: boolean;
  default_enabled: boolean;
  validation?: Record<string, any>;
  item_schema?: PipelineField[];
}

export interface FieldType {
  name: string;
  description: string;
  json_type: string;
  format?: string;
}

export interface RAGPipeline {
  id: string;
  userId: string;
  name: string;
  description?: string;
  modelId: string;
  embeddingModelId: string;
  documentIds: string[];
  sourceIds?: string[];
  pipelineType?: string;
  config?: Record<string, any>;
  promptTemplate?: string;
  outputSchema?: any;
  status: PipelineStatus;
  createdAt: string;
  updatedAt: string;
}

export enum PipelineStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// ==================== Output Types ====================
export interface StructuredOutput {
  id: string;
  pipelineId: string;
  outputData: any;
  filePath?: string;
  format: OutputFormat;
  createdAt: string;
}

export enum OutputFormat {
  CSV = 'CSV',
  JSON = 'JSON',
  EXCEL = 'EXCEL',
  XML = 'XML',
}

// ==================== Database Connection Types ====================
export interface DatabaseConnection {
  id: string;
  userId: string;
  name: string;
  dbType: string;
  host?: string;
  port?: number;
  databaseName?: string;
  username?: string;
  sslEnabled: boolean;
  schemaName: string;
  status: 'untested' | 'connected' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export interface ConnectionTable {
  name: string;
  schema: string;
}

export interface ConnectionTableSchema {
  table_name: string;
  columns: ColumnSchema[];
  row_count: number;
}

export interface ColumnSchema {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default?: string | null;
  description?: string;
}

// ==================== Source Types ====================
export interface Source {
  id: string;
  userId: string;
  name: string;
  sourceType: 'document' | 'database';
  isQueryable: boolean;
  status: 'pending' | 'ready' | 'metadata_extracted' | 'error';
  documentId?: string;
  connectionId?: string;
  tableName?: string;
  sqlViewQuery?: string;
  metadataJson?: string;
  delimiter?: string;
  createdAt: string;
  updatedAt: string;
}

// ==================== Query Types ====================
export interface Query {
  id: string;
  userId: string;
  pipelineId: string;
  question: string;
  answer: string;
  context?: string;
  sources?: string[];
  confidence?: number;
  metadata?: Record<string, any>;
  sql?: string;
  sqlExplanation?: string;
  sqlResults?: Record<string, any>[];
  createdAt: string;
}

// ==================== Billing Types ====================
export interface PlanDetails {
  id: string;
  name: string;
  tier: PlanTier;
  stripePriceId?: string;
  priceMonthly: number;
  priceYearly: number;
  customModelsLimit: number;
  monthlyTokenLimit: number | null;
  maxFileSizeMb: number;
  requestsPerDay: number | null;
  canUseMetadata: boolean;
  canUseCustomModels: boolean;
  prioritySupport: boolean;
  features: string[];
  isActive: boolean;
}

export interface Subscription {
  planTier: PlanTier;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
  subscriptionStatus?: string;
  currentPlan?: PlanDetails;
}

// ==================== Notification Types ====================
export interface AppNotification {
  userId: string;
  id: string;
  orgId?: string;
  type: NotificationType;
  title: string;
  message: string;
  isRead: boolean;
  actionUrl?: string;
  createdAt: string;
}

// ==================== Theme Config Types ====================
export interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    tertiary?: string;
    background?: string;
    paper?: string;
  };
  logo?: string;
  appName: string;
  favicon?: string;
  mode?: 'dark' | 'light';
}

// ==================== API Response Types ====================
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ==================== Audit Types ====================
export interface AuditLogEntry {
  id: string;
  userId: string;
  orgId?: string;
  action: string;
  resource: string;
  resourceId?: string;
  details?: Record<string, any>;
  timestamp: string;
  ipAddress?: string;
}
