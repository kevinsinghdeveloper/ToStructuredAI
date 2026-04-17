import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Tabs, Tab, TextField, Button, Paper, Select, MenuItem,
  FormControl, InputLabel, Switch, FormControlLabel, Grid, Card, CardContent,
  CardActions, Chip, Divider, CircularProgress, InputAdornment,
} from '@mui/material';
import {
  Business as BusinessIcon, Schedule as ScheduleIcon,
  CreditCard as CreditCardIcon, CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useOrganization } from '../context_providers/OrganizationContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';
import { OrgSettings, PlanDetails, PlanTier } from '../../types';

const COMMON_TIMEZONES = [
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'America/Phoenix', 'America/Anchorage', 'Pacific/Honolulu', 'America/Toronto',
  'America/Vancouver', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney',
  'Pacific/Auckland', 'UTC',
];

const ROUNDING_OPTIONS = [
  { value: 1, label: '1 minute' },
  { value: 5, label: '5 minutes' },
  { value: 6, label: '6 minutes (1/10 hr)' },
  { value: 10, label: '10 minutes' },
  { value: 15, label: '15 minutes (1/4 hr)' },
  { value: 30, label: '30 minutes (1/2 hr)' },
];

const TIER_LABELS: Record<PlanTier, string> = {
  free: 'Free', starter: 'Starter', professional: 'Professional', enterprise: 'Enterprise',
};

interface TabPanelProps {
  children: React.ReactNode;
  value: number;
  index: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <Box role="tabpanel" hidden={value !== index} sx={{ pt: 3 }}>
    {value === index && children}
  </Box>
);

const OrgSettingsPage: React.FC = () => {
  const { organization, updateOrganization, isLoading: orgLoading } = useOrganization();
  const { showSuccess, showError } = useNotification();
  const [tab, setTab] = useState(0);

  // General tab state
  const [name, setName] = useState('');
  const [logoUrl, setLogoUrl] = useState('');
  const [generalSaving, setGeneralSaving] = useState(false);

  // Time tracking tab state
  const [timezone, setTimezone] = useState('America/New_York');
  const [weekStart, setWeekStart] = useState<'monday' | 'sunday'>('monday');
  const [roundingIncrement, setRoundingIncrement] = useState(15);
  const [requireApproval, setRequireApproval] = useState(false);
  const [defaultBillableRate, setDefaultBillableRate] = useState('');
  const [trackingSaving, setTrackingSaving] = useState(false);

  // Billing tab state
  const [plans, setPlans] = useState<PlanDetails[]>([]);
  const [plansLoading, setPlansLoading] = useState(false);
  const [billingLoading, setBillingLoading] = useState(false);

  useEffect(() => {
    if (!organization) return;
    setName(organization.name || '');
    setLogoUrl(organization.logoUrl || '');
    const s = organization.settings;
    if (s) {
      setTimezone(s.timezone || 'America/New_York');
      setWeekStart(s.weekStart || 'monday');
      setRoundingIncrement(s.roundingIncrement || 15);
      setRequireApproval(s.requireApproval ?? false);
      setDefaultBillableRate(s.defaultBillableRate?.toString() || '');
    }
  }, [organization]);

  useEffect(() => {
    if (tab === 2) loadPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const loadPlans = async () => {
    setPlansLoading(true);
    try {
      const res = await apiService.getPlans();
      const fetched = res?.data?.plans || res?.plans || [];
      setPlans(Array.isArray(fetched) ? fetched : []);
    } catch (err: any) {
      showError('Failed to load plans');
    } finally {
      setPlansLoading(false);
    }
  };

  const handleSaveGeneral = async () => {
    setGeneralSaving(true);
    try {
      await updateOrganization({ name, logoUrl: logoUrl || undefined });
      showSuccess('Organization details updated');
    } catch (err: any) {
      showError(err.message || 'Failed to update organization');
    } finally {
      setGeneralSaving(false);
    }
  };

  const handleSaveTracking = async () => {
    setTrackingSaving(true);
    try {
      const settings: OrgSettings = {
        timezone,
        weekStart,
        roundingIncrement,
        requireApproval,
        defaultBillableRate: defaultBillableRate ? parseFloat(defaultBillableRate) : undefined,
      };
      await updateOrganization({ settings } as any);
      showSuccess('Time tracking settings updated');
    } catch (err: any) {
      showError(err.message || 'Failed to update settings');
    } finally {
      setTrackingSaving(false);
    }
  };

  const handleUpgrade = async (plan: PlanDetails) => {
    if (!plan.stripePriceId) return;
    setBillingLoading(true);
    try {
      const res = await apiService.createCheckout(
        plan.stripePriceId,
        `${window.location.origin}/settings/org?billing=success`,
        `${window.location.origin}/settings/org?billing=cancel`
      );
      const url = res?.data?.checkoutUrl || res?.data?.url || res?.checkoutUrl || res?.url;
      if (url) window.location.href = url;
      else showError('No checkout URL returned');
    } catch (err: any) {
      showError(err.message || 'Failed to start checkout');
    } finally {
      setBillingLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setBillingLoading(true);
    try {
      const res = await apiService.createBillingPortal(`${window.location.origin}/settings/org`);
      const url = res?.data?.portalUrl || res?.data?.url || res?.portalUrl || res?.url;
      if (url) window.location.href = url;
      else showError('No billing portal URL returned');
    } catch (err: any) {
      showError(err.message || 'Failed to open billing portal');
    } finally {
      setBillingLoading(false);
    }
  };

  if (orgLoading && !organization) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const currentTier = organization?.planTier || 'free';

  return (
    <Box sx={{ p: 3, maxWidth: 900, mx: 'auto' }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Organization Settings
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Manage your organization details, time tracking preferences, and billing.
      </Typography>

      <Paper sx={{ borderRadius: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tab icon={<BusinessIcon />} iconPosition="start" label="General" />
          <Tab icon={<ScheduleIcon />} iconPosition="start" label="Time Tracking" />
          <Tab icon={<CreditCardIcon />} iconPosition="start" label="Billing" />
        </Tabs>

        {/* General Tab */}
        <TabPanel value={tab} index={0}>
          <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Organization Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
            />
            <TextField
              label="Slug"
              value={organization?.slug || ''}
              fullWidth
              disabled
              helperText="The organization slug cannot be changed"
            />
            <TextField
              label="Logo URL"
              value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              fullWidth
              placeholder="https://example.com/logo.png"
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleSaveGeneral}
                disabled={generalSaving || !name.trim()}
              >
                {generalSaving ? <CircularProgress size={20} /> : 'Save Changes'}
              </Button>
            </Box>
          </Box>
        </TabPanel>

        {/* Time Tracking Tab */}
        <TabPanel value={tab} index={1}>
          <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Timezone</InputLabel>
              <Select value={timezone} label="Timezone" onChange={(e) => setTimezone(e.target.value)}>
                {COMMON_TIMEZONES.map((tz) => (
                  <MenuItem key={tz} value={tz}>{tz.replace(/_/g, ' ')}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Week Starts On</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant={weekStart === 'monday' ? 'contained' : 'outlined'}
                  onClick={() => setWeekStart('monday')}
                  size="small"
                >
                  Monday
                </Button>
                <Button
                  variant={weekStart === 'sunday' ? 'contained' : 'outlined'}
                  onClick={() => setWeekStart('sunday')}
                  size="small"
                >
                  Sunday
                </Button>
              </Box>
            </Box>

            <FormControl fullWidth>
              <InputLabel>Rounding Increment</InputLabel>
              <Select
                value={roundingIncrement}
                label="Rounding Increment"
                onChange={(e) => setRoundingIncrement(Number(e.target.value))}
              >
                {ROUNDING_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch checked={requireApproval} onChange={(e) => setRequireApproval(e.target.checked)} />
              }
              label="Require timesheet approval"
            />

            <TextField
              label="Default Billable Rate"
              value={defaultBillableRate}
              onChange={(e) => setDefaultBillableRate(e.target.value)}
              type="number"
              InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
              sx={{ maxWidth: 300 }}
            />

            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="contained" onClick={handleSaveTracking} disabled={trackingSaving}>
                {trackingSaving ? <CircularProgress size={20} /> : 'Save Settings'}
              </Button>
            </Box>
          </Box>
        </TabPanel>

        {/* Billing Tab */}
        <TabPanel value={tab} index={2}>
          <Box sx={{ p: 3 }}>
            <Box sx={{ mb: 4, p: 3, bgcolor: 'action.hover', borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom>Current Plan</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Chip
                  label={TIER_LABELS[currentTier]}
                  color={currentTier === 'free' ? 'default' : 'primary'}
                  size="medium"
                />
                <Typography variant="body2" color="text.secondary">
                  {organization?.memberCount || 0} member{(organization?.memberCount || 0) !== 1 ? 's' : ''}
                </Typography>
              </Box>
              {currentTier !== 'free' && (
                <Button
                  variant="outlined"
                  onClick={handleManageBilling}
                  disabled={billingLoading}
                  sx={{ mt: 2 }}
                >
                  {billingLoading ? <CircularProgress size={20} /> : 'Manage Billing'}
                </Button>
              )}
            </Box>

            <Divider sx={{ my: 3 }} />
            <Typography variant="h6" gutterBottom>Available Plans</Typography>

            {plansLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Grid container spacing={3}>
                {plans.map((plan) => {
                  const isCurrent = plan.tier === currentTier;
                  return (
                    <Grid item xs={12} sm={6} md={3} key={plan.id}>
                      <Card
                        variant="outlined"
                        sx={{
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          borderColor: isCurrent ? 'primary.main' : 'divider',
                          borderWidth: isCurrent ? 2 : 1,
                        }}
                      >
                        <CardContent sx={{ flexGrow: 1 }}>
                          <Typography variant="h6" fontWeight={700}>{plan.name}</Typography>
                          <Typography variant="h4" fontWeight={700} sx={{ my: 1 }}>
                            ${plan.priceMonthly}
                            <Typography component="span" variant="body2" color="text.secondary">/mo</Typography>
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Up to {plan.maxMembers === 0 || plan.maxMembers === -1 ? 'unlimited' : plan.maxMembers} members
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          {plan.features.map((f, i) => (
                            <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                              <CheckIcon sx={{ fontSize: 16, color: 'success.main' }} />
                              <Typography variant="body2">{f}</Typography>
                            </Box>
                          ))}
                        </CardContent>
                        <CardActions sx={{ p: 2, pt: 0 }}>
                          {isCurrent ? (
                            <Button fullWidth variant="outlined" disabled>Current Plan</Button>
                          ) : (
                            <Button
                              fullWidth
                              variant="contained"
                              onClick={() => handleUpgrade(plan)}
                              disabled={billingLoading || !plan.stripePriceId}
                            >
                              {plan.priceMonthly === 0 ? 'Downgrade' : 'Upgrade'}
                            </Button>
                          )}
                        </CardActions>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default OrgSettingsPage;
