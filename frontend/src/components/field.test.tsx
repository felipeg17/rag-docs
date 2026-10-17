import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { Field, TextAreaField } from './field';

it('labels the control and links hint and error', () => {
  render(<Field label="Título" hint="Ayuda" error="Escribe un título." />);
  const input = screen.getByLabelText('Título');
  expect(input.getAttribute('aria-invalid')).toBe('true');
  const describedBy = input.getAttribute('aria-describedby') ?? '';
  expect(describedBy.split(' ')).toHaveLength(2);
  expect(screen.getByText('Ayuda').id).toBe(describedBy.split(' ')[0]);
  expect(screen.getByText('Escribe un título.').id).toBe(describedBy.split(' ')[1]);
});

it('is valid and undescribed without hint or error', () => {
  render(<TextAreaField label="Pregunta" />);
  const textarea = screen.getByLabelText('Pregunta');
  expect(textarea.tagName).toBe('TEXTAREA');
  expect(textarea.getAttribute('aria-invalid')).toBeNull();
  expect(textarea.getAttribute('aria-describedby')).toBeNull();
});
