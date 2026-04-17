import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import ConnectionsTable from '../ConnectionsTable';
import { DatabaseConnection } from '../../../types';

// ==================== Mocks ====================
const mockShowSuccess = jest.fn();
const mockShowError = jest.fn();

jest.mock('../../context_providers/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError,
  }),
}));

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    deleteConnection: jest.fn(),
    testConnection: jest.fn(),
  },
}));

import apiService from '../../../utils/api.service';

const mockDeleteConnection = apiService.deleteConnection as jest.Mock;
const mockTestConnection = apiService.testConnection as jest.Mock;

// ==================== Test Data ====================
const mockConnections: DatabaseConnection[] = [
  {
    id: 'conn-1',
    userId: 'user-1',
    name: 'Production DB',
    dbType: 'postgresql',
    host: 'db.example.com',
    port: 5432,
    databaseName: 'prod_db',
    username: 'admin',
    sslEnabled: true,
    schemaName: 'public',
    status: 'connected',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: 'conn-2',
    userId: 'user-1',
    name: 'Staging DB',
    dbType: 'mysql',
    host: 'staging.example.com',
    port: 3306,
    databaseName: 'staging_db',
    username: 'dev',
    sslEnabled: false,
    schemaName: 'main',
    status: 'failed',
    createdAt: '2024-01-16T10:00:00Z',
    updatedAt: '2024-01-16T10:00:00Z',
  },
  {
    id: 'conn-3',
    userId: 'user-1',
    name: 'Dev DB',
    dbType: 'sqlite',
    host: 'localhost',
    databaseName: 'dev_db',
    sslEnabled: false,
    schemaName: 'public',
    status: 'untested',
    createdAt: '2024-01-17T10:00:00Z',
    updatedAt: '2024-01-17T10:00:00Z',
  },
];

// ==================== Helpers ====================
const defaultProps = {
  connections: mockConnections,
  onRefresh: jest.fn(),
  loading: false,
  onEdit: jest.fn(),
};

const renderTable = (overrides: Partial<typeof defaultProps> = {}) =>
  render(<ConnectionsTable {...defaultProps} {...overrides} />);

/**
 * MUI Tooltip wraps children in a <span aria-label="..."> but the actual
 * <button> is nested inside that span. We need to find the button within
 * the tooltip wrapper to trigger click handlers correctly.
 */
const getActionButtons = (label: string): HTMLElement[] => {
  const tooltipSpans = screen.getAllByLabelText(label);
  return tooltipSpans.map((span) => {
    const button = within(span).getByRole('button');
    return button;
  });
};

// ==================== Tests ====================
beforeEach(() => {
  jest.clearAllMocks();
});

describe('ConnectionsTable', () => {
  describe('empty state', () => {
    it('renders empty state when no connections', () => {
      renderTable({ connections: [] });

      expect(screen.getByText('No database connections')).toBeInTheDocument();
      expect(
        screen.getByText('Add a database connection to start querying your data.')
      ).toBeInTheDocument();
    });
  });

  describe('rendering', () => {
    it('renders connections table with data', () => {
      renderTable();

      // Table headers
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Host')).toBeInTheDocument();
      expect(screen.getByText('Database')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();

      // Connection names
      expect(screen.getByText('Production DB')).toBeInTheDocument();
      expect(screen.getByText('Staging DB')).toBeInTheDocument();
      expect(screen.getByText('Dev DB')).toBeInTheDocument();

      // DB types (uppercased)
      expect(screen.getByText('POSTGRESQL')).toBeInTheDocument();
      expect(screen.getByText('MYSQL')).toBeInTheDocument();
      expect(screen.getByText('SQLITE')).toBeInTheDocument();

      // Database names
      expect(screen.getByText('prod_db')).toBeInTheDocument();
      expect(screen.getByText('staging_db')).toBeInTheDocument();
      expect(screen.getByText('dev_db')).toBeInTheDocument();
    });
  });

  describe('status chips', () => {
    it('shows correct status chips (connected=green, failed=red, untested=gray)', () => {
      renderTable();

      const connectedChip = screen.getByText('Connected');
      expect(connectedChip).toBeInTheDocument();
      expect(connectedChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorSuccess');

      const failedChip = screen.getByText('Failed');
      expect(failedChip).toBeInTheDocument();
      expect(failedChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorError');

      const untestedChip = screen.getByText('Untested');
      expect(untestedChip).toBeInTheDocument();
      expect(untestedChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorDefault');
    });
  });

  describe('edit action', () => {
    it('calls onEdit when edit button clicked', () => {
      const mockOnEdit = jest.fn();
      renderTable({ onEdit: mockOnEdit });

      const editButtons = getActionButtons('Edit connection');
      expect(editButtons).toHaveLength(3);

      fireEvent.click(editButtons[0]);
      expect(mockOnEdit).toHaveBeenCalledWith(mockConnections[0]);
    });
  });

  describe('delete action', () => {
    it('calls apiService.deleteConnection when delete confirmed', async () => {
      mockDeleteConnection.mockResolvedValue({ success: true });
      const mockOnRefresh = jest.fn();
      renderTable({ onRefresh: mockOnRefresh });

      const deleteButtons = getActionButtons('Delete connection');
      fireEvent.click(deleteButtons[0]);

      // Confirmation dialog should appear
      expect(screen.getByText('Delete Connection')).toBeInTheDocument();
      // "Production DB" appears in both the table row and the dialog
      expect(screen.getAllByText(/Production DB/)).toHaveLength(2);

      // Click the confirm Delete button in dialog
      const confirmButton = screen.getByRole('button', { name: 'Delete' });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteConnection).toHaveBeenCalledWith('conn-1');
      });

      await waitFor(() => {
        expect(mockShowSuccess).toHaveBeenCalledWith(
          'Connection "Production DB" deleted successfully'
        );
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });
  });

  describe('test action', () => {
    it('calls apiService.testConnection when test button clicked', async () => {
      mockTestConnection.mockResolvedValue({
        data: { status: 'connected' },
      });
      const mockOnRefresh = jest.fn();
      renderTable({ onRefresh: mockOnRefresh });

      const testButtons = getActionButtons('Test connection');
      fireEvent.click(testButtons[0]);

      await waitFor(() => {
        expect(mockTestConnection).toHaveBeenCalledWith('conn-1');
      });

      await waitFor(() => {
        expect(mockShowSuccess).toHaveBeenCalledWith('Connection test successful');
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });

    it('shows error notification when test connection fails', async () => {
      mockTestConnection.mockResolvedValue({
        data: { status: 'failed', error: 'Connection refused' },
      });
      renderTable();

      const testButtons = getActionButtons('Test connection');
      fireEvent.click(testButtons[0]);

      await waitFor(() => {
        expect(mockShowError).toHaveBeenCalledWith(
          'Connection test failed: Connection refused'
        );
      });
    });
  });

  describe('loading state', () => {
    it('shows loading state', () => {
      renderTable({ connections: [], loading: true });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByText('No database connections')).not.toBeInTheDocument();
    });

    it('does not show loading spinner when connections are already loaded', () => {
      renderTable({ loading: true });

      // Table should render normally since connections array is not empty
      expect(screen.getByText('Production DB')).toBeInTheDocument();
    });
  });
});
