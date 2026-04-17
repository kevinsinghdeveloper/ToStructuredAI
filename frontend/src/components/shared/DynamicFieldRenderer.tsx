import React, { useState } from 'react';
import {
  Box,
  TextField,
  Checkbox,
  FormControlLabel,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  InputAdornment,
} from '@mui/material';
import { OpenInFull as ExpandIcon } from '@mui/icons-material';
import { PipelineField } from '../../types';

interface ExpandableCodeFieldProps {
  field: PipelineField;
  value: string;
  onChange: (fieldId: string, value: string) => void;
}

const CODE_EDITOR_SX = {
  fontFamily: '"Fira Code", "Cascadia Code", "JetBrains Mono", monospace',
  fontSize: '0.9rem',
  bgcolor: '#2b2b2b',
  color: '#ffffff',
  '& textarea': { color: '#ffffff' },
};

const ExpandableCodeField: React.FC<ExpandableCodeFieldProps> = ({ field, value, onChange }) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogValue, setDialogValue] = useState('');

  const handleOpen = () => {
    setDialogValue(value || '');
    setDialogOpen(true);
  };

  const handleApply = () => {
    onChange(field.id, dialogValue);
    setDialogOpen(false);
  };

  const handleCancel = () => {
    setDialogOpen(false);
  };

  const handleTabKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const currentValue = target.value;
      const newValue = currentValue.substring(0, start) + '  ' + currentValue.substring(end);
      if (dialogOpen) {
        setDialogValue(newValue);
      } else {
        onChange(field.id, newValue);
      }
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = start + 2;
      });
    }
  };

  return (
    <>
      <TextField
        label={field.name}
        value={value || ''}
        onChange={(e) => onChange(field.id, e.target.value)}
        onKeyDown={handleTabKey}
        fullWidth
        required={field.required}
        helperText={field.description || 'Enter code here'}
        multiline
        minRows={6}
        maxRows={12}
        placeholder="Enter code..."
        size="small"
        InputProps={{
          sx: CODE_EDITOR_SX,
          endAdornment: (
            <InputAdornment position="end" sx={{ alignSelf: 'flex-start', mt: 1 }}>
              <IconButton
                onClick={handleOpen}
                size="small"
                sx={{ color: 'grey.400' }}
                title="Expand to fullscreen editor"
              >
                <ExpandIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      <Dialog
        open={dialogOpen}
        onClose={handleCancel}
        fullScreen
        PaperProps={{ sx: { bgcolor: '#1e1e1e' } }}
      >
        <DialogTitle
          sx={{
            bgcolor: '#2b2b2b',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            py: 1.5,
          }}
        >
          <Box>
            <Typography variant="h6" component="span">
              {field.name}
            </Typography>
            {field.required && (
              <Typography component="span" color="error.main" sx={{ ml: 0.5 }}>*</Typography>
            )}
          </Box>
          {field.description && (
            <Typography variant="caption" color="grey.400">
              {field.description}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column' }}>
          <TextField
            fullWidth
            multiline
            value={dialogValue}
            onChange={(e) => setDialogValue(e.target.value)}
            onKeyDown={handleTabKey}
            placeholder="Enter code..."
            InputProps={{
              sx: {
                ...CODE_EDITOR_SX,
                bgcolor: '#1e1e1e',
                height: '100%',
                alignItems: 'flex-start',
                '& textarea': {
                  color: '#ffffff',
                  minHeight: 'calc(100vh - 160px)',
                },
                '& fieldset': { border: 'none' },
              },
            }}
            sx={{ flex: 1, '& .MuiInputBase-root': { height: '100%' } }}
          />
        </DialogContent>
        <DialogActions sx={{ bgcolor: '#2b2b2b', px: 3, py: 1.5 }}>
          <Button onClick={handleCancel} sx={{ color: 'grey.400' }}>
            Cancel
          </Button>
          <Button onClick={handleApply} variant="contained">
            Apply
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

const isMultilineText = (field: PipelineField): boolean => {
  const keywords = ['instruction', 'description', 'prompt', 'template', 'content', 'notes'];
  const nameLower = field.name.toLowerCase();
  return keywords.some((kw) => nameLower.includes(kw));
};

interface DynamicFieldRendererProps {
  fields: PipelineField[];
  fieldValues: Record<string, any>;
  onChange: (fieldId: string, value: any) => void;
}

const DynamicFieldRenderer: React.FC<DynamicFieldRendererProps> = ({
  fields,
  fieldValues,
  onChange,
}) => {
  if (!fields || fields.length === 0) {
    return null;
  }

  const renderField = (field: PipelineField) => {
    const value = fieldValues[field.id];

    switch (field.field_type) {
      case 'code':
        return (
          <ExpandableCodeField
            key={field.id}
            field={field}
            value={value ?? ''}
            onChange={onChange}
          />
        );

      case 'text':
        return (
          <TextField
            key={field.id}
            label={field.name}
            value={value ?? ''}
            onChange={(e) => onChange(field.id, e.target.value)}
            fullWidth
            required={field.required}
            helperText={field.description}
            multiline={isMultilineText(field)}
            minRows={isMultilineText(field) ? 3 : undefined}
            maxRows={isMultilineText(field) ? 8 : undefined}
            size="small"
          />
        );

      case 'number':
        return (
          <TextField
            key={field.id}
            label={field.name}
            type="number"
            value={value ?? ''}
            onChange={(e) => {
              const parsed = e.target.value === '' ? '' : Number(e.target.value);
              onChange(field.id, parsed);
            }}
            fullWidth
            required={field.required}
            helperText={field.description}
            size="small"
            inputProps={{
              min: field.validation?.min,
              max: field.validation?.max,
              step: field.validation?.step ?? 1,
            }}
          />
        );

      case 'boolean':
        return (
          <FormControlLabel
            key={field.id}
            control={
              <Checkbox
                checked={Boolean(value)}
                onChange={(e) => onChange(field.id, e.target.checked)}
              />
            }
            label={
              <Box>
                <Typography variant="body2">{field.name}</Typography>
                {field.description && (
                  <Typography variant="caption" color="text.secondary">
                    {field.description}
                  </Typography>
                )}
              </Box>
            }
          />
        );

      case 'date':
        return (
          <TextField
            key={field.id}
            label={field.name}
            type="date"
            value={value ?? ''}
            onChange={(e) => onChange(field.id, e.target.value)}
            fullWidth
            required={field.required}
            helperText={field.description}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
        );

      case 'datetime':
        return (
          <TextField
            key={field.id}
            label={field.name}
            type="datetime-local"
            value={value ?? ''}
            onChange={(e) => onChange(field.id, e.target.value)}
            fullWidth
            required={field.required}
            helperText={field.description}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
        );

      case 'array': {
        const arrayValue = Array.isArray(value) ? value.join('\n') : (value ?? '');
        return (
          <TextField
            key={field.id}
            label={field.name}
            value={arrayValue}
            onChange={(e) => {
              const items = e.target.value.split('\n');
              onChange(field.id, items);
            }}
            fullWidth
            required={field.required}
            helperText={field.description ? `${field.description} (one item per line)` : 'One item per line'}
            multiline
            minRows={3}
            maxRows={10}
            size="small"
            placeholder="Enter one item per line..."
          />
        );
      }

      default:
        return (
          <TextField
            key={field.id}
            label={field.name}
            value={value ?? ''}
            onChange={(e) => onChange(field.id, e.target.value)}
            fullWidth
            required={field.required}
            helperText={field.description}
            size="small"
          />
        );
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {fields.map((field) => renderField(field))}
    </Box>
  );
};

export default DynamicFieldRenderer;
