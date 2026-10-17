import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MAX_PDF_BYTES } from '../api/client';
import { ApiError } from '../api/errors';
import { fakeApi, ingestResponse, pdfFile } from '../test/helpers';
import { UploadView } from './upload_view';

function setup(ingest = vi.fn().mockResolvedValue(ingestResponse('Manual'))) {
  const api = fakeApi({ ingestDocument: ingest });
  const onUploaded = vi.fn();
  const onAsk = vi.fn();
  render(<UploadView api={api} onUploaded={onUploaded} onAsk={onAsk} />);
  return { ingest, onUploaded, onAsk };
}

async function fill(title: string, file: File | null = pdfFile()) {
  const user = userEvent.setup({ applyAccept: false });
  fireEvent.change(screen.getByLabelText('Título'), { target: { value: title } });
  if (file) {
    await user.upload(screen.getByLabelText('Archivo PDF'), file);
  }
  return user;
}

async function submit(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Subir PDF' }));
}

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

describe('title validation', () => {
  it.each([
    ['whitespace only', '   ', 'Escribe un título.'],
    ['a slash', 'a/b', 'El título no puede contener «/» ni ser «.» o «..».'],
    ['a dot', '.', 'El título no puede contener «/» ni ser «.» o «..».'],
    ['two dots', '..', 'El título no puede contener «/» ni ser «.» o «..».'],
    ['1001 characters', 'a'.repeat(1001), 'El título admite como máximo 1000 caracteres.'],
  ])('blocks %s without calling the API', async (_name, title, copy) => {
    const { ingest } = setup();
    const user = await fill(title);
    await submit(user);
    expect(await screen.findByText(copy)).toBeTruthy();
    expect(ingest).not.toHaveBeenCalled();
  });

  it('blocks an empty title', async () => {
    const { ingest } = setup();
    const user = await fill('');
    await submit(user);
    expect(await screen.findByText('Escribe un título.')).toBeTruthy();
    expect(ingest).not.toHaveBeenCalled();
  });

  it('accepts 1000 characters and sends the title trimmed', async () => {
    const { ingest } = setup();
    const title = 'a'.repeat(1000);
    const user = await fill(`  ${title}  `);
    await submit(user);
    await waitFor(() => expect(ingest).toHaveBeenCalledOnce());
    expect(ingest.mock.calls[0]?.[0]).toBe(title);
  });
});

describe('file validation', () => {
  it('blocks a file without PDF magic bytes', async () => {
    const { ingest } = setup();
    const user = await fill('Manual', new File(['plain text'], 'x.pdf'));
    expect(await screen.findByText('El archivo no es un PDF.')).toBeTruthy();
    await submit(user);
    expect(ingest).not.toHaveBeenCalled();
  });

  it('blocks a file over MAX_PDF_BYTES', async () => {
    const { ingest } = setup();
    const user = await fill('Manual', pdfFile('big.pdf', MAX_PDF_BYTES + 1));
    expect(await screen.findByText('El PDF supera el límite de 20 MB.')).toBeTruthy();
    await submit(user);
    expect(ingest).not.toHaveBeenCalled();
  });

  it('accepts a file of exactly MAX_PDF_BYTES', async () => {
    const { ingest } = setup();
    const user = await fill('Manual', pdfFile('max.pdf', MAX_PDF_BYTES));
    await submit(user);
    await waitFor(() => expect(ingest).toHaveBeenCalledOnce());
  });

  it('asks for a file when none is chosen', async () => {
    const { ingest } = setup();
    const user = await fill('Manual', null);
    await submit(user);
    expect(await screen.findByText('Selecciona un archivo PDF.')).toBeTruthy();
    expect(ingest).not.toHaveBeenCalled();
  });
});

describe('results', () => {
  it('shows the 201 success and opens the Ask view with the title', async () => {
    const { onUploaded, onAsk } = setup();
    const user = await fill(' Manual ');
    await submit(user);
    const status = await screen.findByRole('status');
    expect(status.textContent).toContain('Manual indexado.');
    expect(onUploaded).toHaveBeenCalledWith('Manual');
    await user.click(screen.getByRole('button', { name: 'Hacer una pregunta →' }));
    expect(onAsk).toHaveBeenCalledWith('Manual');
  });

  it('shows the 200 updated success', async () => {
    const { onUploaded } = setup(vi.fn().mockResolvedValue(ingestResponse('Manual', 'updated')));
    const user = await fill('Manual');
    await submit(user);
    const status = await screen.findByText(/ya estaba indexado\./);
    expect(status.closest('[role="status"]')?.textContent).toContain('Manual ya estaba indexado.');
    expect(onUploaded).toHaveBeenCalledWith('Manual');
    expect(screen.getByRole('button', { name: 'Hacer una pregunta →' })).toBeTruthy();
  });

  it('shows fixed copy for a 500 and retries', async () => {
    const ingest = vi
      .fn()
      .mockRejectedValueOnce(new ApiError('http', { status: 500, detail: 'Traceback secret' }))
      .mockResolvedValueOnce(ingestResponse('Manual'));
    setup(ingest);
    const user = await fill('Manual');
    await submit(user);
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('El servidor no pudo responder.');
    expect(alert.textContent).not.toContain('secret');
    await user.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByText(/indexado\./)).toBeTruthy();
    expect(ingest).toHaveBeenCalledTimes(2);
  });

  it('puts a 413 on the file field', async () => {
    setup(vi.fn().mockRejectedValue(new ApiError('http', { status: 413 })));
    const user = await fill('Manual');
    await submit(user);
    expect(await screen.findByText('El archivo es demasiado grande para subirlo.')).toBeTruthy();
  });
});
