import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ApiClient } from '../api/client';
import { ApiError } from '../api/errors';
import { answerResponse, fakeApi } from '../test/helpers';
import type { Turn } from './ask_view';
import { AskView } from './ask_view';

/** Holds the state `App` owns, so the view behaves as it does in the app. */
function Harness({ api, initialTitle = 'Manual' }: { api: ApiClient; initialTitle?: string }) {
  const [title, setTitle] = useState(initialTitle);
  const [threads, setThreads] = useState<Record<string, Turn[]>>({});
  return (
    <AskView
      api={api}
      titles={['Manual', 'Otro']}
      title={title}
      onTitleChange={setTitle}
      threads={threads}
      onTurn={(key, turn) =>
        setThreads((current) => ({ ...current, [key]: [...(current[key] ?? []), turn] }))
      }
    />
  );
}

function setup(ask = vi.fn().mockResolvedValue(answerResponse('Respuesta'))) {
  render(<Harness api={fakeApi({ ask })} />);
  return ask;
}

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

describe('submitting', () => {
  it('Enter submits and Shift+Enter does not', async () => {
    const ask = setup();
    const user = userEvent.setup();
    const box = screen.getByLabelText('Pregunta');
    await user.type(box, 'Hola{Shift>}{Enter}{/Shift}mundo');
    expect(ask).not.toHaveBeenCalled();
    expect((box as HTMLTextAreaElement).value).toBe('Hola\nmundo');
    await user.type(box, '{Enter}');
    await waitFor(() => expect(ask).toHaveBeenCalledOnce());
    expect(ask.mock.calls[0]?.[1]).toBe('Hola\nmundo');
  });

  it('trims the title and defaults to the standard strategy', async () => {
    const ask = setup();
    const user = userEvent.setup();
    fireEvent.change(screen.getByLabelText('Documento'), { target: { value: '  Manual  ' } });
    await user.type(screen.getByLabelText('Pregunta'), 'Qué es{Enter}');
    await waitFor(() => expect(ask).toHaveBeenCalledOnce());
    expect(ask).toHaveBeenCalledWith('Manual', 'Qué es', 'standard');
  });

  it('sends rerank when selected and explains it returns no sources', async () => {
    const ask = setup();
    const user = userEvent.setup();
    await user.click(screen.getByRole('radio', { name: 'Rerank' }));
    expect(screen.getByText('Rerank no devuelve fuentes.')).toBeTruthy();
    await user.type(screen.getByLabelText('Pregunta'), 'Qué es{Enter}');
    await waitFor(() => expect(ask).toHaveBeenCalledOnce());
    expect(ask.mock.calls[0]?.[2]).toBe('rerank');
  });

  it('validates the title and the question before calling the API', async () => {
    const ask = setup();
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Preguntar' }));
    expect(await screen.findByText('Escribe una pregunta.')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Documento'), { target: { value: '' } });
    await user.type(screen.getByLabelText('Pregunta'), 'x{Enter}');
    expect(await screen.findByText('Escribe un título.')).toBeTruthy();
    expect(ask).not.toHaveBeenCalled();
  });

  it('offers the uploaded titles as suggestions', () => {
    setup();
    const options = [...document.querySelectorAll('datalist option')].map((o) =>
      o.getAttribute('value'),
    );
    expect(options).toEqual(['Manual', 'Otro']);
  });
});

describe('answers', () => {
  it('renders markup as literal text', async () => {
    const { container } = render(
      <Harness api={fakeApi({ ask: vi.fn().mockResolvedValue(answerResponse('<b>x</b>')) })} />,
    );
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    expect(await screen.findByText('<b>x</b>')).toBeTruthy();
    expect(container.querySelector('b')).toBeNull();
  });

  it('shows the page (pagina + 1) and no score', async () => {
    const sources = [{ page_content: 'Un pasaje', metadata: { pagina: 2 }, score: 0.5 }];
    const { container } = render(
      <Harness api={fakeApi({ ask: vi.fn().mockResolvedValue(answerResponse('R', sources)) })} />,
    );
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    expect(await screen.findByText('Página 3')).toBeTruthy();
    expect(screen.getByText('Fuentes (1)')).toBeTruthy();
    expect(container.textContent).not.toContain('0.5');
  });

  it('shows a note when there are no sources', async () => {
    setup();
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    expect(await screen.findByText('No se devolvieron fuentes.')).toBeTruthy();
  });

  it('shows the no-answer message for a null answer', async () => {
    setup(vi.fn().mockResolvedValue(answerResponse(null)));
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    expect(await screen.findByText('No se obtuvo respuesta.')).toBeTruthy();
  });

  it('treats a missing source_documents as empty', async () => {
    setup(vi.fn().mockResolvedValue({ answer: 'R' }));
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    expect(await screen.findByText('No se devolvieron fuentes.')).toBeTruthy();
  });

  it('keeps two consecutive questions visible, in a polite live region', async () => {
    const ask = vi
      .fn()
      .mockResolvedValueOnce(answerResponse('Primera'))
      .mockResolvedValueOnce(answerResponse('Segunda'));
    setup(ask);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Pregunta'), 'uno{Enter}');
    await screen.findByText('Primera');
    await user.type(screen.getByLabelText('Pregunta'), 'dos{Enter}');
    await screen.findByText('Segunda');
    expect(screen.getByText('uno')).toBeTruthy();
    expect(screen.getByText('Primera')).toBeTruthy();
    expect(screen.getByText('Segunda').closest('[aria-live]')?.getAttribute('aria-live')).toBe(
      'polite',
    );
  });

  it('clears the composer after an answer but keeps it after an error', async () => {
    setup(vi.fn().mockRejectedValue(new ApiError('http', { status: 500 })));
    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Pregunta'), 'conservar{Enter}');
    await screen.findByRole('alert');
    expect((screen.getByLabelText('Pregunta') as HTMLTextAreaElement).value).toBe('conservar');
  });
});

describe('errors', () => {
  it('shows the 404 copy on the document field', async () => {
    setup(vi.fn().mockRejectedValue(new ApiError('http', { status: 404 })));
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    expect(
      await screen.findByText('Documento no encontrado. Revisa el título o súbelo primero.'),
    ).toBeTruthy();
    expect(screen.getByLabelText('Documento').getAttribute('aria-invalid')).toBe('true');
  });

  it.each([
    [
      new ApiError('http', { status: 422, detail: 'secret' }),
      'Revisa los datos e inténtalo de nuevo.',
      false,
    ],
    [
      new ApiError('http', { status: 500, detail: 'secret' }),
      'El servidor no pudo responder. Inténtalo de nuevo.',
      true,
    ],
    [
      new ApiError('http', { status: 504 }),
      'El servidor tardó demasiado en responder. Inténtalo de nuevo.',
      true,
    ],
    [
      new ApiError('timeout'),
      'El servidor tardó demasiado en responder. Inténtalo de nuevo.',
      true,
    ],
    [new ApiError('network'), 'El servidor no pudo responder. Inténtalo de nuevo.', true],
  ])('maps %o to fixed copy', async (error, copy, retry) => {
    setup(vi.fn().mockRejectedValue(error));
    await userEvent.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain(copy);
    expect(alert.textContent).not.toContain('secret');
    expect(screen.queryByRole('button', { name: 'Reintentar' }) != null).toBe(retry);
  });

  it('retries with the same question', async () => {
    const ask = vi
      .fn()
      .mockRejectedValueOnce(new ApiError('network'))
      .mockResolvedValueOnce(answerResponse('Ahora sí'));
    setup(ask);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Pregunta'), 'q{Enter}');
    await user.click(await screen.findByRole('button', { name: 'Reintentar' }));
    expect(await screen.findByText('Ahora sí')).toBeTruthy();
    expect(ask).toHaveBeenCalledTimes(2);
  });
});
