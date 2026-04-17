import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  ListItemText,
  OutlinedInput,
  CircularProgress,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Add as AddIcon,
  Chat as ChatIcon,
  Edit as EditIcon,
  Send as SendIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useDocuments } from '../context_providers/DocumentContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';
import {
  Document,
  ModelConfig,
  RAGPipeline,
  PipelineType,
  ModelType,
} from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';
import DynamicFieldRenderer from '../shared/DynamicFieldRenderer';

// ==================== Types ====================
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// ==================== Helpers ====================
const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'ready':
      return 'success';
    case 'processing':
    case 'pending':
      return 'warning';
    case 'failed':
    case 'error':
    case 'cancelled':
      return 'error';
    default:
      return 'default';
  }
};

// ==================== Main Component ====================
const PipelinesPage: React.FC = () => {
  const navigate = useNavigate();
  const { showError, showSuccess, showWarning } = useNotification();
  const {
    pipelines,
    pipelinesLoading,
    pipelinesError,
    createPipeline,
    updatePipeline,
    deletePipeline,
    models,
    askQuestion,
  } = useDocuments();

  // Local state
  const [pipelineTypes, setPipelineTypes] = useState<PipelineType[]>([]);
  const [pipelineTypesLoading, setPipelineTypesLoading] = useState(false);

  // Create Dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newPipeline, setNewPipeline] = useState({
    name: '',
    description: '',
    pipelineType: '',
    embeddingModelId: '',
    modelId: '',
    documentIds: [] as string[],
  });
  const [selectedPipelineTypeDetails, setSelectedPipelineTypeDetails] = useState<PipelineType | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, any>>({});
  const [creating, setCreating] = useState(false);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);

  // Edit Dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPipeline, setEditingPipeline] = useState<RAGPipeline | null>(null);
  const [editPipelineData, setEditPipelineData] = useState({
    name: '',
    description: '',
    pipelineType: '',
    embeddingModelId: '',
    modelId: '',
    documentIds: [] as string[],
  });
  const [editFieldValues, setEditFieldValues] = useState<Record<string, any>>({});
  const [editPipelineTypeDetails, setEditPipelineTypeDetails] = useState<PipelineType | null>(null);
  const [updating, setUpdating] = useState(false);
  const [editFilteredDocuments, setEditFilteredDocuments] = useState<Document[]>([]);

  // Q&A Chat Dialog state
  const [qaDialogOpen, setQaDialogOpen] = useState(false);
  const [selectedPipeline, setSelectedPipeline] = useState<RAGPipeline | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const MAX_HISTORY = 10;
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Derived model lists
  const embeddingModels = models.filter((m) => m.modelType === ModelType.EMBEDDING);
  const chatModels = models.filter((m) => m.modelType === ModelType.CHAT);

  // ==================== Effects ====================

  // Load pipeline types on mount
  useEffect(() => {
    const loadPipelineTypes = async () => {
      setPipelineTypesLoading(true);
      try {
        const result = await apiService.getAllPipelineTypes();
        const types = result?.data || result || [];
        setPipelineTypes(Array.isArray(types) ? types : []);
      } catch (err: any) {
        showError('Failed to load pipeline types');
      } finally {
        setPipelineTypesLoading(false);
      }
    };
    loadPipelineTypes();
  }, [showError]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Persist chat messages to localStorage
  useEffect(() => {
    if (selectedPipeline && chatMessages.length > 0) {
      const storageKey = `chat_history_${selectedPipeline.id}`;
      localStorage.setItem(storageKey, JSON.stringify(chatMessages));
    }
  }, [chatMessages, selectedPipeline]);

  // Load pipeline type details when create dialog pipeline type changes
  useEffect(() => {
    if (!newPipeline.pipelineType) {
      setSelectedPipelineTypeDetails(null);
      return;
    }
    const loadDetails = async () => {
      try {
        const result = await apiService.getPipelineType(newPipeline.pipelineType);
        setSelectedPipelineTypeDetails(result?.data || result);
        setFieldValues({});
      } catch {
        setSelectedPipelineTypeDetails(null);
      }
    };
    loadDetails();
  }, [newPipeline.pipelineType]);

  // Fetch filtered documents for create dialog when embedding model changes
  useEffect(() => {
    if (!newPipeline.embeddingModelId) {
      setFilteredDocuments([]);
      return;
    }
    const fetchFiltered = async () => {
      try {
        const result = await apiService.getDocumentsByEmbeddingModel(newPipeline.embeddingModelId);
        const docs = result?.data || result || [];
        setFilteredDocuments(Array.isArray(docs) ? docs : []);
      } catch {
        setFilteredDocuments([]);
      }
    };
    fetchFiltered();
  }, [newPipeline.embeddingModelId]);

  // Load pipeline type details when edit dialog pipeline type changes
  useEffect(() => {
    if (!editPipelineData.pipelineType) {
      setEditPipelineTypeDetails(null);
      return;
    }
    const loadDetails = async () => {
      try {
        const result = await apiService.getPipelineType(editPipelineData.pipelineType);
        setEditPipelineTypeDetails(result?.data || result);
      } catch {
        setEditPipelineTypeDetails(null);
      }
    };
    loadDetails();
  }, [editPipelineData.pipelineType]);

  // Fetch filtered documents for edit dialog when embedding model changes
  useEffect(() => {
    if (!editPipelineData.embeddingModelId) {
      setEditFilteredDocuments([]);
      return;
    }
    const fetchFiltered = async () => {
      try {
        const result = await apiService.getDocumentsByEmbeddingModel(editPipelineData.embeddingModelId);
        const docs = result?.data || result || [];
        setEditFilteredDocuments(Array.isArray(docs) ? docs : []);
      } catch {
        setEditFilteredDocuments([]);
      }
    };
    fetchFiltered();
  }, [editPipelineData.embeddingModelId]);

  // ==================== Helpers ====================

  const getModelName = useCallback(
    (modelId: string): string => {
      const model = models.find((m) => m.id === modelId);
      return model?.name || 'Unknown Model';
    },
    [models]
  );

  const loadChatHistory = (pipelineId: string) => {
    const storageKey = `chat_history_${pipelineId}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setChatMessages(
          parsed.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          }))
        );
      } catch {
        setChatMessages([]);
      }
    } else {
      setChatMessages([]);
    }
  };

  // ==================== Handlers ====================

  const handleCreatePipeline = async () => {
    if (
      !newPipeline.name ||
      !newPipeline.embeddingModelId ||
      !newPipeline.modelId ||
      newPipeline.documentIds.length === 0
    ) {
      showWarning('Please fill in all required fields and select at least one document');
      return;
    }

    try {
      setCreating(true);
      await createPipeline({
        name: newPipeline.name,
        description: newPipeline.description,
        pipelineType: newPipeline.pipelineType || undefined,
        embeddingModelId: newPipeline.embeddingModelId,
        modelId: newPipeline.modelId,
        documentIds: newPipeline.documentIds,
        config: Object.keys(fieldValues).length > 0 ? fieldValues : undefined,
      });
      showSuccess('Pipeline created successfully');
      setCreateDialogOpen(false);
      resetCreateForm();
    } catch (err: any) {
      showError('Failed to create pipeline: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  const resetCreateForm = () => {
    setNewPipeline({
      name: '',
      description: '',
      pipelineType: '',
      embeddingModelId: '',
      modelId: '',
      documentIds: [],
    });
    setFieldValues({});
    setSelectedPipelineTypeDetails(null);
    setFilteredDocuments([]);
  };

  const handleOpenEditDialog = (pipeline: RAGPipeline) => {
    setEditingPipeline(pipeline);
    setEditPipelineData({
      name: pipeline.name,
      description: pipeline.description || '',
      pipelineType: pipeline.pipelineType || '',
      embeddingModelId: pipeline.embeddingModelId,
      modelId: pipeline.modelId,
      documentIds: pipeline.documentIds || [],
    });
    setEditFieldValues(pipeline.config || {});
    setEditDialogOpen(true);
  };

  const handleUpdatePipeline = async () => {
    if (
      !editingPipeline ||
      !editPipelineData.name ||
      !editPipelineData.embeddingModelId ||
      !editPipelineData.modelId ||
      editPipelineData.documentIds.length === 0
    ) {
      showWarning('Please fill in all required fields and select at least one document');
      return;
    }

    try {
      setUpdating(true);
      await updatePipeline(editingPipeline.id, {
        name: editPipelineData.name,
        description: editPipelineData.description,
        embeddingModelId: editPipelineData.embeddingModelId,
        modelId: editPipelineData.modelId,
        documentIds: editPipelineData.documentIds,
        config: Object.keys(editFieldValues).length > 0 ? editFieldValues : undefined,
      });
      showSuccess('Pipeline updated successfully');
      handleCloseEditDialog();
    } catch (err: any) {
      showError('Failed to update pipeline: ' + err.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setEditingPipeline(null);
    setEditPipelineData({
      name: '',
      description: '',
      pipelineType: '',
      embeddingModelId: '',
      modelId: '',
      documentIds: [],
    });
    setEditFieldValues({});
    setEditPipelineTypeDetails(null);
    setEditFilteredDocuments([]);
  };

  const handleDeletePipeline = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this pipeline?')) return;
    try {
      await deletePipeline(id);
      showSuccess('Pipeline deleted successfully');
    } catch (err: any) {
      showError('Failed to delete pipeline: ' + err.message);
    }
  };

  const handleOpenChat = (pipeline: RAGPipeline) => {
    setSelectedPipeline(pipeline);
    loadChatHistory(pipeline.id);
    setCurrentInput('');
    setQaDialogOpen(true);
  };

  const handleSendMessage = async () => {
    if (!currentInput.trim() || !selectedPipeline) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: currentInput.trim(),
      timestamp: new Date(),
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setCurrentInput('');
    setIsTyping(true);

    try {
      const result = await askQuestion(selectedPipeline.id, userMessage.content);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.answer || 'No response received.',
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      showError('Failed to get answer: ' + err.message);
    } finally {
      setIsTyping(false);
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChatHistory = () => {
    setChatMessages([]);
    if (selectedPipeline) {
      localStorage.removeItem(`chat_history_${selectedPipeline.id}`);
    }
  };

  // ==================== Render ====================

  if (pipelinesLoading && pipelines.length === 0) {
    return <LoadingSpinner message="Loading pipelines..." />;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Pipelines
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            Create and manage your RAG pipelines for document Q&A and structured extraction
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          disabled={models.length === 0}
        >
          Create Pipeline
        </Button>
      </Box>

      {/* Error Alert */}
      {pipelinesError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {pipelinesError}
        </Alert>
      )}

      {/* Pipelines Table */}
      <Card>
        <CardContent>
          {pipelines.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No pipelines yet
              </Typography>
              <Typography variant="body2" color="text.disabled" sx={{ mb: 2 }}>
                Create your first pipeline to start using RAG queries on your documents.
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
                disabled={models.length === 0}
              >
                Create Pipeline
              </Button>
            </Box>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Pipeline Name</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Chat Model</TableCell>
                    <TableCell>Embedding Model</TableCell>
                    <TableCell>Documents</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pipelines.map((pipeline) => (
                    <TableRow
                      key={pipeline.id}
                      hover
                      sx={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/pipelines/${pipeline.id}`)}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {pipeline.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 200 }}>
                          {pipeline.description || 'No description'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getModelName(pipeline.modelId)}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getModelName(pipeline.embeddingModelId)}
                          size="small"
                          variant="outlined"
                          color="secondary"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${pipeline.documentIds?.length || 0} docs`}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={pipeline.status || 'pending'}
                          color={getStatusColor(pipeline.status || 'pending')}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                        <Tooltip title="Ask Questions">
                          <span>
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleOpenChat(pipeline)}
                              disabled={!pipeline.documentIds || pipeline.documentIds.length === 0}
                            >
                              <ChatIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            color="info"
                            onClick={() => navigate(`/pipelines/${pipeline.id}`)}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Pipeline">
                          <IconButton
                            size="small"
                            color="secondary"
                            onClick={() => handleOpenEditDialog(pipeline)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Pipeline">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeletePipeline(pipeline.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* ==================== Create Pipeline Dialog ==================== */}
      <Dialog
        open={createDialogOpen}
        onClose={() => {
          setCreateDialogOpen(false);
          resetCreateForm();
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Pipeline</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Pipeline Name"
              value={newPipeline.name}
              onChange={(e) => setNewPipeline({ ...newPipeline, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Description"
              value={newPipeline.description}
              onChange={(e) => setNewPipeline({ ...newPipeline, description: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />

            {/* Pipeline Type Selector */}
            <FormControl fullWidth>
              <InputLabel>Pipeline Type</InputLabel>
              <Select
                value={newPipeline.pipelineType}
                onChange={(e) =>
                  setNewPipeline({ ...newPipeline, pipelineType: e.target.value })
                }
                label="Pipeline Type"
                disabled={pipelineTypesLoading}
              >
                {pipelineTypes.map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    <Box>
                      <Typography variant="body2">{type.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Dynamic Fields */}
            {selectedPipelineTypeDetails?.default_fields &&
              selectedPipelineTypeDetails.default_fields.length > 0 && (
                <DynamicFieldRenderer
                  fields={selectedPipelineTypeDetails.default_fields}
                  fieldValues={fieldValues}
                  onChange={(fieldId, value) =>
                    setFieldValues((prev) => ({ ...prev, [fieldId]: value }))
                  }
                />
              )}

            {/* Embedding Model */}
            <FormControl fullWidth required>
              <InputLabel>Embedding Model</InputLabel>
              <Select
                value={newPipeline.embeddingModelId}
                onChange={(e) =>
                  setNewPipeline({
                    ...newPipeline,
                    embeddingModelId: e.target.value,
                    documentIds: [],
                  })
                }
                label="Embedding Model"
              >
                {embeddingModels.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" sx={{ mt: -1 }}>
              Select the embedding model first. Only documents using this model will be available.
            </Typography>

            {/* Chat Model */}
            <FormControl fullWidth required>
              <InputLabel>Chat Model</InputLabel>
              <Select
                value={newPipeline.modelId}
                onChange={(e) => setNewPipeline({ ...newPipeline, modelId: e.target.value })}
                label="Chat Model"
              >
                {chatModels.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Documents Multi-Select */}
            <FormControl fullWidth required disabled={!newPipeline.embeddingModelId}>
              <InputLabel>Documents</InputLabel>
              <Select
                multiple
                value={newPipeline.documentIds}
                onChange={(e) =>
                  setNewPipeline({ ...newPipeline, documentIds: e.target.value as string[] })
                }
                input={<OutlinedInput label="Documents" />}
                renderValue={(selected) => `${selected.length} selected`}
              >
                {filteredDocuments.map((doc) => (
                  <MenuItem key={doc.id} value={doc.id}>
                    <Checkbox checked={newPipeline.documentIds.includes(doc.id)} />
                    <ListItemText primary={doc.originalFileName || doc.fileName} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {newPipeline.embeddingModelId && filteredDocuments.length === 0 && (
              <Typography variant="caption" color="warning.main">
                No documents found with the selected embedding model. Please upload documents first.
              </Typography>
            )}
            {newPipeline.embeddingModelId && filteredDocuments.length > 0 && (
              <Typography variant="caption" color="text.secondary">
                {filteredDocuments.length} document(s) available with this embedding model
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setCreateDialogOpen(false);
              resetCreateForm();
            }}
          >
            Cancel
          </Button>
          <Button onClick={handleCreatePipeline} variant="contained" disabled={creating}>
            {creating ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ==================== Edit Pipeline Dialog ==================== */}
      <Dialog open={editDialogOpen} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Pipeline</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Pipeline Name"
              value={editPipelineData.name}
              onChange={(e) =>
                setEditPipelineData({ ...editPipelineData, name: e.target.value })
              }
              fullWidth
              required
            />
            <TextField
              label="Description"
              value={editPipelineData.description}
              onChange={(e) =>
                setEditPipelineData({ ...editPipelineData, description: e.target.value })
              }
              fullWidth
              multiline
              rows={2}
            />

            {/* Pipeline Type (disabled) */}
            <FormControl fullWidth disabled>
              <InputLabel>Pipeline Type</InputLabel>
              <Select
                value={editPipelineData.pipelineType}
                label="Pipeline Type"
              >
                {pipelineTypes.map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    <Box>
                      <Typography variant="body2">{type.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" sx={{ mt: -1 }}>
              Pipeline type cannot be changed after creation.
            </Typography>

            {/* Dynamic Fields */}
            {editPipelineTypeDetails?.default_fields &&
              editPipelineTypeDetails.default_fields.length > 0 && (
                <DynamicFieldRenderer
                  fields={editPipelineTypeDetails.default_fields}
                  fieldValues={editFieldValues}
                  onChange={(fieldId, value) =>
                    setEditFieldValues((prev) => ({ ...prev, [fieldId]: value }))
                  }
                />
              )}

            {/* Embedding Model */}
            <FormControl fullWidth required>
              <InputLabel>Embedding Model</InputLabel>
              <Select
                value={editPipelineData.embeddingModelId}
                onChange={(e) =>
                  setEditPipelineData({
                    ...editPipelineData,
                    embeddingModelId: e.target.value,
                    documentIds: [],
                  })
                }
                label="Embedding Model"
              >
                {embeddingModels.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" sx={{ mt: -1 }}>
              Changing the embedding model will clear document selection.
            </Typography>

            {/* Chat Model */}
            <FormControl fullWidth required>
              <InputLabel>Chat Model</InputLabel>
              <Select
                value={editPipelineData.modelId}
                onChange={(e) =>
                  setEditPipelineData({ ...editPipelineData, modelId: e.target.value })
                }
                label="Chat Model"
              >
                {chatModels.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Documents Multi-Select */}
            <FormControl fullWidth required disabled={!editPipelineData.embeddingModelId}>
              <InputLabel>Documents</InputLabel>
              <Select
                multiple
                value={editPipelineData.documentIds}
                onChange={(e) =>
                  setEditPipelineData({
                    ...editPipelineData,
                    documentIds: e.target.value as string[],
                  })
                }
                input={<OutlinedInput label="Documents" />}
                renderValue={(selected) => `${selected.length} selected`}
              >
                {editFilteredDocuments.map((doc) => (
                  <MenuItem key={doc.id} value={doc.id}>
                    <Checkbox checked={editPipelineData.documentIds.includes(doc.id)} />
                    <ListItemText primary={doc.originalFileName || doc.fileName} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {editPipelineData.embeddingModelId && editFilteredDocuments.length === 0 && (
              <Typography variant="caption" color="warning.main">
                No documents found with the selected embedding model.
              </Typography>
            )}
            {editPipelineData.embeddingModelId && editFilteredDocuments.length > 0 && (
              <Typography variant="caption" color="text.secondary">
                {editFilteredDocuments.length} document(s) available with this embedding model
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>Cancel</Button>
          <Button onClick={handleUpdatePipeline} variant="contained" disabled={updating}>
            {updating ? <CircularProgress size={24} /> : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ==================== Q&A Chat Dialog ==================== */}
      <Dialog
        open={qaDialogOpen}
        onClose={() => setQaDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Chat - {selectedPipeline?.name}</Typography>
            <Button
              size="small"
              onClick={handleClearChatHistory}
              disabled={chatMessages.length === 0}
            >
              Clear History
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* Chat Messages Area */}
          <Box
            sx={{
              height: 400,
              overflowY: 'auto',
              mb: 2,
              p: 2,
              bgcolor: '#1a1a2e',
              borderRadius: 2,
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
            }}
          >
            {chatMessages.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Typography color="text.disabled">
                  Start a conversation by asking a question about your documents...
                </Typography>
              </Box>
            ) : (
              chatMessages.map((msg) => (
                <Box
                  key={msg.id}
                  sx={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '75%',
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      bgcolor: msg.role === 'user' ? 'primary.main' : 'background.paper',
                      color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                      borderRadius: 2,
                    }}
                  >
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{ display: 'block', mt: 1, opacity: 0.6 }}
                    >
                      {msg.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Paper>
                </Box>
              ))
            )}
            {isTyping && (
              <Box sx={{ alignSelf: 'flex-start', maxWidth: '75%' }}>
                <Paper elevation={1} sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" color="text.secondary">
                      AI is typing...
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

          {/* Input Area */}
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Type your message..."
              fullWidth
              multiline
              maxRows={4}
              size="small"
              disabled={isTyping}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!currentInput.trim() || isTyping}
              sx={{
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                '&:hover': { bgcolor: 'primary.dark' },
                '&.Mui-disabled': { bgcolor: 'action.disabledBackground' },
                width: 40,
                height: 40,
              }}
            >
              <SendIcon fontSize="small" />
            </IconButton>
          </Box>
        </DialogContent>
        <DialogActions>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 'auto' }}>
            {chatMessages.length > 0 &&
              `${chatMessages.length} message${chatMessages.length !== 1 ? 's' : ''}`}
            {chatMessages.length > MAX_HISTORY &&
              ` (keeping last ${MAX_HISTORY} for context)`}
          </Typography>
          <Button onClick={() => setQaDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default PipelinesPage;
