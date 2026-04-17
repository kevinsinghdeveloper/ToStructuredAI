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
  Edit as EditIcon,
  PlayArrow as TestIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { DatabaseConnection } from '../../types';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

interface ConnectionsTableProps {
  connections: DatabaseConnection[];
  onRefresh: () => void;
  loading?: boolean;
  onEdit?: (connection: DatabaseConnection) => void;
}

const getStatusChipProps = (status: DatabaseConnection['status']): { label: string; color: 'success' | 'error' | 'default' } => {
  switch (status) {
    case 'connected':
      return { label: 'Connected', color: 'success' };
    case 'failed':
      return { label: 'Failed', color: 'error' };
    case 'untested':
    default:
      return { label: 'Untested', color: 'default' };
  }
};

const ConnectionsTable: React.FC<ConnectionsTableProps> = ({
  connections,
  onRefresh,
  loading = false,
  onEdit,
}) => {
  const { showSuccess, showError } = useNotification();
  const [testingId, setTestingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteConn, setConfirmDeleteConn] = useState<DatabaseConnection | null>(null);

  const handleTestConnection = useCallback(async (connectionId: string) => {
    setTestingId(connectionId);
    try {
      const result = await apiService.testConnection(connectionId);
      const status = result?.data?.status || result?.status;
      if (status === 'connected') {
        showSuccess('Connection test successful');
      } else {
        showError('Connection test failed: ' + (result?.data?.error || result?.error || 'Unknown error'));
      }
      onRefresh();
    } catch (error: any) {
      showError('Connection test failed: ' + (error.message || 'Unknown error'));
    } finally {
      setTestingId(null);
    }
  }, [onRefresh, showSuccess, showError]);

  const handleDeleteConnection = useCallback(async () => {
    if (!confirmDeleteConn) return;

    setDeletingId(confirmDeleteConn.id);
    try {
      await apiService.deleteConnection(confirmDeleteConn.id);
      showSuccess(`Connection "${confirmDeleteConn.name}" deleted successfully`);
      onRefresh();
    } catch (error: any) {
      showError('Delete failed: ' + (error.message || 'Unknown error'));
    } finally {
      setDeletingId(null);
      setConfirmDeleteConn(null);
    }
  }, [confirmDeleteConn, onRefresh, showSuccess, showError]);

  if (loading && connections.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  if (connections.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <StorageIcon sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No database connections
        </Typography>
        <Typography color="text.secondary">
          Add a database connection to start querying your data.
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
              <TableCell>Host</TableCell>
              <TableCell>Database</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {connections.map((conn) => {
              const chipProps = getStatusChipProps(conn.status);
              const isTesting = testingId === conn.id;
              const isDeleting = deletingId === conn.id;

              return (
                <TableRow key={conn.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {conn.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={conn.dbType?.toUpperCase() || 'N/A'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {conn.host || '-'}
                      {conn.port ? `:${conn.port}` : ''}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {conn.databaseName || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={chipProps.label}
                      color={chipProps.color}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
                      <Tooltip title="Test connection">
                        <span>
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleTestConnection(conn.id)}
                            disabled={isTesting || isDeleting}
                          >
                            {isTesting ? (
                              <CircularProgress size={18} color="inherit" />
                            ) : (
                              <TestIcon fontSize="small" />
                            )}
                          </IconButton>
                        </span>
                      </Tooltip>
                      {onEdit && (
                        <Tooltip title="Edit connection">
                          <span>
                            <IconButton
                              size="small"
                              color="info"
                              onClick={() => onEdit(conn)}
                              disabled={isDeleting}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      )}
                      <Tooltip title="Delete connection">
                        <span>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setConfirmDeleteConn(conn)}
                            disabled={isTesting || isDeleting}
                          >
                            {isDeleting ? (
                              <CircularProgress size={18} color="inherit" />
                            ) : (
                              <DeleteIcon fontSize="small" />
                            )}
                          </IconButton>
                        </span>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!confirmDeleteConn}
        onClose={() => setConfirmDeleteConn(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Delete Connection</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the connection{' '}
            <strong>{confirmDeleteConn?.name}</strong>? This action cannot be undone.
            Any sources linked to this connection will also be affected.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setConfirmDeleteConn(null)}
            disabled={!!deletingId}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConnection}
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

export default ConnectionsTable;
