import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  CircularProgress,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import {
  Storage as StorageIcon,
  TableChart as TableIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { DatabaseConnection, ConnectionTable } from '../../types';
import apiService from '../../utils/api.service';

interface AddDBSourceDialogProps {
  open: boolean;
  onClose: () => void;
  onSourceCreated: () => void;
  connections: DatabaseConnection[];
}

const STEPS = ['Select Connection', 'Choose Tables', 'Confirm & Create'];

const AddDBSourceDialog: React.FC<AddDBSourceDialogProps> = ({
  open,
  onClose,
  onSourceCreated,
  connections,
}) => {
  const [activeStep, setActiveStep] = useState<number>(0);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [tables, setTables] = useState<ConnectionTable[]>([]);
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [loadingTables, setLoadingTables] = useState<boolean>(false);
  const [creating, setCreating] = useState<boolean>(false);
  const [creationProgress, setCreationProgress] = useState<number>(0);
  const [error, setError] = useState<string>('');

  const connectedConnections = connections.filter(
    (conn) => conn.status === 'connected'
  );

  const selectedConnection = connectedConnections.find(
    (conn) => conn.id === selectedConnectionId
  );

  const resetState = useCallback(() => {
    setActiveStep(0);
    setSelectedConnectionId('');
    setTables([]);
    setSelectedTables([]);
    setLoadingTables(false);
    setCreating(false);
    setCreationProgress(0);
    setError('');
  }, []);

  useEffect(() => {
    if (!open) {
      resetState();
    }
  }, [open, resetState]);

  const fetchTables = async (connectionId: string): Promise<void> => {
    setLoadingTables(true);
    setError('');
    try {
      const response = await apiService.getConnectionTables(connectionId);
      const fetchedTables: ConnectionTable[] =
        response?.data?.tables ?? response?.data ?? response?.tables ?? [];
      setTables(fetchedTables);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to fetch tables';
      setError(message);
      setTables([]);
    } finally {
      setLoadingTables(false);
    }
  };

  const handleNext = async (): Promise<void> => {
    if (activeStep === 0) {
      await fetchTables(selectedConnectionId);
      setActiveStep(1);
    } else if (activeStep === 1) {
      setActiveStep(2);
    }
  };

  const handleBack = (): void => {
    if (activeStep === 1) {
      setSelectedTables([]);
      setTables([]);
      setError('');
    }
    setActiveStep((prev) => prev - 1);
  };

  const handleTableToggle = (tableName: string): void => {
    setSelectedTables((prev) =>
      prev.includes(tableName)
        ? prev.filter((t) => t !== tableName)
        : [...prev, tableName]
    );
  };

  const handleSelectAllTables = (): void => {
    if (selectedTables.length === tables.length) {
      setSelectedTables([]);
    } else {
      setSelectedTables(tables.map((t) => t.name));
    }
  };

  const handleCreate = async (): Promise<void> => {
    setCreating(true);
    setCreationProgress(0);
    setError('');

    const failures: string[] = [];

    for (let i = 0; i < selectedTables.length; i++) {
      const tableName = selectedTables[i];
      try {
        await apiService.createSourceFromTable(selectedConnectionId, tableName, {
          name: tableName,
        });
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : `Failed to create source for ${tableName}`;
        failures.push(`${tableName}: ${message}`);
      }
      setCreationProgress(i + 1);
    }

    setCreating(false);

    if (failures.length > 0 && failures.length === selectedTables.length) {
      setError(`All sources failed to create:\n${failures.join('\n')}`);
      return;
    }

    if (failures.length > 0) {
      setError(
        `${selectedTables.length - failures.length} of ${selectedTables.length} sources created. Failures:\n${failures.join('\n')}`
      );
    }

    onSourceCreated();
    onClose();
  };

  const handleClose = (): void => {
    if (!creating) {
      onClose();
    }
  };

  const renderStepContent = (): React.ReactNode => {
    switch (activeStep) {
      case 0:
        return renderConnectionStep();
      case 1:
        return renderTablesStep();
      case 2:
        return renderConfirmStep();
      default:
        return null;
    }
  };

  const renderConnectionStep = (): React.ReactNode => {
    if (connectedConnections.length === 0) {
      return (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No connected database connections available. Please add and test a
          database connection first.
        </Alert>
      );
    }

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Select a database connection to browse its tables.
        </Typography>
        <FormControl fullWidth>
          <InputLabel id="connection-select-label">Connection</InputLabel>
          <Select
            labelId="connection-select-label"
            value={selectedConnectionId}
            label="Connection"
            onChange={(e) => setSelectedConnectionId(e.target.value)}
          >
            {connectedConnections.map((conn) => (
              <MenuItem key={conn.id} value={conn.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <StorageIcon fontSize="small" color="primary" />
                  <Box>
                    <Typography variant="body2">{conn.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {conn.dbType}
                      {conn.databaseName ? ` - ${conn.databaseName}` : ''}
                    </Typography>
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
    );
  };

  const renderTablesStep = (): React.ReactNode => {
    if (loadingTables) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      );
    }

    if (tables.length === 0 && !error) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          No tables found in this connection.
        </Alert>
      );
    }

    return (
      <Box sx={{ mt: 2 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 1,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Select tables to create as sources ({selectedTables.length} of{' '}
            {tables.length} selected)
          </Typography>
          <Button size="small" onClick={handleSelectAllTables}>
            {selectedTables.length === tables.length
              ? 'Deselect All'
              : 'Select All'}
          </Button>
        </Box>
        <Divider />
        <List
          dense
          sx={{
            maxHeight: 320,
            overflow: 'auto',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            mt: 1,
          }}
        >
          {tables.map((table) => {
            const isSelected = selectedTables.includes(table.name);
            return (
              <ListItem key={table.name} disablePadding>
                <ListItemButton
                  onClick={() => handleTableToggle(table.name)}
                  dense
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Checkbox
                      edge="start"
                      checked={isSelected}
                      tabIndex={-1}
                      disableRipple
                      size="small"
                    />
                  </ListItemIcon>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <TableIcon fontSize="small" color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary={table.name}
                    secondary={table.schema || undefined}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>
    );
  };

  const renderConfirmStep = (): React.ReactNode => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Connection
      </Typography>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          mb: 3,
          p: 1.5,
          borderRadius: 2,
          bgcolor: 'action.hover',
        }}
      >
        <StorageIcon color="primary" />
        <Box>
          <Typography variant="body2" fontWeight={600}>
            {selectedConnection?.name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {selectedConnection?.dbType}
            {selectedConnection?.databaseName
              ? ` - ${selectedConnection.databaseName}`
              : ''}
          </Typography>
        </Box>
      </Box>

      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Tables ({selectedTables.length})
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {selectedTables.map((tableName) => (
          <Chip
            key={tableName}
            icon={<TableIcon />}
            label={tableName}
            variant="outlined"
            size="small"
          />
        ))}
      </Box>

      {creating && (
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <CircularProgress size={32} sx={{ mb: 1 }} />
          <Typography variant="body2" color="text.secondary">
            Creating sources... {creationProgress} of {selectedTables.length}
          </Typography>
        </Box>
      )}
    </Box>
  );

  const isNextDisabled = (): boolean => {
    if (activeStep === 0) return !selectedConnectionId;
    if (activeStep === 1) return selectedTables.length === 0;
    return false;
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { minHeight: 480 } }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Typography variant="h6" component="span">
          Add Database Sources
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ pt: 1 }}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {renderStepContent()}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={handleClose} disabled={creating}>
          Cancel
        </Button>
        <Box sx={{ flex: 1 }} />
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={creating}>
            Back
          </Button>
        )}
        {activeStep < 2 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={isNextDisabled() || loadingTables}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={creating}
            startIcon={
              creating ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <CheckCircleIcon />
              )
            }
          >
            {creating ? 'Creating...' : 'Create Sources'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AddDBSourceDialog;
