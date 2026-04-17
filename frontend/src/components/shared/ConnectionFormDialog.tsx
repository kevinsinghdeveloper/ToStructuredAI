import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Box,
  CircularProgress,
  Typography,
  Alert,
} from '@mui/material';
import { DatabaseConnection } from '../../types';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

interface ConnectionFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  connection?: DatabaseConnection;
}

interface FormState {
  name: string;
  dbType: string;
  host: string;
  port: number;
  databaseName: string;
  username: string;
  password: string;
  sslEnabled: boolean;
  schemaName: string;
}

interface FormErrors {
  name?: string;
  host?: string;
  port?: string;
  databaseName?: string;
  username?: string;
  password?: string;
}

const DB_TYPE_OPTIONS = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 'mssql', label: 'Microsoft SQL Server' },
];

const DEFAULT_PORTS: Record<string, number> = {
  postgresql: 5432,
  mysql: 3306,
  mssql: 1433,
};

const INITIAL_FORM_STATE: FormState = {
  name: '',
  dbType: 'postgresql',
  host: '',
  port: 5432,
  databaseName: '',
  username: '',
  password: '',
  sslEnabled: false,
  schemaName: 'public',
};

const ConnectionFormDialog: React.FC<ConnectionFormDialogProps> = ({
  open,
  onClose,
  onSaved,
  connection,
}) => {
  const { showSuccess, showError } = useNotification();
  const [form, setForm] = useState<FormState>(INITIAL_FORM_STATE);
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isEditing = !!connection;

  useEffect(() => {
    if (!open) return;

    if (connection) {
      setForm({
        name: connection.name || '',
        dbType: connection.dbType || 'postgresql',
        host: connection.host || '',
        port: connection.port || DEFAULT_PORTS[connection.dbType] || 5432,
        databaseName: connection.databaseName || '',
        username: connection.username || '',
        password: '',
        sslEnabled: connection.sslEnabled ?? false,
        schemaName: connection.schemaName || 'public',
      });
    } else {
      setForm(INITIAL_FORM_STATE);
    }

    setErrors({});
    setSubmitError(null);
  }, [open, connection]);

  const handleFieldChange = useCallback(
    (field: keyof FormState) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const value = field === 'port' ? parseInt(e.target.value, 10) || 0 : e.target.value;
        setForm((prev) => ({ ...prev, [field]: value }));
        setErrors((prev) => ({ ...prev, [field]: undefined }));
        setSubmitError(null);
      },
    []
  );

  const handleDbTypeChange = useCallback((dbType: string) => {
    setForm((prev) => ({
      ...prev,
      dbType,
      port: DEFAULT_PORTS[dbType] || prev.port,
      schemaName: dbType === 'postgresql' ? 'public' : dbType === 'mssql' ? 'dbo' : '',
    }));
  }, []);

  const handleCheckboxChange = useCallback(
    (field: keyof FormState) =>
      (_e: React.ChangeEvent<HTMLInputElement>, checked: boolean) => {
        setForm((prev) => ({ ...prev, [field]: checked }));
      },
    []
  );

  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!form.name.trim()) {
      newErrors.name = 'Connection name is required';
    }
    if (!form.host.trim()) {
      newErrors.host = 'Host is required';
    }
    if (!form.port || form.port < 1 || form.port > 65535) {
      newErrors.port = 'Port must be between 1 and 65535';
    }
    if (!form.databaseName.trim()) {
      newErrors.databaseName = 'Database name is required';
    }
    if (!form.username.trim()) {
      newErrors.username = 'Username is required';
    }
    if (!isEditing && !form.password.trim()) {
      newErrors.password = 'Password is required for new connections';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [form, isEditing]);

  const handleSubmit = useCallback(async () => {
    if (!validate()) return;

    setSaving(true);
    setSubmitError(null);

    const payload: Record<string, any> = {
      name: form.name.trim(),
      dbType: form.dbType,
      host: form.host.trim(),
      port: form.port,
      databaseName: form.databaseName.trim(),
      username: form.username.trim(),
      sslEnabled: form.sslEnabled,
      schemaName: form.schemaName.trim() || undefined,
    };

    if (form.password) {
      payload.password = form.password;
    }

    try {
      if (isEditing && connection) {
        await apiService.updateConnection(connection.id, payload);
        showSuccess(`Connection "${form.name}" updated successfully`);
      } else {
        await apiService.createConnection(payload);
        showSuccess(`Connection "${form.name}" created successfully`);
      }
      onSaved();
      onClose();
    } catch (error: any) {
      const message = error.message || 'Failed to save connection';
      setSubmitError(message);
      showError(message);
    } finally {
      setSaving(false);
    }
  }, [form, isEditing, connection, validate, onSaved, onClose, showSuccess, showError]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !saving) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit, saving]
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      onKeyDown={handleKeyDown}
    >
      <DialogTitle>
        {isEditing ? 'Edit Connection' : 'New Database Connection'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: 1 }}>
          {submitError && (
            <Alert severity="error" onClose={() => setSubmitError(null)}>
              {submitError}
            </Alert>
          )}

          <TextField
            label="Connection Name"
            value={form.name}
            onChange={handleFieldChange('name')}
            error={!!errors.name}
            helperText={errors.name}
            required
            fullWidth
            autoFocus
          />

          <FormControl fullWidth>
            <InputLabel>Database Type</InputLabel>
            <Select
              value={form.dbType}
              label="Database Type"
              onChange={(e) => handleDbTypeChange(e.target.value)}
            >
              {DB_TYPE_OPTIONS.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>
                  {opt.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Host"
              value={form.host}
              onChange={handleFieldChange('host')}
              error={!!errors.host}
              helperText={errors.host}
              required
              fullWidth
              placeholder="localhost or db.example.com"
            />
            <TextField
              label="Port"
              type="number"
              value={form.port}
              onChange={handleFieldChange('port')}
              error={!!errors.port}
              helperText={errors.port}
              required
              sx={{ width: 140, flexShrink: 0 }}
              inputProps={{ min: 1, max: 65535 }}
            />
          </Box>

          <TextField
            label="Database Name"
            value={form.databaseName}
            onChange={handleFieldChange('databaseName')}
            error={!!errors.databaseName}
            helperText={errors.databaseName}
            required
            fullWidth
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Username"
              value={form.username}
              onChange={handleFieldChange('username')}
              error={!!errors.username}
              helperText={errors.username}
              required
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={form.password}
              onChange={handleFieldChange('password')}
              error={!!errors.password}
              helperText={
                errors.password ||
                (isEditing ? 'Leave blank to keep existing password' : undefined)
              }
              required={!isEditing}
              fullWidth
            />
          </Box>

          <TextField
            label="Schema Name"
            value={form.schemaName}
            onChange={handleFieldChange('schemaName')}
            fullWidth
            placeholder={form.dbType === 'mssql' ? 'dbo' : 'public'}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={form.sslEnabled}
                onChange={handleCheckboxChange('sslEnabled')}
              />
            }
            label={
              <Typography variant="body2">
                Enable SSL/TLS encryption
              </Typography>
            }
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={saving}
        >
          {saving ? (
            <CircularProgress size={22} />
          ) : isEditing ? (
            'Save Changes'
          ) : (
            'Create Connection'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConnectionFormDialog;
