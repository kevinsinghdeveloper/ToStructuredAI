import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Container, Stepper, Step, StepLabel, TextField, Button,
  Paper, Grid, Card, CardContent, IconButton, Select, MenuItem,
  FormControl, InputLabel, CircularProgress, Divider,
} from '@mui/material';
import {
  Business as OrgIcon, Group as TeamIcon, CreditCard as PlanIcon,
  CheckCircle as DoneIcon, Add as AddIcon, Delete as DeleteIcon,
  ArrowForward as NextIcon, ArrowBack as BackIcon,
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useNotification } from '../context_providers/NotificationContext';
import { useOrganization } from '../context_providers/OrganizationContext';
import apiService from '../../utils/api.service';
import { OrgRole, PlanDetails, PlanTier } from '../../types';
import { DEFAULT_PLANS } from './PricingPage';

const STEPS = ['Create Organization', 'Invite Team', 'Choose Plan', 'Complete'];

interface InviteRow {
  email: string;
  role: OrgRole;
}

const OrgSetupWizard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedTier = searchParams.get('plan') as PlanTier | null;
  const preselectedBilling = searchParams.get('billing') || 'monthly';
  const { showSuccess, showError } = useNotification();
  const { fetchOrganization, sendInvitation } = useOrganization();

  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Step 1: Create Org
  const [orgName, setOrgName] = useState('');
  const [slugPreview, setSlugPreview] = useState('');

  // Step 2: Invite Team
  const [invites, setInvites] = useState<InviteRow[]>([{ email: '', role: 'member' }]);

  // Step 3: Choose Plan
  const [plans, setPlans] = useState<PlanDetails[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [plansLoading, setPlansLoading] = useState(false);

  // Track created org for subsequent steps
  const [, setCreatedOrgId] = useState<string | null>(null);

  useEffect(() => {
    const slug = orgName
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .slice(0, 50);
    setSlugPreview(slug);
  }, [orgName]);

  const loadPlans = async () => {
    setPlansLoading(true);
    try {
      const res = await apiService.getPlans();
      const fetched: PlanDetails[] = res?.data?.plans || res?.plans || res?.data || [];
      const data = Array.isArray(fetched) && fetched.length > 0 ? fetched : DEFAULT_PLANS;
      setPlans(data);
      // Pre-select plan from URL params, or default to free
      const targetTier = preselectedTier || 'free';
      const matchingPlan = data.find((p: PlanDetails) => p.tier === targetTier);
      if (matchingPlan) {
        setSelectedPlan(matchingPlan.id);
      } else {
        const freePlan = data.find((p: PlanDetails) => p.tier === 'free');
        if (freePlan) setSelectedPlan(freePlan.id);
      }
    } catch {
      setPlans(DEFAULT_PLANS);
      const targetTier = preselectedTier || 'free';
      const fallback = DEFAULT_PLANS.find((p) => p.tier === targetTier) || DEFAULT_PLANS[0];
      if (fallback) setSelectedPlan(fallback.id);
    } finally {
      setPlansLoading(false);
    }
  };

  const handleCreateOrg = async () => {
    if (!orgName.trim()) return;
    setLoading(true);
    try {
      const res = await apiService.createOrg({ name: orgName.trim() });
      const org = res.data || res;
      setCreatedOrgId(org.id);
      if (org.id) localStorage.setItem('currentOrgId', org.id);
      await fetchOrganization();
      setActiveStep(1);
    } catch (err: any) {
      showError(err.message || 'Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteTeam = async () => {
    const validInvites = invites.filter((i) => i.email.trim());
    if (validInvites.length === 0) {
      setActiveStep(2);
      loadPlans();
      return;
    }
    setLoading(true);
    let successCount = 0;
    for (const invite of validInvites) {
      try {
        await sendInvitation(invite.email.trim(), invite.role);
        successCount++;
      } catch {
        // Continue sending remaining invitations
      }
    }
    if (successCount > 0) {
      showSuccess(`${successCount} invitation${successCount > 1 ? 's' : ''} sent`);
    }
    setLoading(false);
    setActiveStep(2);
    loadPlans();
  };

  const handleChoosePlan = async () => {
    const plan = plans.find((p) => p.id === selectedPlan);
    if (plan && plan.tier !== 'free' && plan.stripePriceId) {
      setLoading(true);
      try {
        const res = await apiService.createCheckout(
          plan.stripePriceId,
          `${window.location.origin}/dashboard?setup=complete`,
          `${window.location.origin}/setup?step=plan`
        );
        const url = res.data?.url || res.url;
        if (url) {
          window.location.href = url;
          return;
        }
      } catch (err: any) {
        showError(err.message || 'Failed to start checkout');
      } finally {
        setLoading(false);
      }
    }
    setActiveStep(3);
  };

  const addInviteRow = () => {
    setInvites([...invites, { email: '', role: 'member' }]);
  };

  const updateInviteRow = (index: number, field: keyof InviteRow, value: string) => {
    const updated = [...invites];
    (updated[index] as any)[field] = value;
    setInvites(updated);
  };

  const removeInviteRow = (index: number) => {
    if (invites.length <= 1) return;
    setInvites(invites.filter((_, i) => i !== index));
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, py: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <OrgIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" fontWeight={600}>Name Your Organization</Typography>
              <Typography color="text.secondary">
                This is your team's workspace for document processing.
              </Typography>
            </Box>
            <TextField
              label="Organization Name"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              fullWidth
              autoFocus
              placeholder="Acme Corporation"
            />
            {slugPreview && (
              <Typography variant="body2" color="text.secondary">
                Your workspace URL: <strong>tostructured.ai/{slugPreview}</strong>
              </Typography>
            )}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                endIcon={loading ? <CircularProgress size={18} /> : <NextIcon />}
                onClick={handleCreateOrg}
                disabled={loading || !orgName.trim()}
                size="large"
              >
                Create Organization
              </Button>
            </Box>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, py: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <TeamIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" fontWeight={600}>Invite Your Team</Typography>
              <Typography color="text.secondary">
                Add team members by email. You can always invite more later.
              </Typography>
            </Box>

            {invites.map((invite, index) => (
              <Box key={index} sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <TextField
                  label="Email"
                  value={invite.email}
                  onChange={(e) => updateInviteRow(index, 'email', e.target.value)}
                  fullWidth
                  placeholder="colleague@company.com"
                  size="small"
                />
                <FormControl sx={{ minWidth: 130 }} size="small">
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={invite.role}
                    label="Role"
                    onChange={(e) => updateInviteRow(index, 'role', e.target.value)}
                  >
                    <MenuItem value="member">Member</MenuItem>
                    <MenuItem value="manager">Manager</MenuItem>
                    <MenuItem value="admin">Admin</MenuItem>
                  </Select>
                </FormControl>
                <IconButton
                  onClick={() => removeInviteRow(index)}
                  disabled={invites.length <= 1}
                  size="small"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            ))}

            <Button startIcon={<AddIcon />} onClick={addInviteRow} variant="text" sx={{ alignSelf: 'flex-start' }}>
              Add Another
            </Button>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="text"
                onClick={() => { setActiveStep(2); loadPlans(); }}
              >
                Skip for Now
              </Button>
              <Button
                variant="contained"
                endIcon={loading ? <CircularProgress size={18} /> : <NextIcon />}
                onClick={handleInviteTeam}
                disabled={loading}
                size="large"
              >
                Send Invitations
              </Button>
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, py: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <PlanIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" fontWeight={600}>Choose Your Plan</Typography>
              <Typography color="text.secondary">
                Start free and upgrade as your team grows.
              </Typography>
            </Box>

            {plansLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Grid container spacing={2}>
                {plans.map((plan) => {
                  const isSelected = selectedPlan === plan.id;
                  return (
                    <Grid item xs={12} sm={6} md={3} key={plan.id}>
                      <Card
                        variant="outlined"
                        sx={{
                          cursor: 'pointer',
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          borderColor: isSelected ? 'primary.main' : 'divider',
                          borderWidth: isSelected ? 2 : 1,
                          transition: 'border-color 0.2s',
                          '&:hover': { borderColor: 'primary.light' },
                        }}
                        onClick={() => setSelectedPlan(plan.id)}
                      >
                        <CardContent sx={{ flexGrow: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="h6" fontWeight={700}>{plan.name}</Typography>
                            {isSelected && <DoneIcon color="primary" fontSize="small" />}
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {plan.priceMonthly === 0
                              ? 'Free'
                              : preselectedBilling === 'yearly' && plan.priceYearly > 0
                                ? `$${Math.round(plan.priceYearly / 12)}`
                                : `$${plan.priceMonthly}`}
                            {plan.priceMonthly > 0 && (
                              <Typography component="span" variant="body2" color="text.secondary">/mo</Typography>
                            )}
                          </Typography>
                          {preselectedBilling === 'yearly' && plan.priceYearly > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              ${plan.priceYearly}/year
                            </Typography>
                          )}
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
                            Up to {plan.maxMembers === -1 ? 'unlimited' : plan.maxMembers} members
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          {plan.features.slice(0, 5).map((f, i) => (
                            <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                              <DoneIcon sx={{ fontSize: 14, color: 'success.main' }} />
                              <Typography variant="caption">{f}</Typography>
                            </Box>
                          ))}
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button startIcon={<BackIcon />} onClick={() => setActiveStep(1)}>
                Back
              </Button>
              <Button
                variant="contained"
                endIcon={loading ? <CircularProgress size={18} /> : <NextIcon />}
                onClick={handleChoosePlan}
                disabled={loading || !selectedPlan}
                size="large"
              >
                Continue
              </Button>
            </Box>
          </Box>
        );

      case 3:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, py: 4 }}>
            <DoneIcon sx={{ fontSize: 64, color: 'success.main' }} />
            <Typography variant="h4" fontWeight={700}>You're All Set!</Typography>
            <Typography color="text.secondary" textAlign="center" sx={{ maxWidth: 400 }}>
              Your organization is ready. Start processing documents, set up pipelines, and invite more team members from the settings.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/dashboard')}
              endIcon={<NextIcon />}
            >
              Go to Dashboard
            </Button>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper sx={{ p: 4, borderRadius: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent()}
      </Paper>
    </Container>
  );
};

export default OrgSetupWizard;
