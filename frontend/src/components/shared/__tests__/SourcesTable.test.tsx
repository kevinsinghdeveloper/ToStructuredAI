import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import SourcesTable from '../SourcesTable';
import { Source } from '../../../types';

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
    deleteSource: jest.fn(),
  },
}));

import apiService from '../../../utils/api.service';

const mockDeleteSource = apiService.deleteSource as jest.Mock;

// ==================== Test Data ====================
const mockSources: Source[] = [
  {
    id: 'src-1',
    userId: 'user-1',
    name: 'Invoice PDF',
    sourceType: 'document',
    isQueryable: false,
    status: 'ready',
    documentId: 'doc-1',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: 'src-2',
    userId: 'user-1',
    name: 'Customers Table',
    sourceType: 'database',
    isQueryable: true,
    status: 'metadata_extracted',
    connectionId: 'conn-1',
    tableName: 'customers',
    createdAt: '2024-01-16T10:00:00Z',
    updatedAt: '2024-01-16T10:00:00Z',
  },
  {
    id: 'src-3',
    userId: 'user-1',
    name: 'Orders Table',
    sourceType: 'database',
    isQueryable: true,
    status: 'pending',
    connectionId: 'conn-1',
    tableName: 'orders',
    createdAt: '2024-01-17T10:00:00Z',
    updatedAt: '2024-01-17T10:00:00Z',
  },
  {
    id: 'src-4',
    userId: 'user-1',
    name: 'Broken Source',
    sourceType: 'document',
    isQueryable: false,
    status: 'error',
    documentId: 'doc-2',
    createdAt: '2024-01-18T10:00:00Z',
    updatedAt: '2024-01-18T10:00:00Z',
  },
];

// ==================== Helpers ====================
const defaultProps = {
  sources: mockSources,
  onRefresh: jest.fn(),
  loading: false,
};

const renderTable = (overrides: Partial<typeof defaultProps> = {}) =>
  render(<SourcesTable {...defaultProps} {...overrides} />);

/**
 * MUI Tooltip wraps children in a <span aria-label="..."> but the actual
 * <button> is nested inside. Find the button within the tooltip wrapper.
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

describe('SourcesTable', () => {
  describe('empty state', () => {
    it('renders empty state when no sources', () => {
      renderTable({ sources: [] });

      expect(screen.getByText('No sources available')).toBeInTheDocument();
      expect(
        screen.getByText(
          'Upload documents or connect a database to create sources for your pipelines.'
        )
      ).toBeInTheDocument();
    });
  });

  describe('rendering', () => {
    it('renders sources table with data', () => {
      renderTable();

      // Table headers
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Table Name')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();

      // Source names
      expect(screen.getByText('Invoice PDF')).toBeInTheDocument();
      expect(screen.getByText('Customers Table')).toBeInTheDocument();
      expect(screen.getByText('Orders Table')).toBeInTheDocument();
      expect(screen.getByText('Broken Source')).toBeInTheDocument();

      // Table names for database sources
      expect(screen.getByText('customers')).toBeInTheDocument();
      expect(screen.getByText('orders')).toBeInTheDocument();
    });
  });

  describe('type chips', () => {
    it('shows document and database type chips', () => {
      renderTable();

      const documentChips = screen.getAllByText('Document');
      const databaseChips = screen.getAllByText('Database');

      // 2 document sources (src-1, src-4), 2 database sources (src-2, src-3)
      expect(documentChips).toHaveLength(2);
      expect(databaseChips).toHaveLength(2);

      // Document chips use primary color, database chips use secondary
      documentChips.forEach((chip) => {
        expect(chip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorPrimary');
      });

      databaseChips.forEach((chip) => {
        expect(chip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorSecondary');
      });
    });
  });

  describe('queryable badge', () => {
    it('shows queryable badge', () => {
      renderTable();

      // src-2 and src-3 are queryable -- the Search icon has data-testid="SearchIcon"
      const queryableIcons = screen.getAllByTestId('SearchIcon');
      expect(queryableIcons).toHaveLength(2);
    });
  });

  describe('status chips', () => {
    it('shows correct status chips for each source', () => {
      renderTable();

      expect(screen.getByText('Ready')).toBeInTheDocument();
      expect(screen.getByText('Metadata Extracted')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();

      expect(screen.getByText('Ready').closest('.MuiChip-root')).toHaveClass(
        'MuiChip-colorSuccess'
      );
      expect(
        screen.getByText('Metadata Extracted').closest('.MuiChip-root')
      ).toHaveClass('MuiChip-colorSuccess');
      expect(screen.getByText('Pending').closest('.MuiChip-root')).toHaveClass(
        'MuiChip-colorWarning'
      );
      expect(screen.getByText('Error').closest('.MuiChip-root')).toHaveClass(
        'MuiChip-colorError'
      );
    });
  });

  describe('delete action', () => {
    it('calls apiService.deleteSource when delete confirmed', async () => {
      mockDeleteSource.mockResolvedValue({ success: true });
      const mockOnRefresh = jest.fn();
      renderTable({ onRefresh: mockOnRefresh });

      const deleteButtons = getActionButtons('Delete source');
      expect(deleteButtons).toHaveLength(4);
      fireEvent.click(deleteButtons[0]);

      // Confirmation dialog should appear
      expect(screen.getByText('Delete Source')).toBeInTheDocument();
      // "Invoice PDF" appears in both the table row and the dialog
      expect(screen.getAllByText(/Invoice PDF/)).toHaveLength(2);

      // Click the confirm Delete button in dialog
      const confirmButton = screen.getByRole('button', { name: 'Delete' });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteSource).toHaveBeenCalledWith('src-1');
      });

      await waitFor(() => {
        expect(mockShowSuccess).toHaveBeenCalledWith(
          'Source "Invoice PDF" deleted successfully'
        );
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });

    it('shows error notification when delete fails', async () => {
      mockDeleteSource.mockRejectedValue(new Error('Server error'));
      renderTable();

      const deleteButtons = getActionButtons('Delete source');
      fireEvent.click(deleteButtons[1]);

      // Confirm deletion
      const confirmButton = screen.getByRole('button', { name: 'Delete' });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockShowError).toHaveBeenCalledWith('Delete failed: Server error');
      });
    });

    it('closes dialog when cancel is clicked', async () => {
      renderTable();

      const deleteButtons = getActionButtons('Delete source');
      fireEvent.click(deleteButtons[0]);

      expect(screen.getByText('Delete Source')).toBeInTheDocument();

      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      fireEvent.click(cancelButton);

      // MUI Dialog uses transitions, so wait for it to be removed
      await waitFor(() => {
        expect(screen.queryByText('Delete Source')).not.toBeInTheDocument();
      });
    });
  });

  describe('loading state', () => {
    it('shows loading spinner when loading with empty sources', () => {
      renderTable({ sources: [], loading: true });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByText('No sources available')).not.toBeInTheDocument();
    });
  });
});
