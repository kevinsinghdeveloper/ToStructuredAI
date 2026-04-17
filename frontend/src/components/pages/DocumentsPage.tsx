import React, { useState, useEffect, useCallback } from 'react';
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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  UploadFile as UploadFileIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { useDocuments } from '../context_providers/DocumentContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';
import { ModelConfig, ModelType } from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';

// ==================== Helpers ====================
const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (status?.toUpperCase()) {
    case 'READY':
    case 'COMPLETED':
      return 'success';
    case 'UPLOADED':
    case 'EXTRACTING':
    case 'EMBEDDING':
    case 'PROCESSING':
    case 'INDEXED':
      return 'warning';
    case 'ERROR':
    case 'FAILED':
      return 'error';
    default:
      return 'default';
  }
};

const isProcessing = (status: string): boolean => {
  const upper = status?.toUpperCase();
  return ['UPLOADED', 'EXTRACTING', 'EMBEDDING', 'INDEXED', 'PROCESSING'].includes(upper);
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const ACCEPTED_FILE_TYPES = '.pdf,.doc,.docx,.xlsx,.xls,.csv,.txt';

// ==================== Main Component ====================
const DocumentsPage: React.FC = () => {
  const { showError, showWarning, showSuccess } = useNotification();
  const {
    documents,
    documentsLoading,
    uploadDocument,
    fetchDocuments,
    deleteDocument,
  } = useDocuments();

  // Local state for embedding models
  const [embeddingModels, setEmbeddingModels] = useState<ModelConfig[]>([]);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState<string>('');

  // Overwrite confirmation state
  const [overwriteDialogOpen, setOverwriteDialogOpen] = useState(false);
  const [existingDocument, setExistingDocument] = useState<any>(null);

  // Load embedding models on mount
  useEffect(() => {
    const loadEmbeddingModels = async () => {
      try {
        const result = await apiService.getAllModels('embedding');
        const modelList = result?.data || result;
        const models = Array.isArray(modelList) ? modelList : [];
        setEmbeddingModels(models.filter(
          (m: ModelConfig) => m.modelType === ModelType.EMBEDDING && m.isActive !== false
        ));
      } catch (error) {
        console.error('Failed to load embedding models:', error);
      }
    };
    loadEmbeddingModels();
  }, []);

  // Poll for status updates when documents are processing
  const hasProcessingDocs = documents.some((doc) => isProcessing(doc.status));

  useEffect(() => {
    if (!hasProcessingDocs) return;

    const pollInterval = setInterval(() => {
      fetchDocuments();
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [hasProcessingDocs, fetchDocuments]);

  // File selection handler
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setUploadDialogOpen(true);
    e.target.value = '';
  }, []);

  // Upload handler
  const handleUploadDocument = useCallback(async (overwrite: boolean = false) => {
    if (!selectedFile || !selectedEmbeddingModel) {
      showWarning('Please select both a file and an embedding model');
      return;
    }

    try {
      setUploading(true);
      await uploadDocument(selectedFile, selectedEmbeddingModel, overwrite);
      showSuccess('Document uploaded successfully');
      setUploadDialogOpen(false);
      setOverwriteDialogOpen(false);
      setSelectedFile(null);
      setSelectedEmbeddingModel('');
      setExistingDocument(null);
    } catch (error: any) {
      if (error.response?.status === 409) {
        const existingDoc = error.response?.data?.data?.existing_document;
        setExistingDocument(existingDoc);
        setUploadDialogOpen(false);
        setOverwriteDialogOpen(true);
      } else {
        showError('Upload failed: ' + (error.message || 'Unknown error'));
      }
    } finally {
      setUploading(false);
    }
  }, [selectedFile, selectedEmbeddingModel, uploadDocument, showSuccess, showError, showWarning]);

  const handleConfirmOverwrite = useCallback(() => {
    handleUploadDocument(true);
  }, [handleUploadDocument]);

  const handleCancelOverwrite = useCallback(() => {
    setOverwriteDialogOpen(false);
    setUploadDialogOpen(true);
    setExistingDocument(null);
  }, []);

  const handleDeleteDocument = useCallback(async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(id);
      showSuccess('Document deleted successfully');
    } catch (error: any) {
      showError('Delete failed: ' + (error.message || 'Unknown error'));
    }
  }, [deleteDocument, showSuccess, showError]);

  if (documentsLoading && documents.length === 0) {
    return <LoadingSpinner message="Loading documents..." />;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight={700}>
          Documents
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload and manage your documents for RAG processing
        </Typography>
      </Box>

      {/* Upload Section */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <input
              type="file"
              id="file-upload"
              accept={ACCEPTED_FILE_TYPES}
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />
            <label htmlFor="file-upload">
              <Button
                variant="contained"
                component="span"
                startIcon={<UploadFileIcon />}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Document'}
              </Button>
            </label>
            <Typography variant="body2" color="text.secondary">
              Supported formats: PDF, Word (.docx, .doc), Excel (.xlsx, .xls), CSV (.csv), Text (.txt)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            All Documents
          </Typography>

          {documents.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <DescriptionIcon sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No documents yet
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                Upload your first document to get started with RAG processing.
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>File Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Uploaded</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {documents.map((doc) => (
                    <TableRow key={doc.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {doc.fileName}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={doc.fileType?.toUpperCase() || 'N/A'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatFileSize(doc.fileSize)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(doc.uploadedAt).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={doc.status}
                          color={getStatusColor(doc.status)}
                          size="small"
                          icon={isProcessing(doc.status)
                            ? <CircularProgress size={14} color="inherit" />
                            : undefined
                          }
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteDocument(doc.id)}
                          title="Delete document"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Upload Document Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
              Supported formats: PDF, Word (.docx, .doc), Excel (.xlsx, .xls), CSV (.csv), Text (.txt)
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Selected file: <strong>{selectedFile?.name}</strong>
            </Typography>
            <FormControl fullWidth required>
              <InputLabel>Embedding Model</InputLabel>
              <Select
                value={selectedEmbeddingModel}
                onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
                label="Embedding Model"
              >
                {embeddingModels.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary">
              The embedding model will be used to create vector representations of your document for search and retrieval.
            </Typography>
            {embeddingModels.length === 0 && (
              <Typography variant="caption" color="warning.main">
                No embedding models available. Please ask an admin to configure an embedding model first.
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => handleUploadDocument(false)}
            variant="contained"
            disabled={uploading || !selectedEmbeddingModel}
          >
            {uploading ? <CircularProgress size={24} /> : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Overwrite Confirmation Dialog */}
      <Dialog
        open={overwriteDialogOpen}
        onClose={handleCancelOverwrite}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>File Already Exists</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <Typography variant="body1">
              A document with the filename <strong>{selectedFile?.name}</strong> already exists.
            </Typography>
            {existingDocument && (
              <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Existing file: {existingDocument.fileName || existingDocument.original_filename}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Uploaded: {new Date(existingDocument.uploadedAt).toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Size: {formatFileSize(existingDocument.fileSize || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {existingDocument.status}
                </Typography>
              </Box>
            )}
            <Typography variant="body2" color="warning.main">
              Do you want to overwrite the existing file, or cancel and rename your file?
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelOverwrite}>Cancel & Rename</Button>
          <Button
            onClick={handleConfirmOverwrite}
            variant="contained"
            color="warning"
            disabled={uploading}
          >
            {uploading ? <CircularProgress size={24} /> : 'Overwrite'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DocumentsPage;
