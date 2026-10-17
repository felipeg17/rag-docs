import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { Card } from './card';

it('renders its children', () => {
  render(<Card>Contenido</Card>);
  expect(screen.getByText('Contenido')).toBeTruthy();
});
