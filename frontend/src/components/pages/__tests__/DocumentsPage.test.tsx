import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DocumentsPage from '../DocumentsPage';
import { useDocuments } from '../../context_providers/DocumentContext';
import { DocumentStatus, ModelType, ModelProvider } from '../../../types';
import apiService from '../../../utils/api.service';

// ==================== Mocks ====================
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

jest.mock('../../context_providers/DocumentContext', () => ({
  useDocuments: jest.fn(),
}));

jest.mock('../../context_providers/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError,
    showWarning: mockShowWarning,
    showInfo: jest.fn(),
  }),
}));

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    getAllModels: jest.fn(),
  },
}));

const mockShowSuccess = jest.fn();
const mockShowError = jest.fn();
const mockShowWarning = jest.fn();
const mockUploadDocument = jest.fn();
const mockFetchDocuments = jest.fn();
const mockDeleteDocument = jest.fn();

const mockUseDocuments = useDocuments as jest.Mock;
const mockGetAllModels = apiService.getAllModels as jest.Mock;

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
];

const mockEmbeddingModels = [
  {
    id: 'emb-1',
    userId: 'user-1',
    name: 'Text Embedding 3 Small',
    modelId: 'text-embedding-3-small',
    modelType: ModelType.EMBEDDING,
    provider: ModelProvider.OPENAI,
    temperature: 0,
    maxTokens: 8191,
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'emb-2',
    userId: 'user-1',
    name: 'Text Embedding 3 Large',
    modelId: 'text-embedding-3-large',
    modelType: ModelType.EMBEDDING,
    provider: ModelProvider.OPENAI,
    temperature: 0,
    maxTokens: 8191,
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

// ==================== Helpers ====================
const renderDocumentsPage = () =>
  render(
    <MemoryRouter>
      <DocumentsPage />
    </MemoryRouter>
  );

const setupMock = (overrides: Record<string, any> = {}) => {
  mockUseDocuments.mockReturnValue({
    documents: mockDocuments,
    documentsLoading: false,
    documentsError: null,
    uploadDocument: mockUploadDocument,
    fetchDocuments: mockFetchDocuments,
    deleteDocument: mockDeleteDocument,
    models: [],
    modelsLoading: false,
    modelsError: null,
    pipelines: [],
    pipelinesLoading: false,
    pipelinesError: null,
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
  // Default: embedding models API returns our test models
  mockGetAllModels.mockResolvedValue({ data: mockEmbeddingModels });
  // Prevent window.confirm from blocking
  jest.spyOn(window, 'confirm').mockReturnValue(true);
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('DocumentsPage', () => {
  describe('rendering', () => {
    it('renders the page title "Documents"', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText('Documents')).toBeInTheDocument();
    });

    it('renders the page subtitle', () => {
      setupMock();
      renderDocumentsPage();

      expect(
        screen.getByText(/Upload and manage your documents for RAG processing/i)
      ).toBeInTheDocument();
    });

    it('renders the upload button', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });

    it('renders the All Documents section heading', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText('All Documents')).toBeInTheDocument();
    });
  });

  describe('documents table', () => {
    it('renders document filenames in the table', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText('report.pdf')).toBeInTheDocument();
      expect(screen.getByText('notes.txt')).toBeInTheDocument();
    });

    it('renders document status chips', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText(DocumentStatus.READY)).toBeInTheDocument();
      expect(screen.getByText(DocumentStatus.EXTRACTING)).toBeInTheDocument();
    });

    it('renders formatted file sizes', () => {
      setupMock();
      renderDocumentsPage();

      // 102400 bytes = 100.0 KB
      expect(screen.getByText('100.0 KB')).toBeInTheDocument();
      // 2048 bytes = 2.0 KB
      expect(screen.getByText('2.0 KB')).toBeInTheDocument();
    });

    it('renders file type chips', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText('PDF')).toBeInTheDocument();
      expect(screen.getByText('TXT')).toBeInTheDocument();
    });

    it('renders upload dates', () => {
      setupMock();
      renderDocumentsPage();

      // Date formatting depends on locale, but the dates should appear
      expect(screen.getByText(new Date('2024-01-15T10:00:00Z').toLocaleDateString())).toBeInTheDocument();
      expect(screen.getByText(new Date('2024-01-16T10:00:00Z').toLocaleDateString())).toBeInTheDocument();
    });

    it('renders table headers', () => {
      setupMock();
      renderDocumentsPage();

      expect(screen.getByText('File Name')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Size')).toBeInTheDocument();
      expect(screen.getByText('Uploaded')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('shows empty state message when no documents exist', () => {
      setupMock({ documents: [] });
      renderDocumentsPage();

      expect(screen.getByText('No documents yet')).toBeInTheDocument();
      expect(
        screen.getByText(/Upload your first document to get started with RAG processing/i)
      ).toBeInTheDocument();
    });

    it('does not render table when documents are empty', () => {
      setupMock({ documents: [] });
      renderDocumentsPage();

      expect(screen.queryByText('File Name')).not.toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('shows loading spinner when documentsLoading is true and documents array is empty', () => {
      setupMock({ documentsLoading: true, documents: [] });
      renderDocumentsPage();

      expect(screen.getByText('Loading documents...')).toBeInTheDocument();
    });

    it('does not show loading spinner when documents already loaded', () => {
      setupMock({ documentsLoading: true });
      renderDocumentsPage();

      // Documents are loaded so the page renders normally even if loading is true
      expect(screen.queryByText('Loading documents...')).not.toBeInTheDocument();
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });
  });

  describe('delete functionality', () => {
    it('calls window.confirm when delete button is clicked', () => {
      setupMock();
      renderDocumentsPage();

      const deleteButtons = screen.getAllByTitle('Delete document');
      fireEvent.click(deleteButtons[0]);

      expect(window.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this document?'
      );
    });

    it('calls deleteDocument when user confirms deletion', async () => {
      mockDeleteDocument.mockResolvedValue(undefined);
      setupMock();
      renderDocumentsPage();

      const deleteButtons = screen.getAllByTitle('Delete document');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockDeleteDocument).toHaveBeenCalledWith('doc-1');
      });
    });

    it('shows success notification after successful deletion', async () => {
      mockDeleteDocument.mockResolvedValue(undefined);
      setupMock();
      renderDocumentsPage();

      const deleteButtons = screen.getAllByTitle('Delete document');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockShowSuccess).toHaveBeenCalledWith('Document deleted successfully');
      });
    });

    it('does not call deleteDocument when user cancels', () => {
      (window.confirm as jest.Mock).mockReturnValue(false);
      setupMock();
      renderDocumentsPage();

      const deleteButtons = screen.getAllByTitle('Delete document');
      fireEvent.click(deleteButtons[0]);

      expect(mockDeleteDocument).not.toHaveBeenCalled();
    });

    it('shows error notification when deletion fails', async () => {
      mockDeleteDocument.mockRejectedValue(new Error('Server error'));
      setupMock();
      renderDocumentsPage();

      const deleteButtons = screen.getAllByTitle('Delete document');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockShowError).toHaveBeenCalledWith('Delete failed: Server error');
      });
    });
  });

  describe('upload dialog', () => {
    it('opens upload dialog when a file is selected via input', async () => {
      setupMock();
      renderDocumentsPage();

      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      expect(fileInput).toBeTruthy();

      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('Upload Document', { selector: '[class*="MuiDialogTitle"]' })).toBeInTheDocument();
      });
    });

    it('shows selected file name in dialog', async () => {
      setupMock();
      renderDocumentsPage();

      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      const testFile = new File(['test content'], 'my-report.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('my-report.pdf')).toBeInTheDocument();
      });
    });

    it('shows embedding model selector in dialog', async () => {
      setupMock();
      renderDocumentsPage();

      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('Embedding Model')).toBeInTheDocument();
      });
    });

    it('has Upload button disabled when no embedding model is selected', async () => {
      setupMock();
      renderDocumentsPage();

      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        // The Upload button in the dialog (not the page-level upload button)
        const dialogActions = screen.getByText('Upload Document', { selector: '[class*="MuiDialogTitle"]' })
          .closest('[class*="MuiDialog-root"]');
        const uploadBtn = dialogActions?.querySelector('button[class*="MuiButton-contained"]');
        expect(uploadBtn).toBeDisabled();
      });
    });

    it('closes dialog when Cancel button is clicked', async () => {
      setupMock();
      renderDocumentsPage();

      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(screen.getByText('Upload Document', { selector: '[class*="MuiDialogTitle"]' })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));

      await waitFor(() => {
        expect(screen.queryByText('Upload Document', { selector: '[class*="MuiDialogTitle"]' })).not.toBeInTheDocument();
      });
    });
  });

  describe('embedding models loading', () => {
    it('fetches embedding models on mount', () => {
      setupMock();
      renderDocumentsPage();

      expect(mockGetAllModels).toHaveBeenCalledWith('embedding');
    });

    it('shows warning when no embedding models are available', async () => {
      mockGetAllModels.mockResolvedValue({ data: [] });
      setupMock();
      renderDocumentsPage();

      // Open the upload dialog
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      await waitFor(() => {
        expect(
          screen.getByText(/No embedding models available/i)
        ).toBeInTheDocument();
      });
    });

    it('handles API error when loading models gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      mockGetAllModels.mockRejectedValue(new Error('Network error'));
      setupMock();
      renderDocumentsPage();

      // Page should still render without crashing
      await waitFor(() => {
        expect(screen.getByText('Documents')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('supported formats info', () => {
    it('displays supported file format information', () => {
      setupMock();
      renderDocumentsPage();

      expect(
        screen.getByText(/Supported formats: PDF, Word/i)
      ).toBeInTheDocument();
    });
  });
});
