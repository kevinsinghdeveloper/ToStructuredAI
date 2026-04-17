import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  IconButton,
  TextField,
  Divider,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  ArrowBack as BackIcon,
  Send as SendIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Description as DocIcon,
  SmartToy as AIIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useDocuments } from '../context_providers/DocumentContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';
import {
  RAGPipeline,
  Document,
  StructuredOutput,
  Query,
  PipelineStatus,
} from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';

// ==================== Types ====================
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  confidence?: number;
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

const formatDate = (iso: string): string => {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// ==================== Main Component ====================
const PipelineDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showError, showSuccess } = useNotification();
  const { models, runPipeline, askQuestion } = useDocuments();

  // Pipeline data
  const [pipeline, setPipeline] = useState<RAGPipeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Related data
  const [documents, setDocuments] = useState<Document[]>([]);
  const [outputs, setOutputs] = useState<StructuredOutput[]>([]);
  const [outputsLoading, setOutputsLoading] = useState(false);

  // Run state
  const [running, setRunning] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ==================== Data Loading ====================

  const loadPipeline = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.getPipeline(id);
      const pipelineData = result?.data || result;
      setPipeline(pipelineData);
    } catch (err: any) {
      setError(err.message || 'Failed to load pipeline');
      showError('Failed to load pipeline details');
    } finally {
      setLoading(false);
    }
  }, [id, showError]);

  const loadOutputs = useCallback(async () => {
    if (!id) return;
    try {
      setOutputsLoading(true);
      const result = await apiService.getOutputs(id);
      const outputData = result?.data || result || [];
      setOutputs(Array.isArray(outputData) ? outputData : []);
    } catch {
      setOutputs([]);
    } finally {
      setOutputsLoading(false);
    }
  }, [id]);

  const loadDocuments = useCallback(async () => {
    if (!pipeline?.documentIds || pipeline.documentIds.length === 0) {
      setDocuments([]);
      return;
    }
    try {
      const docPromises = pipeline.documentIds.map((docId) =>
        apiService.getDocument(docId).catch(() => null)
      );
      const results = await Promise.all(docPromises);
      const validDocs = results
        .map((r) => r?.data || r)
        .filter((d): d is Document => d !== null);
      setDocuments(validDocs);
    } catch {
      setDocuments([]);
    }
  }, [pipeline?.documentIds]);

  const loadChatHistory = useCallback(() => {
    if (!id) return;
    const storageKey = `chat_history_${id}`;
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
    }
  }, [id]);

  // ==================== Effects ====================

  useEffect(() => {
    loadPipeline();
  }, [loadPipeline]);

  useEffect(() => {
    if (pipeline) {
      loadDocuments();
      loadOutputs();
      loadChatHistory();
    }
  }, [pipeline, loadDocuments, loadOutputs, loadChatHistory]);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Persist chat
  useEffect(() => {
    if (id && chatMessages.length > 0) {
      localStorage.setItem(`chat_history_${id}`, JSON.stringify(chatMessages));
    }
  }, [chatMessages, id]);

  // ==================== Handlers ====================

  const getModelName = useCallback(
    (modelId: string): string => {
      const model = models.find((m) => m.id === modelId);
      return model?.name || modelId;
    },
    [models]
  );

  const handleRunPipeline = async () => {
    if (!pipeline) return;
    try {
      setRunning(true);
      await runPipeline(pipeline.id);
      showSuccess('Pipeline run started successfully');
      await loadPipeline();
      await loadOutputs();
    } catch (err: any) {
      showError('Failed to run pipeline: ' + err.message);
    } finally {
      setRunning(false);
    }
  };

  const handleSendMessage = async () => {
    if (!currentInput.trim() || !pipeline) return;

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
      const result = await askQuestion(pipeline.id, userMessage.content);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.answer || 'No response received.',
        timestamp: new Date(),
        sources: result.sources,
        confidence: result.confidence,
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

  const handleClearChat = () => {
    setChatMessages([]);
    if (id) {
      localStorage.removeItem(`chat_history_${id}`);
    }
  };

  const handleDownloadOutput = async (output: StructuredOutput) => {
    if (!pipeline) return;
    try {
      const blob = await apiService.downloadOutput(output.id, pipeline.id);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `output-${output.id}.${output.format?.toLowerCase() || 'json'}`
      );
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      showError('Failed to download output: ' + err.message);
    }
  };

  const handleDeleteOutput = async (output: StructuredOutput) => {
    if (!pipeline) return;
    if (!window.confirm('Are you sure you want to delete this output?')) return;
    try {
      await apiService.deleteOutput(output.id, pipeline.id);
      setOutputs((prev) => prev.filter((o) => o.id !== output.id));
      showSuccess('Output deleted successfully');
    } catch (err: any) {
      showError('Failed to delete output: ' + err.message);
    }
  };

  // ==================== Render ====================

  if (loading) {
    return <LoadingSpinner message="Loading pipeline details..." />;
  }

  if (error || !pipeline) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Pipeline not found'}
        </Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/pipelines')}>
          Back to Pipelines
        </Button>
      </Container>
    );
  }

  const isProcessing = pipeline.status === PipelineStatus.PROCESSING;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <IconButton onClick={() => navigate('/pipelines')} size="small">
          <BackIcon />
        </IconButton>
        <Typography variant="h4" fontWeight={700}>
          {pipeline.name}
        </Typography>
        <Chip
          label={pipeline.status || 'pending'}
          color={getStatusColor(pipeline.status || 'pending')}
          size="small"
          sx={{ ml: 1 }}
        />
      </Box>
      {pipeline.description && (
        <Typography variant="body1" color="text.secondary" sx={{ ml: 6, mb: 3 }}>
          {pipeline.description}
        </Typography>
      )}

      {/* Pipeline Info Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, rgba(123, 109, 246, 0.15), rgba(123, 109, 246, 0.05))' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Pipeline Type
              </Typography>
              <Typography variant="h6" fontWeight={600}>
                {pipeline.pipelineType || 'Default'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05))' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Chat Model
              </Typography>
              <Typography variant="body1" fontWeight={600} noWrap>
                {getModelName(pipeline.modelId)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05))' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Embedding Model
              </Typography>
              <Typography variant="body1" fontWeight={600} noWrap>
                {getModelName(pipeline.embeddingModelId)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05))' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Documents
              </Typography>
              <Typography variant="h6" fontWeight={600}>
                {pipeline.documentIds?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Run Pipeline + Dates */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Created</Typography>
                <Typography variant="body2">{formatDate(pipeline.createdAt)}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Updated</Typography>
                <Typography variant="body2">{formatDate(pipeline.updatedAt)}</Typography>
              </Box>
            </Box>
            <Button
              variant="contained"
              startIcon={running || isProcessing ? <CircularProgress size={20} color="inherit" /> : <RunIcon />}
              onClick={handleRunPipeline}
              disabled={running || isProcessing}
              color="secondary"
            >
              {running ? 'Starting...' : isProcessing ? 'Processing...' : 'Run Pipeline'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Linked Documents */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Linked Documents
          </Typography>
          {documents.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No documents linked to this pipeline.
            </Typography>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>File Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Uploaded</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {documents.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <DocIcon fontSize="small" color="action" />
                          <Typography variant="body2">
                            {doc.originalFileName || doc.fileName}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={doc.fileType} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{formatFileSize(doc.fileSize)}</TableCell>
                      <TableCell>
                        <Chip
                          label={doc.status}
                          size="small"
                          color={getStatusColor(doc.status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(doc.uploadedAt || doc.createdAt)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Pipeline Outputs */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Pipeline Outputs
            </Typography>
            {outputsLoading && <CircularProgress size={20} />}
          </Box>
          {outputs.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No outputs generated yet. Run the pipeline to generate outputs.
            </Typography>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Output ID</TableCell>
                    <TableCell>Format</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {outputs.map((output) => (
                    <TableRow key={output.id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem">
                          {output.id.substring(0, 12)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={output.format}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(output.createdAt)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Download">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleDownloadOutput(output)}
                          >
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteOutput(output)}
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

      {/* Q&A Chat Section (embedded, not dialog) */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Ask Questions
            </Typography>
            <Button
              size="small"
              onClick={handleClearChat}
              disabled={chatMessages.length === 0}
            >
              Clear History
            </Button>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {/* Chat Messages */}
          <Box
            sx={{
              height: 420,
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
                <AIIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.disabled">
                  Ask questions about the documents in this pipeline.
                </Typography>
                <Typography variant="caption" color="text.disabled">
                  Press Enter to send, Shift+Enter for new line
                </Typography>
              </Box>
            ) : (
              chatMessages.map((msg) => {
                const isUser = msg.role === 'user';
                return (
                  <Box
                    key={msg.id}
                    sx={{
                      alignSelf: isUser ? 'flex-end' : 'flex-start',
                      maxWidth: '80%',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      {!isUser && <AIIcon sx={{ fontSize: 16, color: 'text.secondary' }} />}
                      {isUser && <PersonIcon sx={{ fontSize: 16, color: 'text.secondary' }} />}
                      <Typography variant="caption" color="text.secondary">
                        {isUser ? 'You' : 'Assistant'}
                      </Typography>
                    </Box>
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        bgcolor: isUser ? 'primary.main' : 'background.paper',
                        color: isUser ? 'primary.contrastText' : 'text.primary',
                        borderRadius: 2,
                        border: isUser ? 'none' : '1px solid',
                        borderColor: isUser ? 'transparent' : 'divider',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {msg.content}
                      </Typography>
                      {msg.sources && msg.sources.length > 0 && (
                        <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                          <Typography variant="caption" color="text.secondary">
                            Sources: {msg.sources.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {msg.confidence !== undefined && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          Confidence: {(msg.confidence * 100).toFixed(0)}%
                        </Typography>
                      )}
                    </Paper>
                    <Typography variant="caption" color="text.disabled" sx={{ mt: 0.25, px: 0.5 }}>
                      {msg.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Box>
                );
              })
            )}
            {isTyping && (
              <Box sx={{ alignSelf: 'flex-start', maxWidth: '80%' }}>
                <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
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

          {/* Chat Input */}
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Ask a question about your documents..."
              fullWidth
              multiline
              maxRows={4}
              size="small"
              disabled={isTyping || (pipeline.documentIds?.length || 0) === 0}
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
          {(pipeline.documentIds?.length || 0) === 0 && (
            <Typography variant="caption" color="warning.main" sx={{ mt: 1 }}>
              Add documents to this pipeline to enable Q&A.
            </Typography>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default PipelineDetailPage;
