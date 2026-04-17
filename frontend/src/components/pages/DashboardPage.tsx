import React from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  AccountTree as AccountTreeIcon,
  CheckCircle as CheckCircleIcon,
  Psychology as PsychologyIcon,
  UploadFile as UploadFileIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useDocuments } from '../context_providers/DocumentContext';
import { useAuth } from '../context_providers/AuthContext';
import { DocumentStatus, PipelineStatus } from '../../types';
import LoadingSpinner from '../shared/LoadingSpinner';

// ==================== Constants ====================
const STAT_CARD_STYLES = {
  documents: {
    gradient: 'linear-gradient(135deg, rgba(123, 109, 246, 0.15), rgba(123, 109, 246, 0.05))',
    iconBg: 'rgba(123, 109, 246, 0.15)',
    color: '#7b6df6',
  },
  pipelines: {
    gradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05))',
    iconBg: 'rgba(16, 185, 129, 0.15)',
    color: '#10b981',
  },
  ready: {
    gradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05))',
    iconBg: 'rgba(59, 130, 246, 0.15)',
    color: '#3b82f6',
  },
  models: {
    gradient: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05))',
    iconBg: 'rgba(245, 158, 11, 0.15)',
    color: '#f59e0b',
  },
};

// ==================== Helpers ====================
const getDocumentStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (status?.toUpperCase()) {
    case 'READY':
    case 'COMPLETED':
      return 'success';
    case 'UPLOADED':
    case 'EXTRACTING':
    case 'EMBEDDING':
    case 'PROCESSING':
      return 'warning';
    case 'ERROR':
    case 'FAILED':
      return 'error';
    default:
      return 'default';
  }
};

const getPipelineStatusColor = (status: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'processing':
    case 'pending':
      return 'warning';
    case 'failed':
    case 'cancelled':
      return 'error';
    default:
      return 'default';
  }
};

const isDocumentProcessing = (status: string): boolean => {
  const upper = status?.toUpperCase();
  return ['UPLOADED', 'EXTRACTING', 'EMBEDDING', 'PROCESSING'].includes(upper);
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// ==================== Main Component ====================
const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const {
    documents,
    documentsLoading,
    pipelines,
    pipelinesLoading,
    models,
    modelsLoading,
  } = useDocuments();

  const isLoading = documentsLoading && documents.length === 0
    && pipelinesLoading && pipelines.length === 0;

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  const readyDocuments = documents.filter(
    (d) => d.status === DocumentStatus.READY || d.status?.toUpperCase() === 'COMPLETED'
  );
  const activeModels = models.filter((m) => m.isActive !== false);

  const recentDocuments = [...documents]
    .sort((a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime())
    .slice(0, 5);

  const recentPipelines = [...pipelines]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 5);

  const firstName = user?.firstName || 'there';

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Welcome back, {firstName}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your documents, pipelines, and AI models from one place.
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: STAT_CARD_STYLES.documents.gradient,
            border: '1px solid rgba(148, 163, 184, 0.08)',
            transition: 'all 0.3s ease',
            '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
          }}>
            <CardContent sx={{ py: 3 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: '12px',
                bgcolor: STAT_CARD_STYLES.documents.iconBg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                mb: 2, color: STAT_CARD_STYLES.documents.color,
              }}>
                <DescriptionIcon sx={{ fontSize: 28 }} />
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
                {documents.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">Total Documents</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: STAT_CARD_STYLES.pipelines.gradient,
            border: '1px solid rgba(148, 163, 184, 0.08)',
            transition: 'all 0.3s ease',
            '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
          }}>
            <CardContent sx={{ py: 3 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: '12px',
                bgcolor: STAT_CARD_STYLES.pipelines.iconBg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                mb: 2, color: STAT_CARD_STYLES.pipelines.color,
              }}>
                <AccountTreeIcon sx={{ fontSize: 28 }} />
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
                {pipelines.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">Active Pipelines</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: STAT_CARD_STYLES.ready.gradient,
            border: '1px solid rgba(148, 163, 184, 0.08)',
            transition: 'all 0.3s ease',
            '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
          }}>
            <CardContent sx={{ py: 3 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: '12px',
                bgcolor: STAT_CARD_STYLES.ready.iconBg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                mb: 2, color: STAT_CARD_STYLES.ready.color,
              }}>
                <CheckCircleIcon sx={{ fontSize: 28 }} />
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
                {readyDocuments.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">Ready Documents</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: STAT_CARD_STYLES.models.gradient,
            border: '1px solid rgba(148, 163, 184, 0.08)',
            transition: 'all 0.3s ease',
            '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
          }}>
            <CardContent sx={{ py: 3 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: '12px',
                bgcolor: STAT_CARD_STYLES.models.iconBg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                mb: 2, color: STAT_CARD_STYLES.models.color,
              }}>
                <PsychologyIcon sx={{ fontSize: 28 }} />
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
                {activeModels.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">Models</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Documents & Recent Pipelines */}
      <Grid container spacing={3}>
        {/* Recent Documents */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight={600}>
                  Recent Documents
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<UploadFileIcon />}
                  onClick={() => navigate('/documents')}
                >
                  Upload
                </Button>
              </Box>

              {recentDocuments.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <DescriptionIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">
                    No documents yet. Upload your first document to get started.
                  </Typography>
                </Box>
              ) : (
                <TableContainer component={Paper} elevation={0}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>File Name</TableCell>
                        <TableCell>Size</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentDocuments.map((doc) => (
                        <TableRow key={doc.id} hover>
                          <TableCell>
                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                              {doc.fileName}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {formatFileSize(doc.fileSize)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={doc.status}
                              color={getDocumentStatusColor(doc.status)}
                              size="small"
                              icon={isDocumentProcessing(doc.status)
                                ? <CircularProgress size={14} color="inherit" />
                                : undefined
                              }
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Pipelines */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight={600}>
                  Recent Pipelines
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => navigate('/pipelines')}
                >
                  Create
                </Button>
              </Box>

              {recentPipelines.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <AccountTreeIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">
                    No pipelines yet. Create your first pipeline to start using RAG queries.
                  </Typography>
                </Box>
              ) : (
                <TableContainer component={Paper} elevation={0}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Documents</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentPipelines.map((pipeline) => (
                        <TableRow key={pipeline.id} hover>
                          <TableCell>
                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                              {pipeline.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {pipeline.documentIds?.length || 0} docs
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={pipeline.status || PipelineStatus.PENDING}
                              color={getPipelineStatusColor(pipeline.status || PipelineStatus.PENDING)}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DashboardPage;
