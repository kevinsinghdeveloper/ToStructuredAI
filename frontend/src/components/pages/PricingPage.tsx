import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Container, Grid, Card, CardContent, CardActions,
  Button, Switch, FormControlLabel, Chip, CircularProgress, Divider,
  useTheme, useMediaQuery, alpha,
} from '@mui/material';
import { CheckCircle as CheckIcon, Star as StarIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../../utils/api.service';
import { PlanDetails, PlanTier } from '../../types';

export const DEFAULT_PLANS: PlanDetails[] = [
  {
    id: 'free',
    name: 'Free',
    tier: 'free',
    priceMonthly: 0,
    priceYearly: 0,
    maxMembers: 1,
    maxProjects: 2,
    features: [
      '1 team member',
      '2 projects',
      'Basic time tracking',
      'Manual time entries',
      'Personal dashboard',
    ],
    isActive: true,
  },
  {
    id: 'starter',
    name: 'Starter',
    tier: 'starter',
    priceMonthly: 12,
    priceYearly: 115,
    maxMembers: 5,
    maxProjects: 10,
    features: [
      'Up to 5 team members',
      '10 projects',
      'Timer & manual tracking',
      'Weekly timesheets',
      'Basic reports',
      'Client management',
      'Email support',
    ],
    isActive: true,
  },
  {
    id: 'professional',
    name: 'Professional',
    tier: 'professional',
    priceMonthly: 29,
    priceYearly: 278,
    maxMembers: 0,
    maxProjects: 0,
    features: [
      'Unlimited team members',
      'Unlimited projects',
      'Timer & manual tracking',
      'Weekly timesheets with approval',
      'Advanced reports & analytics',
      'Client management',
      'Budget tracking',
      'AI time assistant',
      'Narrative presets',
      'Export to CSV/PDF',
      'Priority email support',
    ],
    isActive: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tier: 'enterprise',
    priceMonthly: 79,
    priceYearly: 758,
    maxMembers: 0,
    maxProjects: 0,
    features: [
      'Everything in Professional',
      'Unlimited everything',
      'Custom integrations',
      'SSO / SAML authentication',
      'Advanced security controls',
      'Dedicated account manager',
      'Custom onboarding',
      'SLA guarantee',
      'Priority support',
      'API access',
    ],
    isActive: true,
  },
];

const TIER_ORDER: PlanTier[] = ['free', 'starter', 'professional', 'enterprise'];

const PricingPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [plans, setPlans] = useState<PlanDetails[]>([]);
  const [isYearly, setIsYearly] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    // Only fetch from API if authenticated; otherwise use defaults
    if (!localStorage.getItem('authToken')) {
      setPlans(DEFAULT_PLANS);
      setLoading(false);
      return;
    }
    try {
      const res = await apiService.getPlans();
      const fetched: PlanDetails[] = res?.data?.plans || res?.plans || [];
      if (fetched.length > 0) {
        const sorted = [...fetched].sort(
          (a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier)
        );
        setPlans(sorted);
      } else {
        setPlans(DEFAULT_PLANS);
      }
    } catch {
      setPlans(DEFAULT_PLANS);
    } finally {
      setLoading(false);
    }
  };

  const getPrice = (plan: PlanDetails): string => {
    const price = isYearly ? plan.priceYearly : plan.priceMonthly;
    if (price === 0) return '0';
    if (isYearly) {
      const monthly = price / 12;
      return monthly.toFixed(0);
    }
    return price.toFixed(0);
  };

  const getAnnualTotal = (plan: PlanDetails): string => {
    return plan.priceYearly.toFixed(0);
  };

  const getSavingsPercent = (plan: PlanDetails): number => {
    if (plan.priceMonthly === 0) return 0;
    const yearlyIfMonthly = plan.priceMonthly * 12;
    const savings = ((yearlyIfMonthly - plan.priceYearly) / yearlyIfMonthly) * 100;
    return Math.round(savings);
  };

  const handleCTA = (plan: PlanDetails) => {
    if (plan.tier === 'enterprise') {
      window.location.href = 'mailto:sales@zerve.app?subject=Enterprise%20Plan%20Inquiry&body=I%20am%20interested%20in%20the%20Zerve%20My%20Time%20Enterprise%20plan.';
      return;
    }
    if (plan.tier === 'free') {
      navigate('/register');
    } else {
      const params = new URLSearchParams();
      params.set('plan', plan.tier);
      params.set('billing', isYearly ? 'yearly' : 'monthly');
      navigate(`/register?${params.toString()}`);
    }
  };

  const getCTALabel = (plan: PlanDetails): string => {
    if (plan.tier === 'free') return 'Get Started';
    if (plan.tier === 'enterprise') return 'Contact Sales';
    return 'Start Free Trial';
  };

  const isPopular = (tier: PlanTier): boolean => tier === 'professional';

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', pt: { xs: 4, md: 8 }, pb: 8 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 6 } }}>
          <Typography
            variant="h2"
            fontWeight={700}
            sx={{
              mb: 2,
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Simple, transparent pricing
          </Typography>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 600, mx: 'auto', mb: 4, fontWeight: 400 }}
          >
            Choose the plan that fits your team. Start free, upgrade when you need more.
          </Typography>

          {/* Monthly/Yearly Toggle */}
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1.5,
              bgcolor: alpha(theme.palette.primary.main, 0.08),
              borderRadius: 3,
              px: 3,
              py: 1,
            }}
          >
            <Typography
              variant="body1"
              fontWeight={isYearly ? 400 : 600}
              color={isYearly ? 'text.secondary' : 'text.primary'}
            >
              Monthly
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={isYearly}
                  onChange={(e) => setIsYearly(e.target.checked)}
                  color="primary"
                />
              }
              label=""
              sx={{ mx: 0 }}
            />
            <Typography
              variant="body1"
              fontWeight={isYearly ? 600 : 400}
              color={isYearly ? 'text.primary' : 'text.secondary'}
            >
              Yearly
            </Typography>
            {isYearly && (
              <Chip
                label="Save ~20%"
                size="small"
                color="secondary"
                sx={{ fontWeight: 600, ml: 0.5 }}
              />
            )}
          </Box>
        </Box>

        {/* Plan Cards */}
        <Grid container spacing={3} justifyContent="center">
          {plans.map((plan) => {
            const popular = isPopular(plan.tier);
            const savings = getSavingsPercent(plan);

            return (
              <Grid
                item
                xs={12}
                sm={6}
                lg={3}
                key={plan.id}
              >
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    borderColor: popular ? theme.palette.primary.main : 'divider',
                    borderWidth: popular ? 2 : 1,
                    borderStyle: 'solid',
                    transform: popular && !isMobile ? 'scale(1.04)' : 'none',
                    zIndex: popular ? 1 : 0,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: popular && !isMobile ? 'scale(1.06)' : 'translateY(-4px)',
                      boxShadow: popular
                        ? `0 12px 40px ${alpha(theme.palette.primary.main, 0.3)}`
                        : '0 8px 32px rgba(0, 0, 0, 0.2)',
                    },
                  }}
                >
                  {/* Popular Badge */}
                  {popular && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -1,
                        left: 0,
                        right: 0,
                        bgcolor: theme.palette.primary.main,
                        color: '#fff',
                        textAlign: 'center',
                        py: 0.5,
                        borderTopLeftRadius: 16,
                        borderTopRightRadius: 16,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 0.5,
                      }}
                    >
                      <StarIcon sx={{ fontSize: 16 }} />
                      <Typography variant="caption" fontWeight={700} letterSpacing={1} textTransform="uppercase">
                        Most Popular
                      </Typography>
                    </Box>
                  )}

                  <CardContent
                    sx={{
                      flexGrow: 1,
                      pt: popular ? 5 : 3,
                      px: 3,
                      pb: 2,
                    }}
                  >
                    {/* Plan Name */}
                    <Typography variant="h5" fontWeight={700} gutterBottom>
                      {plan.name}
                    </Typography>

                    {/* Price */}
                    <Box sx={{ mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
                        <Typography variant="h3" fontWeight={800} sx={{ lineHeight: 1 }}>
                          ${getPrice(plan)}
                        </Typography>
                        {plan.priceMonthly > 0 && (
                          <Typography variant="body1" color="text.secondary">
                            /mo
                          </Typography>
                        )}
                      </Box>
                      {isYearly && plan.priceYearly > 0 && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          ${getAnnualTotal(plan)} billed annually
                        </Typography>
                      )}
                      {isYearly && savings > 0 && (
                        <Typography
                          variant="body2"
                          sx={{ color: theme.palette.secondary.main, fontWeight: 600, mt: 0.25 }}
                        >
                          Save {savings}% vs monthly
                        </Typography>
                      )}
                      {plan.priceMonthly === 0 && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          Free forever
                        </Typography>
                      )}
                    </Box>

                    {/* Members / Projects */}
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {plan.maxMembers === 0 ? 'Unlimited' : `Up to ${plan.maxMembers}`} members
                      {' / '}
                      {plan.maxProjects === 0 ? 'unlimited' : plan.maxProjects} projects
                    </Typography>

                    <Divider sx={{ my: 2 }} />

                    {/* Features */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {(plan.features || []).map((feature, i) => (
                        <Box key={i} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <CheckIcon
                            sx={{
                              fontSize: 18,
                              color: theme.palette.secondary.main,
                              mt: 0.2,
                              flexShrink: 0,
                            }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {feature}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>

                  <CardActions sx={{ p: 3, pt: 1 }}>
                    <Button
                      fullWidth
                      variant={popular ? 'contained' : 'outlined'}
                      size="large"
                      onClick={() => handleCTA(plan)}
                      sx={{
                        py: 1.5,
                        fontWeight: 700,
                        ...(popular && {
                          background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark || theme.palette.primary.main})`,
                          '&:hover': {
                            background: `linear-gradient(135deg, ${theme.palette.primary.light || theme.palette.primary.main}, ${theme.palette.primary.main})`,
                          },
                        }),
                      }}
                    >
                      {getCTALabel(plan)}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* FAQ / Bottom CTA */}
        <Box sx={{ textAlign: 'center', mt: { xs: 6, md: 8 } }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Need a custom plan for your organization?
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
            We offer custom Enterprise plans with dedicated support, SLAs, and custom integrations
            tailored to your needs.
          </Typography>
          <Button
            variant="outlined"
            size="large"
            onClick={() => {
              window.location.href = 'mailto:sales@zerve.app?subject=Custom%20Enterprise%20Plan%20Inquiry&body=I%20am%20interested%20in%20a%20custom%20Zerve%20My%20Time%20Enterprise%20plan.';
            }}
          >
            Contact Sales
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default PricingPage;
