import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Dropzone } from './dropzone';

const PDF = new File(['%PDF-1.4'], 'manual.pdf', { type: 'application/pdf' });

it('selects a file from the input', async () => {
  const onSelect = vi.fn();
  render(<Dropzone file={null} onSelect={onSelect} onRemove={vi.fn()} />);
  await userEvent.upload(screen.getByLabelText('Archivo PDF'), PDF);
  expect(onSelect).toHaveBeenCalledWith(PDF);
});

it('selects a dropped file', () => {
  const onSelect = vi.fn();
  render(<Dropzone file={null} onSelect={onSelect} onRemove={vi.fn()} />);
  fireEvent.drop(screen.getByRole('button', { name: /Arrastra un PDF/ }), {
    dataTransfer: { files: [PDF] },
  });
  expect(onSelect).toHaveBeenCalledWith(PDF);
});

it('opens the file input from the zone button', async () => {
  render(<Dropzone file={null} onSelect={vi.fn()} onRemove={vi.fn()} />);
  const input = screen.getByLabelText('Archivo PDF') as HTMLInputElement;
  const click = vi.spyOn(input, 'click');
  await userEvent.click(screen.getByRole('button', { name: /Arrastra un PDF/ }));
  expect(click).toHaveBeenCalled();
});

it('shows the file name and size with a remove button, and the error', async () => {
  const onRemove = vi.fn();
  render(
    <Dropzone file={PDF} error="El archivo no es un PDF." onSelect={vi.fn()} onRemove={onRemove} />,
  );
  expect(screen.getByText('manual.pdf')).toBeTruthy();
  expect(screen.getByText('El archivo no es un PDF.')).toBeTruthy();
  await userEvent.click(screen.getByRole('button', { name: 'Quitar' }));
  expect(onRemove).toHaveBeenCalledOnce();
});
