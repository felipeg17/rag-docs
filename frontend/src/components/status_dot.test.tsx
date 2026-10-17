import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { ApiError } from '../api/errors';
import { StatusDot } from './status_dot';

it('shows checking, then online for a healthy server', async () => {
  render(<StatusDot api={{ health: vi.fn().mockResolvedValue(undefined) }} />);
  expect(screen.getByText('Comprobando…')).toBeTruthy();
  expect(await screen.findByText('Servidor en línea')).toBeTruthy();
});

it.each([
  ['a 503', new ApiError('http', { status: 503 })],
  ['a timeout', new ApiError('timeout')],
  ['a network error', new ApiError('network')],
])('shows offline on %s', async (_name, error) => {
  render(<StatusDot api={{ health: vi.fn().mockRejectedValue(error) }} />);
  expect(await screen.findByText('Servidor sin conexión')).toBeTruthy();
});
