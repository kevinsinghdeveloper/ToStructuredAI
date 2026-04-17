import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  FolderOpen as EmptyIcon,
} from '@mui/icons-material';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useNotification } from '../context_providers/NotificationContext';
import { useDocuments } from '../context_providers/DocumentContext';
import apiService from '../../utils/api.service';
import { StructuredOutput, OutputFormat } from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';

// ==================== Helpers ====================

const formatDate = (iso: string): string => {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getFormatColor = (
  format: string
): 'primary' | 'secondary' | 'success' | 'warning' | 'info' => {
  switch (format?.toUpperCase()) {
    case 'JSON':
      return 'primary';
    case 'CSV':
      return 'success';
    case 'EXCEL':
      return 'warning';
    case 'XML':
      return 'info';
    default:
      return 'secondary';
  }
};

const getFileExtension = (format: string): string => {
  switch (format?.toUpperCase()) {
    case 'JSON':
      return 'json';
    case 'CSV':
      return 'csv';
    case 'EXCEL':
      return 'xlsx';
    case 'XML':
      return 'xml';
    default:
      return 'dat';
  }
};

// ==================== Main Component ====================
const OutputsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showError, showSuccess } = useNotification();
  const { pipelines } = useDocuments();

  const pipelineIdFilter = searchParams.get('pipeline_id') || undefined;

  // State
  const [outputs, setOutputs] = useState<StructuredOutput[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Delete confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [outputToDelete, setOutputToDelete] = useState<StructuredOutput | null>(null);
  const [deleting, setDeleting] = useState(false);

  // ==================== Data Loading ====================

  const loadOutputs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.getOutputs(pipelineIdFilter);
      const data = result?.data || result || [];
      setOutputs(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || 'Failed to load outputs');
      showError('Failed to load outputs');
    } finally {
      setLoading(false);
    }
  }, [pipelineIdFilter, showError]);

  useEffect(() => {
    loadOutputs();
  }, [loadOutputs]);

  // ==================== Helpers ====================

  const getPipelineName = useCallback(
    (pipelineId: string): string => {
      const pipeline = pipelines.find((p) => p.id === pipelineId);
      return pipeline?.name || `Pipeline ${pipelineId.substring(0, 8)}...`;
    },
    [pipelines]
  );

  // ==================== Handlers ====================

  const handleDownload = async (output: StructuredOutput) => {
    try {
      const blob = await apiService.downloadOutput(output.id, output.pipelineId);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      const extension = getFileExtension(output.format);
      const pipelineName = getPipelineName(output.pipelineId)
        .replace(/\s+/g, '_')
        .toLowerCase();
      link.setAttribute('download', `${pipelineName}_output.${extension}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      showSuccess('Download started');
    } catch (err: any) {
      showError('Failed to download output: ' + err.message);
    }
  };

  const handleDeleteClick = (output: StructuredOutput) => {
    setOutputToDelete(output);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!outputToDelete) return;
    try {
      setDeleting(true);
      await apiService.deleteOutput(outputToDelete.id, outputToDelete.pipelineId);
      setOutputs((prev) => prev.filter((o) => o.id !== outputToDelete.id));
      showSuccess('Output deleted successfully');
      setDeleteDialogOpen(false);
      setOutputToDelete(null);
    } catch (err: any) {
      showError('Failed to delete output: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setOutputToDelete(null);
  };

  // ==================== Render ====================

  if (loading) {
    return <LoadingSpinner message="Loading outputs..." />;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 4,
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Outputs
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            {pipelineIdFilter
              ? `Outputs for pipeline: ${getPipelineName(pipelineIdFilter)}`
              : 'View and download structured outputs from your pipelines'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {pipelineIdFilter && (
            <Button variant="outlined" onClick={() => navigate('/outputs')}>
              Show All Outputs
            </Button>
          )}
          <Tooltip title="Refresh">
            <IconButton onClick={loadOutputs} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} action={
          <Button color="inherit" size="small" onClick={loadOutputs}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      )}

      {/* Outputs Table */}
      <Card>
        <CardContent>
          {outputs.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <EmptyIcon sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No outputs yet
              </Typography>
              <Typography variant="body2" color="text.disabled" sx={{ mb: 2 }}>
                Run a pipeline to generate structured outputs from your documents.
              </Typography>
              <Button variant="outlined" onClick={() => navigate('/pipelines')}>
                Go to Pipelines
              </Button>
            </Box>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Pipeline</TableCell>
                    <TableCell>Format</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {outputs.map((output) => (
                    <TableRow key={output.id} hover>
                      <TableCell>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          sx={{
                            cursor: 'pointer',
                            '&:hover': { color: 'primary.main' },
                          }}
                          onClick={() => navigate(`/pipelines/${output.pipelineId}`)}
                        >
                          {getPipelineName(output.pipelineId)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={output.format}
                          size="small"
                          color={getFormatColor(output.format)}
                          variant="outlined"
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
                            onClick={() => handleDownload(output)}
                          >
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteClick(output)}
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

      {/* Summary */}
      {outputs.length > 0 && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Typography variant="caption" color="text.secondary">
            {outputs.length} output{outputs.length !== 1 ? 's' : ''} total
          </Typography>
        </Box>
      )}

      {/* ==================== Delete Confirmation Dialog ==================== */}
      <Dialog open={deleteDialogOpen} onClose={handleCancelDelete} maxWidth="xs" fullWidth>
        <DialogTitle>Delete Output</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete this output?
          </Typography>
          {outputToDelete && (
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: 'background.default',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Pipeline: {getPipelineName(outputToDelete.pipelineId)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Format: {outputToDelete.format}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Created: {formatDate(outputToDelete.createdAt)}
              </Typography>
            </Box>
          )}
          <Typography variant="body2" color="error.main" sx={{ mt: 2 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} disabled={deleting}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={deleting}
          >
            {deleting ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OutputsPage;
