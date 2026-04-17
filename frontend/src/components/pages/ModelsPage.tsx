import React, { useState, useCallback } from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { useDocuments } from '../context_providers/DocumentContext';
import { useAuth } from '../context_providers/AuthContext';
import { useNotification } from '../context_providers/NotificationContext';
import { ModelConfig, ModelProvider } from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';

// ==================== Types ====================
interface ModelFormData {
  name: string;
  modelId: string;
  modelType: 'chat' | 'embedding';
  provider: ModelProvider;
  config: string;
  isActive: boolean;
}

const DEFAULT_CONFIG = JSON.stringify({
  api_key: '',
  temperature: 0.7,
  max_tokens: 2000,
}, null, 2);

const getInitialFormData = (): ModelFormData => ({
  name: '',
  modelId: '',
  modelType: 'chat',
  provider: ModelProvider.OPENAI,
  config: DEFAULT_CONFIG,
  isActive: true,
});

const buildFormDataFromModel = (model: ModelConfig): ModelFormData => {
  let configToShow: string;
  if (model.config) {
    configToShow = model.config;
  } else {
    const config = {
      api_key: '',
      temperature: model.temperature,
      max_tokens: model.maxTokens,
      top_p: model.topP,
      frequency_penalty: model.frequencyPenalty,
      presence_penalty: model.presencePenalty,
    };
    configToShow = JSON.stringify(config, null, 2);
  }

  return {
    name: model.name,
    modelId: model.modelId,
    modelType: model.modelType as 'chat' | 'embedding',
    provider: model.provider,
    config: configToShow,
    isActive: model.isActive ?? true,
  };
};

// ==================== Main Component ====================
const ModelsPage: React.FC = () => {
  const { user } = useAuth();
  const { showError, showSuccess } = useNotification();
  const { models, modelsLoading, createModel, updateModel, deleteModel } = useDocuments();

  const isAdmin = user?.isSuperAdmin || false;

  const filteredModels = isAdmin
    ? models
    : models.filter((model) => model.isActive !== false);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);
  const [formData, setFormData] = useState<ModelFormData>(getInitialFormData());

  const handleOpenDialog = useCallback((model?: ModelConfig) => {
    if (model) {
      setEditingModel(model);
      setFormData(buildFormDataFromModel(model));
    } else {
      setEditingModel(null);
      setFormData(getInitialFormData());
    }
    setDialogOpen(true);
  }, []);

  const handleCloseDialog = useCallback(() => {
    setDialogOpen(false);
    setEditingModel(null);
  }, []);

  const handleSubmit = useCallback(async () => {
    try {
      JSON.parse(formData.config);
    } catch {
      showError('Invalid JSON in config field');
      return;
    }

    const modelData = {
      name: formData.name,
      modelId: formData.modelId,
      modelType: formData.modelType,
      provider: formData.provider,
      config: formData.config,
      isActive: formData.isActive,
    };

    try {
      if (editingModel) {
        await updateModel(editingModel.id, modelData);
        showSuccess('Model updated successfully');
      } else {
        await createModel(modelData);
        showSuccess('Model created successfully');
      }
      handleCloseDialog();
    } catch (error: any) {
      showError('Failed to save model: ' + (error.message || 'Unknown error'));
    }
  }, [formData, editingModel, createModel, updateModel, showError, showSuccess, handleCloseDialog]);

  const handleDelete = useCallback(async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this model configuration?')) return;

    try {
      await deleteModel(id);
      showSuccess('Model deleted successfully');
    } catch (error: any) {
      showError('Failed to delete model: ' + (error.message || 'Unknown error'));
    }
  }, [deleteModel, showError, showSuccess]);

  const updateFormField = useCallback(<K extends keyof ModelFormData>(
    field: K,
    value: ModelFormData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  if (modelsLoading && filteredModels.length === 0) {
    return <LoadingSpinner message="Loading models..." />;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight={700}>
            Model Configurations
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {isAdmin
              ? 'Configure and manage AI models for document processing and chat'
              : 'View available AI models'
            }
          </Typography>
        </Box>
        {isAdmin && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Model
          </Button>
        )}
      </Box>

      {/* Model Cards Grid */}
      {filteredModels.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <PsychologyIcon sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No models configured yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Create your first model configuration to start processing documents
            </Typography>
            {isAdmin && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
              >
                Add Your First Model
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {filteredModels.map((model) => (
            <Grid item xs={12} md={6} lg={4} key={model.id}>
              <Card sx={{
                height: '100%',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
                },
              }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Typography variant="h6" fontWeight={600} noWrap sx={{ maxWidth: '70%' }}>
                      {model.name}
                    </Typography>
                    {isAdmin && (
                      <Box sx={{ display: 'flex', flexShrink: 0 }}>
                        <IconButton size="small" onClick={() => handleOpenDialog(model)} title="Edit model">
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(model.id)}
                          title="Delete model"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    )}
                  </Box>

                  <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    <Chip
                      label={model.modelType}
                      color="primary"
                      size="small"
                    />
                    <Chip
                      label={model.provider}
                      color="secondary"
                      size="small"
                    />
                    {isAdmin && (
                      <Chip
                        label={model.isActive !== false ? 'Active' : 'Inactive'}
                        color={model.isActive !== false ? 'success' : 'default'}
                        size="small"
                        variant={model.isActive !== false ? 'filled' : 'outlined'}
                      />
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      Model ID: {model.modelId}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Temperature: {model.temperature}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Max Tokens: {model.maxTokens}
                    </Typography>
                    {model.hasApiKey && (
                      <Typography variant="caption" color="success.main">
                        API Key configured
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.disabled" sx={{ mt: 1 }}>
                      Created: {new Date(model.createdAt).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingModel ? 'Edit Model Configuration' : 'Create New Model'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Model Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => updateFormField('name', e.target.value)}
              placeholder="e.g. GPT-4 Production"
            />

            <TextField
              label="Model ID"
              fullWidth
              required
              value={formData.modelId}
              onChange={(e) => updateFormField('modelId', e.target.value)}
              placeholder="e.g. gpt-4, claude-3-sonnet-20240229, text-embedding-ada-002"
              helperText="The specific model identifier from the provider"
            />

            <FormControl fullWidth required>
              <InputLabel>Model Type</InputLabel>
              <Select
                value={formData.modelType}
                label="Model Type"
                onChange={(e) => updateFormField('modelType', e.target.value as 'chat' | 'embedding')}
              >
                <MenuItem value="chat">Chat/Completion (LLM)</MenuItem>
                <MenuItem value="embedding">Embedding</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth required>
              <InputLabel>Provider</InputLabel>
              <Select
                value={formData.provider}
                label="Provider"
                onChange={(e) => updateFormField('provider', e.target.value as ModelProvider)}
              >
                <MenuItem value={ModelProvider.OPENAI}>OpenAI</MenuItem>
                <MenuItem value={ModelProvider.ANTHROPIC}>Anthropic</MenuItem>
                <MenuItem value={ModelProvider.CUSTOM}>Custom</MenuItem>
              </Select>
            </FormControl>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Configuration (JSON)
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={10}
                value={formData.config}
                onChange={(e) => updateFormField('config', e.target.value)}
                placeholder={'{\n  "api_key": "sk-...",\n  "temperature": 0.7,\n  "max_tokens": 2000,\n  "top_p": 1.0,\n  "frequency_penalty": 0.0,\n  "presence_penalty": 0.0\n}'}
                helperText="Include API key and model parameters in JSON format"
                sx={{
                  '& textarea': {
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                  },
                }}
              />
            </Box>

            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.isActive}
                  onChange={(e) => updateFormField('isActive', e.target.checked)}
                />
              }
              label="Active (visible to all users)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.name || !formData.modelId}
          >
            {editingModel ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ModelsPage;
