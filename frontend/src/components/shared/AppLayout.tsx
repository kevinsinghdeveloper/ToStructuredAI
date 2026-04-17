import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton, Avatar, Badge, Tooltip,
  Divider, useMediaQuery, useTheme, Menu, MenuItem,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DescriptionIcon,
  SmartToy as SmartToyIcon,
  AccountTree as AccountTreeIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Business as BusinessIcon,
  Notifications as NotificationsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
  Menu as MenuIcon,
} from '@mui/icons-material';
import NotificationPanel from './NotificationPanel';
import { useBrowserTitle } from '../../hooks/useBrowserTitle';
import { useAuth } from '../context_providers/AuthContext';
import { useOrganization } from '../context_providers/OrganizationContext';
import apiService from '../../utils/api.service';

const DRAWER_WIDTH = 240;

const mainNavItems = [
  { label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { label: 'Documents', icon: <DescriptionIcon />, path: '/documents' },
  { label: 'Models', icon: <SmartToyIcon />, path: '/models' },
  { label: 'Pipelines', icon: <AccountTreeIcon />, path: '/pipelines' },
  { label: 'Outputs', icon: <DownloadIcon />, path: '/outputs' },
];

const bottomNavItems = [
  { label: 'Organizations', icon: <BusinessIcon />, path: '/organizations' },
  { label: 'Org Settings', icon: <BusinessIcon />, path: '/org/settings' },
  { label: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const AppLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileAnchor, setProfileAnchor] = useState<null | HTMLElement>(null);
  const [notifAnchor, setNotifAnchor] = useState<null | HTMLElement>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, logout } = useAuth();
  const { organizations } = useOrganization();
  useBrowserTitle();

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await apiService.getUnreadNotificationCount();
      const data = res.data || res;
      setUnreadCount(typeof data === 'number' ? data : (data?.count ?? 0));
    } catch {
      // Non-critical
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  const userInitials = [user?.firstName?.[0], user?.lastName?.[0]].filter(Boolean).join('').toUpperCase() || '?';

  const handleLogout = () => {
    setProfileAnchor(null);
    logout();
    navigate('/login');
  };

  const isSuperAdmin = !!user?.isSuperAdmin;
  const showOrganizations = isSuperAdmin || organizations.length > 1;

  const filteredBottomItems = bottomNavItems.filter((item) => {
    if (item.path === '/organizations') return showOrganizations;
    if (item.path === '/org/settings') return !!user?.orgId || organizations.length > 0;
    return true;
  });

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ justifyContent: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>
          ToStructured AI
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ flex: 1 }}>
        {mainNavItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
            onClick={() => { navigate(item.path); if (isMobile) setMobileOpen(false); }}
            sx={{ borderRadius: 1, mx: 1, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <Divider />
      <List>
        {filteredBottomItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
            onClick={() => { navigate(item.path); if (isMobile) setMobileOpen(false); }}
            sx={{ borderRadius: 1, mx: 1, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Top bar */}
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          {isMobile && (
            <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ mr: 2 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" noWrap sx={{ flexGrow: 1, fontWeight: 700 }}>
            ToStructured AI
          </Typography>
          <Tooltip title="Notifications">
            <IconButton color="inherit" onClick={(e) => setNotifAnchor(e.currentTarget)}>
              <Badge badgeContent={unreadCount} color="error"><NotificationsIcon /></Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Profile">
            <IconButton sx={{ ml: 1 }} onClick={(e) => setProfileAnchor(e.currentTarget)}>
              <Avatar sx={{ width: 32, height: 32, fontSize: 14, bgcolor: 'primary.main' }}>{userInitials}</Avatar>
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={profileAnchor}
            open={Boolean(profileAnchor)}
            onClose={() => setProfileAnchor(null)}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            slotProps={{ paper: { sx: { minWidth: 220, mt: 1 } } }}
          >
            <MenuItem disabled sx={{ opacity: '1 !important', flexDirection: 'column', alignItems: 'flex-start', py: 1.5 }}>
              <Typography variant="subtitle2">{user?.firstName} {user?.lastName}</Typography>
              <Typography variant="caption" color="text.secondary">{user?.email}</Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { setProfileAnchor(null); navigate('/settings'); }}>
              <ListItemIcon><PersonIcon fontSize="small" /></ListItemIcon>
              Profile
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      {isMobile ? (
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}>
          {drawer}
        </Drawer>
      ) : (
        <Drawer variant="permanent"
          sx={{ width: DRAWER_WIDTH, flexShrink: 0, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}>
          {drawer}
        </Drawer>
      )}

      {/* Main content */}
      <Box component="main" sx={{ flexGrow: 1, pt: 8, minHeight: '100vh' }}>
        <Outlet />
      </Box>

      {/* Notification Panel */}
      <NotificationPanel
        anchorEl={notifAnchor}
        onClose={() => setNotifAnchor(null)}
        onCountChange={setUnreadCount}
      />
    </Box>
  );
};

export default AppLayout;
