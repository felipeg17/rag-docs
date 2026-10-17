import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Alert } from './alert';

it('uses role alert for errors and role status otherwise', () => {
  const { rerender } = render(<Alert variant="error">Falló</Alert>);
  expect(screen.getByRole('alert').textContent).toContain('Falló');
  rerender(<Alert variant="success">Listo</Alert>);
  expect(screen.getByRole('status').textContent).toContain('Listo');
});

it('runs the action', async () => {
  const onClick = vi.fn();
  render(
    <Alert variant="error" action={{ label: 'Reintentar', onClick }}>
      Falló
    </Alert>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
  expect(onClick).toHaveBeenCalledOnce();
});
