import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { EmptyState } from './empty_state';

it('renders the sentence and the action', () => {
  render(<EmptyState action={<button type="button">Ir</button>}>Nada aún.</EmptyState>);
  expect(screen.getByText('Nada aún.')).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Ir' })).toBeTruthy();
});
