import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
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
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Tooltip,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Description as DocumentIcon,
  Storage as DatabaseIcon,
  Search as QueryableIcon,
  FolderOpen as EmptyIcon,
} from '@mui/icons-material';
import { Source } from '../../types';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

interface SourcesTableProps {
  sources: Source[];
  onRefresh: () => void;
  loading?: boolean;
}

const getSourceTypeChipProps = (
  sourceType: Source['sourceType']
): { label: string; color: 'primary' | 'secondary'; icon: React.ReactElement } => {
  switch (sourceType) {
    case 'database':
      return { label: 'Database', color: 'secondary', icon: <DatabaseIcon fontSize="small" /> };
    case 'document':
    default:
      return { label: 'Document', color: 'primary', icon: <DocumentIcon fontSize="small" /> };
  }
};

const getStatusChipProps = (
  status: Source['status']
): { label: string; color: 'success' | 'warning' | 'error' | 'default' } => {
  switch (status) {
    case 'ready':
      return { label: 'Ready', color: 'success' };
    case 'metadata_extracted':
      return { label: 'Metadata Extracted', color: 'success' };
    case 'pending':
      return { label: 'Pending', color: 'warning' };
    case 'error':
      return { label: 'Error', color: 'error' };
    default:
      return { label: status || 'Unknown', color: 'default' };
  }
};

const SourcesTable: React.FC<SourcesTableProps> = ({
  sources,
  onRefresh,
  loading = false,
}) => {
  const { showSuccess, showError } = useNotification();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteSource, setConfirmDeleteSource] = useState<Source | null>(null);

  const handleDeleteSource = useCallback(async () => {
    if (!confirmDeleteSource) return;

    setDeletingId(confirmDeleteSource.id);
    try {
      await apiService.deleteSource(confirmDeleteSource.id);
      showSuccess(`Source "${confirmDeleteSource.name}" deleted successfully`);
      onRefresh();
    } catch (error: any) {
      showError('Delete failed: ' + (error.message || 'Unknown error'));
    } finally {
      setDeletingId(null);
      setConfirmDeleteSource(null);
    }
  }, [confirmDeleteSource, onRefresh, showSuccess, showError]);

  if (loading && sources.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  if (sources.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <EmptyIcon sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No sources available
        </Typography>
        <Typography color="text.secondary">
          Upload documents or connect a database to create sources for your pipelines.
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <TableContainer component={Paper} elevation={0}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Table Name</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sources.map((source) => {
              const typeProps = getSourceTypeChipProps(source.sourceType);
              const statusProps = getStatusChipProps(source.status);
              const isDeleting = deletingId === source.id;

              return (
                <TableRow key={source.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" fontWeight={500}>
                        {source.name}
                      </Typography>
                      {source.isQueryable && (
                        <Tooltip title="Queryable - can be used for SQL generation">
                          <QueryableIcon
                            fontSize="small"
                            color="info"
                            sx={{ fontSize: 16 }}
                          />
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={typeProps.label}
                      color={typeProps.color}
                      size="small"
                      icon={typeProps.icon}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={statusProps.label}
                      color={statusProps.color}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {source.tableName || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Delete source">
                      <span>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => setConfirmDeleteSource(source)}
                          disabled={isDeleting}
                        >
                          {isDeleting ? (
                            <CircularProgress size={18} color="inherit" />
                          ) : (
                            <DeleteIcon fontSize="small" />
                          )}
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!confirmDeleteSource}
        onClose={() => setConfirmDeleteSource(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Delete Source</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the source{' '}
            <strong>{confirmDeleteSource?.name}</strong>? This action cannot be undone.
            Any pipelines using this source may be affected.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setConfirmDeleteSource(null)}
            disabled={!!deletingId}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteSource}
            variant="contained"
            color="error"
            disabled={!!deletingId}
          >
            {deletingId ? <CircularProgress size={22} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SourcesTable;
