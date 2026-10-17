import { render } from '@testing-library/react';
import { expect, it } from 'vitest';
import { Skeleton, Spinner } from './spinner';

it('renders the spinner hidden from assistive tech', () => {
  const { container } = render(<Spinner />);
  expect(container.firstElementChild?.getAttribute('aria-hidden')).toBe('true');
});

it('renders three skeleton lines', () => {
  const { container } = render(<Skeleton />);
  expect(container.firstElementChild?.children.length).toBe(3);
});
