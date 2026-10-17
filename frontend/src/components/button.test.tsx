import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Button } from './button';

it('calls onClick', async () => {
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Hola</Button>);
  await userEvent.click(screen.getByRole('button', { name: 'Hola' }));
  expect(onClick).toHaveBeenCalledOnce();
});

it('is busy and disabled while loading, keeping the label', async () => {
  const onClick = vi.fn();
  render(
    <Button loading onClick={onClick}>
      Preguntar
    </Button>,
  );
  const button = screen.getByRole('button', { name: 'Preguntar' }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  expect(button.getAttribute('aria-busy')).toBe('true');
  await userEvent.click(button);
  expect(onClick).not.toHaveBeenCalled();
});

it('defaults to type button', () => {
  render(<Button>Hola</Button>);
  expect(screen.getByRole('button').getAttribute('type')).toBe('button');
});
