import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { Message } from './message';

it('renders markup as literal text', () => {
  const { container } = render(<Message variant="answer">{'<b>x</b>'}</Message>);
  expect(screen.getByText('<b>x</b>')).toBeTruthy();
  expect(container.querySelector('b')).toBeNull();
});
