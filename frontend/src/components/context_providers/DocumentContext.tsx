import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '../../utils/api.service';
import { Document, ModelConfig, RAGPipeline, Query, DatabaseConnection, Source } from '../../types';
import { useAuth } from './AuthContext';

interface DocumentContextType {
  // Documents
  documents: Document[];
  documentsLoading: boolean;
  documentsError: string | null;
  uploadDocument: (file: File, embeddingModelId: string, overwrite?: boolean) => Promise<Document>;
  fetchDocuments: () => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;

  // Models
  models: ModelConfig[];
  modelsLoading: boolean;
  modelsError: string | null;
  fetchModels: () => Promise<void>;
  createModel: (model: Partial<ModelConfig>) => Promise<ModelConfig>;
  updateModel: (id: string, model: Partial<ModelConfig>) => Promise<ModelConfig>;
  deleteModel: (id: string) => Promise<void>;

  // Pipelines
  pipelines: RAGPipeline[];
  pipelinesLoading: boolean;
  pipelinesError: string | null;
  fetchPipelines: () => Promise<void>;
  createPipeline: (pipeline: Partial<RAGPipeline>) => Promise<RAGPipeline>;
  updatePipeline: (id: string, pipeline: Partial<RAGPipeline>) => Promise<RAGPipeline>;
  deletePipeline: (id: string) => Promise<void>;
  runPipeline: (id: string, data?: any) => Promise<any>;

  // Queries (Q&A)
  queries: Query[];
  queriesLoading: boolean;
  queriesError: string | null;
  askQuestion: (pipelineId: string, question: string) => Promise<Query>;
  fetchQueries: (pipelineId?: string) => Promise<void>;

  // Database Connections
  connections: DatabaseConnection[];
  connectionsLoading: boolean;
  fetchConnections: () => Promise<void>;

  // Sources
  sources: Source[];
  sourcesLoading: boolean;
  fetchSources: () => Promise<void>;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export const useDocuments = () => {
  const context = useContext(DocumentContext);
  if (!context) {
    throw new Error('useDocuments must be used within a DocumentContextProvider');
  }
  return context;
};

interface DocumentContextProviderProps {
  children: ReactNode;
}

export const DocumentContextProvider: React.FC<DocumentContextProviderProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  // Documents state
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  // Models state
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);

  // Pipelines state
  const [pipelines, setPipelines] = useState<RAGPipeline[]>([]);
  const [pipelinesLoading, setPipelinesLoading] = useState(false);
  const [pipelinesError, setPipelinesError] = useState<string | null>(null);

  // Queries state
  const [queries, setQueries] = useState<Query[]>([]);
  const [queriesLoading, setQueriesLoading] = useState(false);
  const [queriesError, setQueriesError] = useState<string | null>(null);

  // Connections state
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [connectionsLoading, setConnectionsLoading] = useState(false);

  // Sources state
  const [sources, setSources] = useState<Source[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchDocuments();
      fetchModels();
      fetchPipelines();
      fetchConnections();
      fetchSources();
    }
  }, [isAuthenticated]);

  // Document methods
  const fetchDocuments = async () => {
    try {
      setDocumentsLoading(true);
      setDocumentsError(null);
      const result = await apiService.getAllDocuments();
      setDocuments(result.data || result);
    } catch (err: any) {
      setDocumentsError(err.message || 'Failed to fetch documents');
    } finally {
      setDocumentsLoading(false);
    }
  };

  const uploadDocument = async (file: File, embeddingModelId: string, overwrite: boolean = false): Promise<Document> => {
    try {
      setDocumentsLoading(true);
      setDocumentsError(null);
      const result = await apiService.uploadDocument(file, embeddingModelId, overwrite);
      const doc = result.data || result;
      setDocuments((prev) => [doc, ...prev]);
      return doc;
    } catch (err: any) {
      setDocumentsError(err.message || 'Failed to upload document');
      throw err;
    } finally {
      setDocumentsLoading(false);
    }
  };

  const deleteDocument = async (id: string) => {
    try {
      setDocumentsLoading(true);
      setDocumentsError(null);
      await apiService.deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete document';
      setDocumentsError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setDocumentsLoading(false);
    }
  };

  // Model methods
  const fetchModels = async () => {
    try {
      setModelsLoading(true);
      setModelsError(null);
      const result = await apiService.getAllModels();
      setModels(result.data || result);
    } catch (err: any) {
      setModelsError(err.message || 'Failed to fetch models');
    } finally {
      setModelsLoading(false);
    }
  };

  const createModel = async (model: Partial<ModelConfig>): Promise<ModelConfig> => {
    try {
      setModelsLoading(true);
      setModelsError(null);
      const result = await apiService.createModel(model);
      const newModel = result.data || result;
      setModels((prev) => [newModel, ...prev]);
      return newModel;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to create model';
      setModelsError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setModelsLoading(false);
    }
  };

  const updateModel = async (id: string, model: Partial<ModelConfig>): Promise<ModelConfig> => {
    try {
      setModelsLoading(true);
      setModelsError(null);
      const result = await apiService.updateModel(id, model);
      const updatedModel = result.data || result;
      setModels((prev) => prev.map((m) => (m.id === id ? updatedModel : m)));
      return updatedModel;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to update model';
      setModelsError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setModelsLoading(false);
    }
  };

  const deleteModel = async (id: string) => {
    try {
      setModelsLoading(true);
      setModelsError(null);
      await apiService.deleteModel(id);
      setModels((prev) => prev.filter((m) => m.id !== id));
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete model';
      setModelsError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setModelsLoading(false);
    }
  };

  // Pipeline methods
  const fetchPipelines = async () => {
    try {
      setPipelinesLoading(true);
      setPipelinesError(null);
      const result = await apiService.getAllPipelines();
      setPipelines(result.data || result);
    } catch (err: any) {
      setPipelinesError(err.message || 'Failed to fetch pipelines');
    } finally {
      setPipelinesLoading(false);
    }
  };

  const createPipeline = async (pipeline: Partial<RAGPipeline>): Promise<RAGPipeline> => {
    try {
      setPipelinesLoading(true);
      setPipelinesError(null);
      const result = await apiService.createPipeline(pipeline);
      const newPipeline = result.data || result;
      setPipelines((prev) => [newPipeline, ...prev]);
      return newPipeline;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to create pipeline';
      setPipelinesError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setPipelinesLoading(false);
    }
  };

  const updatePipeline = async (id: string, pipeline: Partial<RAGPipeline>): Promise<RAGPipeline> => {
    try {
      setPipelinesLoading(true);
      setPipelinesError(null);
      const result = await apiService.updatePipeline(id, pipeline);
      const updatedPipeline = result.data || result;
      setPipelines((prev) => prev.map((p) => (p.id === id ? updatedPipeline : p)));
      return updatedPipeline;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to update pipeline';
      setPipelinesError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setPipelinesLoading(false);
    }
  };

  const deletePipeline = async (id: string) => {
    try {
      setPipelinesLoading(true);
      setPipelinesError(null);
      await apiService.deletePipeline(id);
      setPipelines((prev) => prev.filter((p) => p.id !== id));
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete pipeline';
      setPipelinesError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setPipelinesLoading(false);
    }
  };

  const runPipeline = async (id: string, data?: any) => {
    try {
      setPipelinesLoading(true);
      setPipelinesError(null);
      const result = await apiService.runPipeline(id, data);
      return result.data || result;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to run pipeline';
      setPipelinesError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setPipelinesLoading(false);
    }
  };

  // Query methods
  const fetchQueries = async (pipelineId?: string) => {
    try {
      setQueriesLoading(true);
      setQueriesError(null);
      const result = await apiService.getQueries(pipelineId);
      setQueries(result.data || result);
    } catch (err: any) {
      setQueriesError(err.message || 'Failed to fetch queries');
    } finally {
      setQueriesLoading(false);
    }
  };

  const askQuestion = async (pipelineId: string, question: string): Promise<Query> => {
    try {
      setQueriesLoading(true);
      setQueriesError(null);
      const result = await apiService.askQuestion(pipelineId, question);
      const query = result.data || result;
      setQueries((prev) => [query, ...prev]);
      return query;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to ask question';
      setQueriesError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setQueriesLoading(false);
    }
  };

  // Connection methods
  const fetchConnections = async () => {
    try {
      setConnectionsLoading(true);
      const result = await apiService.getConnections();
      setConnections(result.data || result);
    } catch {
      // Silent fail — connections are optional
    } finally {
      setConnectionsLoading(false);
    }
  };

  // Source methods
  const fetchSources = async () => {
    try {
      setSourcesLoading(true);
      const result = await apiService.getSources();
      setSources(result.data || result);
    } catch {
      // Silent fail — sources are optional
    } finally {
      setSourcesLoading(false);
    }
  };

  const value: DocumentContextType = {
    documents,
    documentsLoading,
    documentsError,
    uploadDocument,
    fetchDocuments,
    deleteDocument,
    models,
    modelsLoading,
    modelsError,
    fetchModels,
    createModel,
    updateModel,
    deleteModel,
    pipelines,
    pipelinesLoading,
    pipelinesError,
    fetchPipelines,
    createPipeline,
    updatePipeline,
    deletePipeline,
    runPipeline,
    queries,
    queriesLoading,
    queriesError,
    askQuestion,
    fetchQueries,
    connections,
    connectionsLoading,
    fetchConnections,
    sources,
    sourcesLoading,
    fetchSources,
  };

  return <DocumentContext.Provider value={value}>{children}</DocumentContext.Provider>;
};

export default DocumentContext;
