import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it } from 'vitest';
import type { SourceDocument } from '../api/types';
import { Sources } from './sources';

it('shows the 1-based page and no score', () => {
  const sources: SourceDocument[] = [
    { page_content: 'Texto', metadata: { pagina: 2 }, score: 0.9 },
    { page_content: 'Otro', metadata: {} },
  ];
  const { container } = render(<Sources sources={sources} />);
  expect(screen.getByText('Fuentes (2)')).toBeTruthy();
  expect(screen.getByText('Página 3')).toBeTruthy();
  expect(container.textContent).not.toContain('0.9');
  expect(container.textContent?.match(/Página/g)).toHaveLength(1);
});

it('shows the note instead of the details block when empty', () => {
  const { container } = render(<Sources sources={[]} />);
  expect(screen.getByText('No se devolvieron fuentes.')).toBeTruthy();
  expect(container.querySelector('details')).toBeNull();
});

it('toggles long excerpts', async () => {
  const sources: SourceDocument[] = [{ page_content: 'x'.repeat(300), metadata: {} }];
  render(<Sources sources={sources} />);
  const toggle = screen.getByRole('button', { name: 'Mostrar más' });
  await userEvent.click(toggle);
  expect(screen.getByRole('button', { name: 'Mostrar menos' }).getAttribute('aria-expanded')).toBe(
    'true',
  );
});
