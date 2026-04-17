import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardPage from '../DashboardPage';
import { useDocuments } from '../../context_providers/DocumentContext';
import { DocumentStatus, PipelineStatus } from '../../../types';

// ==================== Mocks ====================
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

jest.mock('../../context_providers/DocumentContext', () => ({
  useDocuments: jest.fn(),
}));

jest.mock('../../context_providers/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      firstName: 'Kevin',
      lastName: 'Singh',
      email: 'kevin@example.com',
      orgRole: 'admin' as const,
      isSuperAdmin: false,
      isActive: true,
      isVerified: true,
      status: 'active' as const,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    isAuthenticated: true,
    token: 'mock-token',
    isLoading: false,
  }),
}));

const mockUseDocuments = useDocuments as jest.Mock;

// ==================== Test Data ====================
const mockDocuments = [
  {
    id: 'doc-1',
    userId: 'user-1',
    fileName: 'report.pdf',
    originalFileName: 'report.pdf',
    fileType: 'pdf',
    fileSize: 102400,
    status: DocumentStatus.READY,
    uploadedAt: '2024-01-15T10:00:00Z',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: 'doc-2',
    userId: 'user-1',
    fileName: 'notes.txt',
    originalFileName: 'notes.txt',
    fileType: 'txt',
    fileSize: 2048,
    status: DocumentStatus.EXTRACTING,
    uploadedAt: '2024-01-16T10:00:00Z',
    createdAt: '2024-01-16T10:00:00Z',
    updatedAt: '2024-01-16T10:00:00Z',
  },
  {
    id: 'doc-3',
    userId: 'user-1',
    fileName: 'data.csv',
    originalFileName: 'data.csv',
    fileType: 'csv',
    fileSize: 51200,
    status: DocumentStatus.READY,
    uploadedAt: '2024-01-14T10:00:00Z',
    createdAt: '2024-01-14T10:00:00Z',
    updatedAt: '2024-01-14T10:00:00Z',
  },
];

const mockPipelines = [
  {
    id: 'pipe-1',
    userId: 'user-1',
    name: 'Invoice Extractor',
    description: 'Extracts invoice data',
    modelId: 'model-1',
    embeddingModelId: 'emb-1',
    documentIds: ['doc-1', 'doc-3'],
    status: PipelineStatus.COMPLETED,
    createdAt: '2024-01-17T10:00:00Z',
    updatedAt: '2024-01-17T10:00:00Z',
  },
  {
    id: 'pipe-2',
    userId: 'user-1',
    name: 'Resume Parser',
    description: 'Parses resume data',
    modelId: 'model-1',
    embeddingModelId: 'emb-1',
    documentIds: ['doc-2'],
    status: PipelineStatus.PROCESSING,
    createdAt: '2024-01-18T10:00:00Z',
    updatedAt: '2024-01-18T10:00:00Z',
  },
];

const mockModels = [
  {
    id: 'model-1',
    userId: 'user-1',
    name: 'GPT-4',
    modelId: 'gpt-4',
    modelType: 'chat' as const,
    provider: 'OPENAI' as const,
    temperature: 0.7,
    maxTokens: 4096,
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'emb-1',
    userId: 'user-1',
    name: 'Text Embedding',
    modelId: 'text-embedding-3-small',
    modelType: 'embedding' as const,
    provider: 'OPENAI' as const,
    temperature: 0,
    maxTokens: 8191,
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'model-inactive',
    userId: 'user-1',
    name: 'Disabled Model',
    modelId: 'old-model',
    modelType: 'chat' as const,
    provider: 'OPENAI' as const,
    temperature: 0.5,
    maxTokens: 2048,
    isActive: false,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

// ==================== Helpers ====================
const renderDashboard = () =>
  render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>
  );

const setupMock = (overrides: Partial<ReturnType<typeof useDocuments>> = {}) => {
  mockUseDocuments.mockReturnValue({
    documents: mockDocuments,
    documentsLoading: false,
    documentsError: null,
    pipelines: mockPipelines,
    pipelinesLoading: false,
    pipelinesError: null,
    models: mockModels,
    modelsLoading: false,
    modelsError: null,
    uploadDocument: jest.fn(),
    fetchDocuments: jest.fn(),
    deleteDocument: jest.fn(),
    fetchModels: jest.fn(),
    createModel: jest.fn(),
    updateModel: jest.fn(),
    deleteModel: jest.fn(),
    fetchPipelines: jest.fn(),
    createPipeline: jest.fn(),
    updatePipeline: jest.fn(),
    deletePipeline: jest.fn(),
    runPipeline: jest.fn(),
    queries: [],
    queriesLoading: false,
    queriesError: null,
    askQuestion: jest.fn(),
    fetchQueries: jest.fn(),
    ...overrides,
  });
};

// ==================== Tests ====================
beforeEach(() => {
  jest.clearAllMocks();
});

describe('DashboardPage', () => {
  describe('rendering', () => {
    it('renders the welcome message with user first name', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText(/Welcome back, Kevin/i)).toBeInTheDocument();
    });

    it('renders dashboard subtitle', () => {
      setupMock();
      renderDashboard();

      expect(
        screen.getByText(/Manage your documents, pipelines, and AI models from one place/i)
      ).toBeInTheDocument();
    });
  });

  describe('stat cards', () => {
    it('shows correct total document count', () => {
      setupMock();
      renderDashboard();

      // The stat card for documents should show 3
      expect(screen.getByText('Total Documents')).toBeInTheDocument();
      // The h3 with the count "3"
      const totalDocsLabel = screen.getByText('Total Documents');
      const card = totalDocsLabel.closest('[class*="MuiCardContent"]');
      expect(card).toHaveTextContent('3');
    });

    it('shows correct pipeline count', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText('Active Pipelines')).toBeInTheDocument();
      const pipelinesLabel = screen.getByText('Active Pipelines');
      const card = pipelinesLabel.closest('[class*="MuiCardContent"]');
      expect(card).toHaveTextContent('2');
    });

    it('shows correct ready document count filtering by READY status', () => {
      setupMock();
      renderDashboard();

      // 2 docs have READY status (doc-1, doc-3)
      expect(screen.getByText('Ready Documents')).toBeInTheDocument();
      const readyLabel = screen.getByText('Ready Documents');
      const card = readyLabel.closest('[class*="MuiCardContent"]');
      expect(card).toHaveTextContent('2');
    });

    it('shows correct active model count (excludes inactive)', () => {
      setupMock();
      renderDashboard();

      // 2 active models out of 3 total (one has isActive: false)
      expect(screen.getByText('Models')).toBeInTheDocument();
      const modelsLabel = screen.getByText('Models');
      const card = modelsLabel.closest('[class*="MuiCardContent"]');
      expect(card).toHaveTextContent('2');
    });
  });

  describe('recent documents table', () => {
    it('renders the Recent Documents heading', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText('Recent Documents')).toBeInTheDocument();
    });

    it('renders document filenames in the table', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText('report.pdf')).toBeInTheDocument();
      expect(screen.getByText('notes.txt')).toBeInTheDocument();
      expect(screen.getByText('data.csv')).toBeInTheDocument();
    });

    it('renders document status chips', () => {
      setupMock();
      renderDashboard();

      // READY appears twice (doc-1 and doc-3), EXTRACTING once (doc-2)
      const readyChips = screen.getAllByText(DocumentStatus.READY);
      expect(readyChips.length).toBe(2);
      expect(screen.getByText(DocumentStatus.EXTRACTING)).toBeInTheDocument();
    });

    it('renders formatted file sizes', () => {
      setupMock();
      renderDashboard();

      // 102400 bytes = 100.0 KB
      expect(screen.getByText('100.0 KB')).toBeInTheDocument();
      // 2048 bytes = 2.0 KB
      expect(screen.getByText('2.0 KB')).toBeInTheDocument();
      // 51200 bytes = 50.0 KB
      expect(screen.getByText('50.0 KB')).toBeInTheDocument();
    });
  });

  describe('recent pipelines table', () => {
    it('renders the Recent Pipelines heading', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText('Recent Pipelines')).toBeInTheDocument();
    });

    it('renders pipeline names in the table', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText('Invoice Extractor')).toBeInTheDocument();
      expect(screen.getByText('Resume Parser')).toBeInTheDocument();
    });

    it('renders pipeline document counts', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText('2 docs')).toBeInTheDocument();
      expect(screen.getByText('1 docs')).toBeInTheDocument();
    });

    it('renders pipeline status chips', () => {
      setupMock();
      renderDashboard();

      expect(screen.getByText(PipelineStatus.COMPLETED)).toBeInTheDocument();
      expect(screen.getByText(PipelineStatus.PROCESSING)).toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('shows loading spinner when all data is loading and arrays are empty', () => {
      setupMock({
        documents: [],
        documentsLoading: true,
        pipelines: [],
        pipelinesLoading: true,
        modelsLoading: true,
      });
      renderDashboard();

      expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
    });

    it('does not show loading spinner when documents already loaded', () => {
      setupMock({
        documentsLoading: true,
        // documents array is NOT empty so isLoading short-circuits
      });
      renderDashboard();

      expect(screen.queryByText('Loading dashboard...')).not.toBeInTheDocument();
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    });
  });

  describe('navigation', () => {
    it('navigates to /documents when Upload button is clicked', () => {
      setupMock();
      renderDashboard();

      const uploadButton = screen.getByRole('button', { name: /Upload/i });
      fireEvent.click(uploadButton);

      expect(mockNavigate).toHaveBeenCalledWith('/documents');
    });

    it('navigates to /pipelines when Create button is clicked', () => {
      setupMock();
      renderDashboard();

      const createButton = screen.getByRole('button', { name: /Create/i });
      fireEvent.click(createButton);

      expect(mockNavigate).toHaveBeenCalledWith('/pipelines');
    });
  });

  describe('empty state', () => {
    it('shows empty document message when no documents exist', () => {
      setupMock({ documents: [] });
      renderDashboard();

      expect(
        screen.getByText(/No documents yet. Upload your first document to get started./i)
      ).toBeInTheDocument();
    });

    it('shows empty pipeline message when no pipelines exist', () => {
      setupMock({ pipelines: [] });
      renderDashboard();

      expect(
        screen.getByText(/No pipelines yet. Create your first pipeline to start using RAG queries./i)
      ).toBeInTheDocument();
    });

    it('shows zero counts in stat cards when all data is empty', () => {
      setupMock({
        documents: [],
        pipelines: [],
        models: [],
      });
      renderDashboard();

      // All stat cards show 0
      const totalDocsCard = screen.getByText('Total Documents').closest('[class*="MuiCardContent"]');
      expect(totalDocsCard).toHaveTextContent('0');

      const pipelinesCard = screen.getByText('Active Pipelines').closest('[class*="MuiCardContent"]');
      expect(pipelinesCard).toHaveTextContent('0');

      const readyCard = screen.getByText('Ready Documents').closest('[class*="MuiCardContent"]');
      expect(readyCard).toHaveTextContent('0');

      const modelsCard = screen.getByText('Models').closest('[class*="MuiCardContent"]');
      expect(modelsCard).toHaveTextContent('0');
    });

    it('shows both empty states simultaneously', () => {
      setupMock({ documents: [], pipelines: [] });
      renderDashboard();

      expect(
        screen.getByText(/No documents yet. Upload your first document to get started./i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/No pipelines yet. Create your first pipeline to start using RAG queries./i)
      ).toBeInTheDocument();
    });
  });
});
