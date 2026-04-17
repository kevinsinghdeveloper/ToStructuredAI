/* eslint-disable import/first */
import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { DocumentContextProvider, useDocuments } from '../DocumentContext';

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    getAllDocuments: jest.fn(),
    uploadDocument: jest.fn(),
    deleteDocument: jest.fn(),
    getAllModels: jest.fn(),
    createModel: jest.fn(),
    updateModel: jest.fn(),
    deleteModel: jest.fn(),
    getAllPipelines: jest.fn(),
    createPipeline: jest.fn(),
    updatePipeline: jest.fn(),
    deletePipeline: jest.fn(),
    runPipeline: jest.fn(),
    getQueries: jest.fn(),
    askQuestion: jest.fn(),
  },
}));

jest.mock('../AuthContext', () => ({
  useAuth: jest.fn(),
}));

import apiService from '../../../utils/api.service';
import { useAuth } from '../AuthContext';

const mockUseAuth = useAuth as jest.Mock;

const mockGetAllDocuments = apiService.getAllDocuments as jest.Mock;
const mockUploadDocument = apiService.uploadDocument as jest.Mock;
const mockDeleteDocument = apiService.deleteDocument as jest.Mock;

const mockGetAllModels = apiService.getAllModels as jest.Mock;
const mockCreateModel = apiService.createModel as jest.Mock;
const mockUpdateModel = apiService.updateModel as jest.Mock;
const mockDeleteModel = apiService.deleteModel as jest.Mock;

const mockGetAllPipelines = apiService.getAllPipelines as jest.Mock;
const mockCreatePipeline = apiService.createPipeline as jest.Mock;
const mockUpdatePipeline = apiService.updatePipeline as jest.Mock;
const mockDeletePipeline = apiService.deletePipeline as jest.Mock;
const mockRunPipeline = apiService.runPipeline as jest.Mock;

const mockGetQueries = apiService.getQueries as jest.Mock;
const mockAskQuestion = apiService.askQuestion as jest.Mock;

// -- Test fixtures --

const mockDocument = {
  id: 'doc-1',
  userId: 'user-1',
  embeddingModelId: 'emb-1',
  fileName: 'test.pdf',
  originalFileName: 'test.pdf',
  fileType: 'application/pdf',
  fileSize: 1024,
  status: 'READY',
  chunkCount: 10,
  uploadedAt: '2025-06-01T00:00:00Z',
  createdAt: '2025-06-01T00:00:00Z',
  updatedAt: '2025-06-01T00:00:00Z',
};

const mockDocument2 = {
  ...mockDocument,
  id: 'doc-2',
  fileName: 'test2.pdf',
  originalFileName: 'test2.pdf',
};

const mockModel = {
  id: 'model-1',
  userId: 'user-1',
  name: 'GPT-4',
  modelId: 'gpt-4',
  modelType: 'chat',
  provider: 'OPENAI',
  temperature: 0.7,
  maxTokens: 4096,
  isActive: true,
  createdAt: '2025-06-01T00:00:00Z',
  updatedAt: '2025-06-01T00:00:00Z',
};

const mockModel2 = {
  ...mockModel,
  id: 'model-2',
  name: 'Claude',
  modelId: 'claude-3',
  provider: 'ANTHROPIC',
};

const mockPipeline = {
  id: 'pipe-1',
  userId: 'user-1',
  name: 'Test Pipeline',
  description: 'A test pipeline',
  modelId: 'model-1',
  embeddingModelId: 'emb-1',
  documentIds: ['doc-1'],
  status: 'pending',
  createdAt: '2025-06-01T00:00:00Z',
  updatedAt: '2025-06-01T00:00:00Z',
};

const mockPipeline2 = {
  ...mockPipeline,
  id: 'pipe-2',
  name: 'Another Pipeline',
};

const mockQuery = {
  id: 'query-1',
  userId: 'user-1',
  pipelineId: 'pipe-1',
  question: 'What is this about?',
  answer: 'This is about testing.',
  sources: ['doc-1'],
  confidence: 0.95,
  createdAt: '2025-06-01T00:00:00Z',
};

// -- Helpers --

const createWrapper = () => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <DocumentContextProvider>{children}</DocumentContextProvider>
  );
  return Wrapper;
};

/**
 * Renders the hook with isAuthenticated=false (default) so the useEffect
 * does not trigger auto-fetch. Use renderAuthenticatedHook for auto-fetch tests.
 */
const renderUnauthenticatedHook = () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
  // Resolve all fetches to empty arrays to avoid unhandled rejections
  mockGetAllDocuments.mockResolvedValue({ data: [] });
  mockGetAllModels.mockResolvedValue({ data: [] });
  mockGetAllPipelines.mockResolvedValue({ data: [] });
  return renderHook(() => useDocuments(), { wrapper: createWrapper() });
};

const renderAuthenticatedHook = () => {
  mockUseAuth.mockReturnValue({ isAuthenticated: true });
  mockGetAllDocuments.mockResolvedValue({ data: [] });
  mockGetAllModels.mockResolvedValue({ data: [] });
  mockGetAllPipelines.mockResolvedValue({ data: [] });
  return renderHook(() => useDocuments(), { wrapper: createWrapper() });
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe('DocumentContext', () => {
  // ============================================================
  // useDocuments hook guard
  // ============================================================
  describe('useDocuments hook', () => {
    it('throws when used outside of DocumentContextProvider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      expect(() => {
        renderHook(() => useDocuments());
      }).toThrow('useDocuments must be used within a DocumentContextProvider');
      consoleSpy.mockRestore();
    });
  });

  // ============================================================
  // Initial state
  // ============================================================
  describe('initial state', () => {
    it('has empty arrays, loading false, and no errors', () => {
      const { result } = renderUnauthenticatedHook();

      expect(result.current.documents).toEqual([]);
      expect(result.current.documentsLoading).toBe(false);
      expect(result.current.documentsError).toBeNull();

      expect(result.current.models).toEqual([]);
      expect(result.current.modelsLoading).toBe(false);
      expect(result.current.modelsError).toBeNull();

      expect(result.current.pipelines).toEqual([]);
      expect(result.current.pipelinesLoading).toBe(false);
      expect(result.current.pipelinesError).toBeNull();

      expect(result.current.queries).toEqual([]);
      expect(result.current.queriesLoading).toBe(false);
      expect(result.current.queriesError).toBeNull();
    });
  });

  // ============================================================
  // Auto-fetch on authentication
  // ============================================================
  describe('auto-fetch on authentication', () => {
    it('calls getAllDocuments, getAllModels, getAllPipelines when isAuthenticated is true', async () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
      mockGetAllDocuments.mockResolvedValue({ data: [mockDocument] });
      mockGetAllModels.mockResolvedValue({ data: [mockModel] });
      mockGetAllPipelines.mockResolvedValue({ data: [mockPipeline] });

      const { result } = renderHook(() => useDocuments(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.documentsLoading).toBe(false);
      });

      expect(mockGetAllDocuments).toHaveBeenCalledTimes(1);
      expect(mockGetAllModels).toHaveBeenCalledTimes(1);
      expect(mockGetAllPipelines).toHaveBeenCalledTimes(1);

      expect(result.current.documents).toEqual([mockDocument]);
      expect(result.current.models).toEqual([mockModel]);
      expect(result.current.pipelines).toEqual([mockPipeline]);
    });

    it('does NOT call any API when isAuthenticated is false', () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: false });
      renderHook(() => useDocuments(), { wrapper: createWrapper() });

      expect(mockGetAllDocuments).not.toHaveBeenCalled();
      expect(mockGetAllModels).not.toHaveBeenCalled();
      expect(mockGetAllPipelines).not.toHaveBeenCalled();
    });
  });

  // ============================================================
  // Documents
  // ============================================================
  describe('fetchDocuments', () => {
    it('sets documents from data wrapper response', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllDocuments.mockResolvedValue({ data: [mockDocument, mockDocument2] });

      await act(async () => {
        await result.current.fetchDocuments();
      });

      expect(result.current.documents).toEqual([mockDocument, mockDocument2]);
      expect(result.current.documentsLoading).toBe(false);
      expect(result.current.documentsError).toBeNull();
    });

    it('sets documents from flat response (no data wrapper)', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllDocuments.mockResolvedValue([mockDocument]);

      await act(async () => {
        await result.current.fetchDocuments();
      });

      expect(result.current.documents).toEqual([mockDocument]);
    });

    it('sets documentsError on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllDocuments.mockRejectedValue(new Error('Network error'));

      await act(async () => {
        await result.current.fetchDocuments();
      });

      expect(result.current.documentsError).toBe('Network error');
      expect(result.current.documentsLoading).toBe(false);
    });

    it('uses default error message when error has no message', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllDocuments.mockRejectedValue({});

      await act(async () => {
        await result.current.fetchDocuments();
      });

      expect(result.current.documentsError).toBe('Failed to fetch documents');
    });
  });

  describe('uploadDocument', () => {
    it('adds uploaded document to front of list and returns it', async () => {
      const { result } = renderUnauthenticatedHook();

      const mockFile = new File(['content'], 'upload.pdf', { type: 'application/pdf' });
      mockUploadDocument.mockResolvedValue({ data: mockDocument });

      let returnedDoc: any;
      await act(async () => {
        returnedDoc = await result.current.uploadDocument(mockFile, 'emb-1', false);
      });

      expect(mockUploadDocument).toHaveBeenCalledWith(mockFile, 'emb-1', false);
      expect(returnedDoc).toEqual(mockDocument);
      expect(result.current.documents[0]).toEqual(mockDocument);
      expect(result.current.documentsLoading).toBe(false);
      expect(result.current.documentsError).toBeNull();
    });

    it('handles flat response (no data wrapper)', async () => {
      const { result } = renderUnauthenticatedHook();

      const mockFile = new File(['content'], 'upload.pdf', { type: 'application/pdf' });
      mockUploadDocument.mockResolvedValue(mockDocument);

      let returnedDoc: any;
      await act(async () => {
        returnedDoc = await result.current.uploadDocument(mockFile, 'emb-1');
      });

      expect(returnedDoc).toEqual(mockDocument);
      expect(result.current.documents[0]).toEqual(mockDocument);
    });

    it('sets documentsError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      const mockFile = new File(['content'], 'upload.pdf', { type: 'application/pdf' });
      const uploadError = new Error('Upload failed');
      mockUploadDocument.mockRejectedValue(uploadError);

      await act(async () => {
        await expect(
          result.current.uploadDocument(mockFile, 'emb-1')
        ).rejects.toThrow('Upload failed');
      });

      expect(result.current.documentsError).toBe('Upload failed');
      expect(result.current.documentsLoading).toBe(false);
    });
  });

  describe('deleteDocument', () => {
    it('removes document from list on success', async () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
      mockGetAllDocuments.mockResolvedValue({ data: [mockDocument, mockDocument2] });
      mockGetAllModels.mockResolvedValue({ data: [] });
      mockGetAllPipelines.mockResolvedValue({ data: [] });
      mockDeleteDocument.mockResolvedValue({});

      const { result } = renderHook(() => useDocuments(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.documents).toHaveLength(2);
      });

      await act(async () => {
        await result.current.deleteDocument('doc-1');
      });

      expect(mockDeleteDocument).toHaveBeenCalledWith('doc-1');
      expect(result.current.documents).toHaveLength(1);
      expect(result.current.documents[0].id).toBe('doc-2');
      expect(result.current.documentsLoading).toBe(false);
    });

    it('sets documentsError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockDeleteDocument.mockRejectedValue(new Error('Delete failed'));

      await act(async () => {
        await expect(
          result.current.deleteDocument('doc-1')
        ).rejects.toThrow('Delete failed');
      });

      expect(result.current.documentsError).toBe('Delete failed');
      expect(result.current.documentsLoading).toBe(false);
    });

    it('uses default error message when error has no message', async () => {
      const { result } = renderUnauthenticatedHook();

      mockDeleteDocument.mockRejectedValue({});

      await act(async () => {
        await expect(
          result.current.deleteDocument('doc-1')
        ).rejects.toThrow('Failed to delete document');
      });

      expect(result.current.documentsError).toBe('Failed to delete document');
    });
  });

  // ============================================================
  // Models
  // ============================================================
  describe('fetchModels', () => {
    it('sets models from data wrapper response', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllModels.mockResolvedValue({ data: [mockModel, mockModel2] });

      await act(async () => {
        await result.current.fetchModels();
      });

      expect(result.current.models).toEqual([mockModel, mockModel2]);
      expect(result.current.modelsLoading).toBe(false);
      expect(result.current.modelsError).toBeNull();
    });

    it('sets modelsError on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllModels.mockRejectedValue(new Error('Models fetch error'));

      await act(async () => {
        await result.current.fetchModels();
      });

      expect(result.current.modelsError).toBe('Models fetch error');
      expect(result.current.modelsLoading).toBe(false);
    });
  });

  describe('createModel', () => {
    it('adds new model to front of list and returns it', async () => {
      const { result } = renderUnauthenticatedHook();

      mockCreateModel.mockResolvedValue({ data: mockModel });

      let returnedModel: any;
      await act(async () => {
        returnedModel = await result.current.createModel({ name: 'GPT-4' });
      });

      expect(mockCreateModel).toHaveBeenCalledWith({ name: 'GPT-4' });
      expect(returnedModel).toEqual(mockModel);
      expect(result.current.models[0]).toEqual(mockModel);
      expect(result.current.modelsLoading).toBe(false);
    });

    it('sets modelsError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockCreateModel.mockRejectedValue(new Error('Create failed'));

      await act(async () => {
        await expect(
          result.current.createModel({ name: 'Bad Model' })
        ).rejects.toThrow('Create failed');
      });

      expect(result.current.modelsError).toBe('Create failed');
      expect(result.current.modelsLoading).toBe(false);
    });
  });

  describe('updateModel', () => {
    it('replaces updated model in list and returns it', async () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
      mockGetAllDocuments.mockResolvedValue({ data: [] });
      mockGetAllModels.mockResolvedValue({ data: [mockModel, mockModel2] });
      mockGetAllPipelines.mockResolvedValue({ data: [] });

      const updatedModel = { ...mockModel, name: 'GPT-4 Turbo' };
      mockUpdateModel.mockResolvedValue({ data: updatedModel });

      const { result } = renderHook(() => useDocuments(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.models).toHaveLength(2);
      });

      let returnedModel: any;
      await act(async () => {
        returnedModel = await result.current.updateModel('model-1', { name: 'GPT-4 Turbo' });
      });

      expect(mockUpdateModel).toHaveBeenCalledWith('model-1', { name: 'GPT-4 Turbo' });
      expect(returnedModel).toEqual(updatedModel);
      expect(result.current.models.find((m) => m.id === 'model-1')?.name).toBe('GPT-4 Turbo');
      expect(result.current.models).toHaveLength(2);
    });

    it('sets modelsError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockUpdateModel.mockRejectedValue(new Error('Update failed'));

      await act(async () => {
        await expect(
          result.current.updateModel('model-1', { name: 'Bad Update' })
        ).rejects.toThrow('Update failed');
      });

      expect(result.current.modelsError).toBe('Update failed');
    });
  });

  describe('deleteModel', () => {
    it('removes model from list on success', async () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
      mockGetAllDocuments.mockResolvedValue({ data: [] });
      mockGetAllModels.mockResolvedValue({ data: [mockModel, mockModel2] });
      mockGetAllPipelines.mockResolvedValue({ data: [] });
      mockDeleteModel.mockResolvedValue({});

      const { result } = renderHook(() => useDocuments(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.models).toHaveLength(2);
      });

      await act(async () => {
        await result.current.deleteModel('model-1');
      });

      expect(mockDeleteModel).toHaveBeenCalledWith('model-1');
      expect(result.current.models).toHaveLength(1);
      expect(result.current.models[0].id).toBe('model-2');
    });

    it('sets modelsError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockDeleteModel.mockRejectedValue(new Error('Delete model failed'));

      await act(async () => {
        await expect(
          result.current.deleteModel('model-1')
        ).rejects.toThrow('Delete model failed');
      });

      expect(result.current.modelsError).toBe('Delete model failed');
      expect(result.current.modelsLoading).toBe(false);
    });
  });

  // ============================================================
  // Pipelines
  // ============================================================
  describe('fetchPipelines', () => {
    it('sets pipelines from data wrapper response', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllPipelines.mockResolvedValue({ data: [mockPipeline, mockPipeline2] });

      await act(async () => {
        await result.current.fetchPipelines();
      });

      expect(result.current.pipelines).toEqual([mockPipeline, mockPipeline2]);
      expect(result.current.pipelinesLoading).toBe(false);
      expect(result.current.pipelinesError).toBeNull();
    });

    it('sets pipelinesError on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllPipelines.mockRejectedValue(new Error('Pipelines fetch error'));

      await act(async () => {
        await result.current.fetchPipelines();
      });

      expect(result.current.pipelinesError).toBe('Pipelines fetch error');
      expect(result.current.pipelinesLoading).toBe(false);
    });
  });

  describe('createPipeline', () => {
    it('adds new pipeline to front of list and returns it', async () => {
      const { result } = renderUnauthenticatedHook();

      mockCreatePipeline.mockResolvedValue({ data: mockPipeline });

      let returnedPipeline: any;
      await act(async () => {
        returnedPipeline = await result.current.createPipeline({ name: 'Test Pipeline' });
      });

      expect(mockCreatePipeline).toHaveBeenCalledWith({ name: 'Test Pipeline' });
      expect(returnedPipeline).toEqual(mockPipeline);
      expect(result.current.pipelines[0]).toEqual(mockPipeline);
      expect(result.current.pipelinesLoading).toBe(false);
    });

    it('sets pipelinesError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockCreatePipeline.mockRejectedValue(new Error('Create pipeline failed'));

      await act(async () => {
        await expect(
          result.current.createPipeline({ name: 'Bad Pipeline' })
        ).rejects.toThrow('Create pipeline failed');
      });

      expect(result.current.pipelinesError).toBe('Create pipeline failed');
    });
  });

  describe('updatePipeline', () => {
    it('replaces updated pipeline in list and returns it', async () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
      mockGetAllDocuments.mockResolvedValue({ data: [] });
      mockGetAllModels.mockResolvedValue({ data: [] });
      mockGetAllPipelines.mockResolvedValue({ data: [mockPipeline] });

      const updatedPipeline = { ...mockPipeline, name: 'Updated Pipeline' };
      mockUpdatePipeline.mockResolvedValue({ data: updatedPipeline });

      const { result } = renderHook(() => useDocuments(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.pipelines).toHaveLength(1);
      });

      let returnedPipeline: any;
      await act(async () => {
        returnedPipeline = await result.current.updatePipeline('pipe-1', { name: 'Updated Pipeline' });
      });

      expect(mockUpdatePipeline).toHaveBeenCalledWith('pipe-1', { name: 'Updated Pipeline' });
      expect(returnedPipeline).toEqual(updatedPipeline);
      expect(result.current.pipelines[0].name).toBe('Updated Pipeline');
    });

    it('sets pipelinesError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockUpdatePipeline.mockRejectedValue(new Error('Update pipeline failed'));

      await act(async () => {
        await expect(
          result.current.updatePipeline('pipe-1', { name: 'Bad' })
        ).rejects.toThrow('Update pipeline failed');
      });

      expect(result.current.pipelinesError).toBe('Update pipeline failed');
    });
  });

  describe('deletePipeline', () => {
    it('removes pipeline from list on success', async () => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
      mockGetAllDocuments.mockResolvedValue({ data: [] });
      mockGetAllModels.mockResolvedValue({ data: [] });
      mockGetAllPipelines.mockResolvedValue({ data: [mockPipeline, mockPipeline2] });
      mockDeletePipeline.mockResolvedValue({});

      const { result } = renderHook(() => useDocuments(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(result.current.pipelines).toHaveLength(2);
      });

      await act(async () => {
        await result.current.deletePipeline('pipe-1');
      });

      expect(mockDeletePipeline).toHaveBeenCalledWith('pipe-1');
      expect(result.current.pipelines).toHaveLength(1);
      expect(result.current.pipelines[0].id).toBe('pipe-2');
    });

    it('sets pipelinesError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockDeletePipeline.mockRejectedValue(new Error('Delete pipeline failed'));

      await act(async () => {
        await expect(
          result.current.deletePipeline('pipe-1')
        ).rejects.toThrow('Delete pipeline failed');
      });

      expect(result.current.pipelinesError).toBe('Delete pipeline failed');
    });
  });

  describe('runPipeline', () => {
    it('calls apiService.runPipeline and returns result data', async () => {
      const { result } = renderUnauthenticatedHook();

      const runResult = { status: 'completed', outputId: 'out-1' };
      mockRunPipeline.mockResolvedValue({ data: runResult });

      let returnedResult: any;
      await act(async () => {
        returnedResult = await result.current.runPipeline('pipe-1', { key: 'value' });
      });

      expect(mockRunPipeline).toHaveBeenCalledWith('pipe-1', { key: 'value' });
      expect(returnedResult).toEqual(runResult);
      expect(result.current.pipelinesLoading).toBe(false);
    });

    it('handles flat response (no data wrapper)', async () => {
      const { result } = renderUnauthenticatedHook();

      const runResult = { status: 'completed' };
      mockRunPipeline.mockResolvedValue(runResult);

      let returnedResult: any;
      await act(async () => {
        returnedResult = await result.current.runPipeline('pipe-1');
      });

      expect(returnedResult).toEqual(runResult);
    });

    it('sets pipelinesError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockRunPipeline.mockRejectedValue(new Error('Run failed'));

      await act(async () => {
        await expect(
          result.current.runPipeline('pipe-1')
        ).rejects.toThrow('Run failed');
      });

      expect(result.current.pipelinesError).toBe('Run failed');
      expect(result.current.pipelinesLoading).toBe(false);
    });
  });

  // ============================================================
  // Queries
  // ============================================================
  describe('fetchQueries', () => {
    it('sets queries from data wrapper response', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetQueries.mockResolvedValue({ data: [mockQuery] });

      await act(async () => {
        await result.current.fetchQueries('pipe-1');
      });

      expect(mockGetQueries).toHaveBeenCalledWith('pipe-1');
      expect(result.current.queries).toEqual([mockQuery]);
      expect(result.current.queriesLoading).toBe(false);
      expect(result.current.queriesError).toBeNull();
    });

    it('calls getQueries without pipelineId when omitted', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetQueries.mockResolvedValue({ data: [mockQuery] });

      await act(async () => {
        await result.current.fetchQueries();
      });

      expect(mockGetQueries).toHaveBeenCalledWith(undefined);
      expect(result.current.queries).toEqual([mockQuery]);
    });

    it('sets queriesError on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetQueries.mockRejectedValue(new Error('Queries fetch error'));

      await act(async () => {
        await result.current.fetchQueries();
      });

      expect(result.current.queriesError).toBe('Queries fetch error');
      expect(result.current.queriesLoading).toBe(false);
    });

    it('uses default error message when error has no message', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetQueries.mockRejectedValue({});

      await act(async () => {
        await result.current.fetchQueries();
      });

      expect(result.current.queriesError).toBe('Failed to fetch queries');
    });
  });

  describe('askQuestion', () => {
    it('adds query to front of queries list and returns it', async () => {
      const { result } = renderUnauthenticatedHook();

      mockAskQuestion.mockResolvedValue({ data: mockQuery });

      let returnedQuery: any;
      await act(async () => {
        returnedQuery = await result.current.askQuestion('pipe-1', 'What is this about?');
      });

      expect(mockAskQuestion).toHaveBeenCalledWith('pipe-1', 'What is this about?');
      expect(returnedQuery).toEqual(mockQuery);
      expect(result.current.queries[0]).toEqual(mockQuery);
      expect(result.current.queriesLoading).toBe(false);
      expect(result.current.queriesError).toBeNull();
    });

    it('handles flat response (no data wrapper)', async () => {
      const { result } = renderUnauthenticatedHook();

      mockAskQuestion.mockResolvedValue(mockQuery);

      let returnedQuery: any;
      await act(async () => {
        returnedQuery = await result.current.askQuestion('pipe-1', 'Question?');
      });

      expect(returnedQuery).toEqual(mockQuery);
      expect(result.current.queries[0]).toEqual(mockQuery);
    });

    it('sets queriesError and rethrows on failure', async () => {
      const { result } = renderUnauthenticatedHook();

      mockAskQuestion.mockRejectedValue(new Error('Ask failed'));

      await act(async () => {
        await expect(
          result.current.askQuestion('pipe-1', 'Question?')
        ).rejects.toThrow('Ask failed');
      });

      expect(result.current.queriesError).toBe('Ask failed');
      expect(result.current.queriesLoading).toBe(false);
    });

    it('uses default error message when error has no message', async () => {
      const { result } = renderUnauthenticatedHook();

      mockAskQuestion.mockRejectedValue({});

      await act(async () => {
        await expect(
          result.current.askQuestion('pipe-1', 'Question?')
        ).rejects.toThrow('Failed to ask question');
      });

      expect(result.current.queriesError).toBe('Failed to ask question');
    });
  });

  // ============================================================
  // Error clearing on subsequent successful calls
  // ============================================================
  describe('error clearing', () => {
    it('clears documentsError on subsequent successful fetchDocuments', async () => {
      const { result } = renderUnauthenticatedHook();

      // First call fails
      mockGetAllDocuments.mockRejectedValueOnce(new Error('Temporary error'));
      await act(async () => {
        await result.current.fetchDocuments();
      });
      expect(result.current.documentsError).toBe('Temporary error');

      // Second call succeeds
      mockGetAllDocuments.mockResolvedValueOnce({ data: [mockDocument] });
      await act(async () => {
        await result.current.fetchDocuments();
      });
      expect(result.current.documentsError).toBeNull();
      expect(result.current.documents).toEqual([mockDocument]);
    });

    it('clears modelsError on subsequent successful fetchModels', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllModels.mockRejectedValueOnce(new Error('Temporary error'));
      await act(async () => {
        await result.current.fetchModels();
      });
      expect(result.current.modelsError).toBe('Temporary error');

      mockGetAllModels.mockResolvedValueOnce({ data: [mockModel] });
      await act(async () => {
        await result.current.fetchModels();
      });
      expect(result.current.modelsError).toBeNull();
    });

    it('clears pipelinesError on subsequent successful fetchPipelines', async () => {
      const { result } = renderUnauthenticatedHook();

      mockGetAllPipelines.mockRejectedValueOnce(new Error('Temporary error'));
      await act(async () => {
        await result.current.fetchPipelines();
      });
      expect(result.current.pipelinesError).toBe('Temporary error');

      mockGetAllPipelines.mockResolvedValueOnce({ data: [mockPipeline] });
      await act(async () => {
        await result.current.fetchPipelines();
      });
      expect(result.current.pipelinesError).toBeNull();
    });
  });
});
