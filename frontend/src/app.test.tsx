import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { App } from './app';
import { answerResponse, fakeApi, ingestResponse, pdfFile } from './test/helpers';

function goTo(hash: string) {
  act(() => {
    window.location.hash = hash;
  });
}

async function upload(user: ReturnType<typeof userEvent.setup>, title: string) {
  fireEvent.change(screen.getByLabelText('Título'), { target: { value: title } });
  await user.upload(screen.getByLabelText('Archivo PDF'), pdfFile());
  await user.click(screen.getByRole('button', { name: 'Subir PDF' }));
}

beforeEach(() => {
  window.location.hash = '';
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

afterEach(() => {
  vi.restoreAllMocks();
});

it('renders the view named in the URL hash', () => {
  window.location.hash = '#ask';
  render(<App api={fakeApi()} />);
  expect(screen.getByRole('heading', { name: 'Preguntar' })).toBeTruthy();
  expect(screen.getByLabelText('Documento')).toBeTruthy();
});

it('defaults to the upload view and shows the backend status', async () => {
  render(<App api={fakeApi()} />);
  expect(screen.getByRole('heading', { name: 'Subir PDF' })).toBeTruthy();
  expect(await screen.findByText('Servidor en línea')).toBeTruthy();
});

it('keeps session state across views and writes nothing to web storage', async () => {
  const setItem = vi.spyOn(Storage.prototype, 'setItem');
  const ingestDocument = vi
    .fn()
    .mockResolvedValueOnce(ingestResponse('Manual A', 'created'))
    .mockResolvedValueOnce(ingestResponse('Manual B', 'updated'));
  const ask = vi.fn().mockResolvedValue(answerResponse('Respuesta de A'));
  const user = userEvent.setup();
  render(<App api={fakeApi({ ingestDocument, ask })} />);

  await upload(user, 'Manual A');
  await screen.findByText(/indexado\./);
  await upload(user, 'Manual B');
  await screen.findByText(/ya estaba indexado\./);

  // The next action opens the Ask view with that title filled in.
  await user.click(screen.getByRole('button', { name: 'Hacer una pregunta →' }));
  await waitFor(() => expect(window.location.hash).toBe('#ask'));
  const title = await screen.findByLabelText('Documento');
  expect((title as HTMLInputElement).value).toBe('Manual B');
  const options = [...document.querySelectorAll('datalist option')].map((o) =>
    o.getAttribute('value'),
  );
  expect(options).toEqual(['Manual A', 'Manual B']);

  // A thread belongs to its title.
  fireEvent.change(title, { target: { value: 'Manual A' } });
  await user.type(screen.getByLabelText('Pregunta'), 'pregunta A{Enter}');
  await screen.findByText('Respuesta de A');
  fireEvent.change(title, { target: { value: 'Manual B' } });
  expect(screen.queryByText('Respuesta de A')).toBeNull();
  fireEvent.change(title, { target: { value: 'Manual A' } });
  expect(screen.getByText('Respuesta de A')).toBeTruthy();

  // Switching views keeps it.
  goTo('#upload');
  expect(await screen.findByRole('heading', { name: 'Subir PDF' })).toBeTruthy();
  goTo('#ask');
  const again = await screen.findByLabelText('Documento');
  expect((again as HTMLInputElement).value).toBe('Manual A');
  expect(screen.getByText('Respuesta de A')).toBeTruthy();

  expect(setItem).not.toHaveBeenCalled();
  expect(localStorage.length).toBe(0);
  expect(sessionStorage.length).toBe(0);
});

it('marks the active nav link', () => {
  render(<App api={fakeApi()} />);
  const nav = screen.getByRole('navigation', { name: 'Principal' });
  expect(within(nav).getByRole('link', { name: 'Subir PDF' }).getAttribute('aria-current')).toBe(
    'page',
  );
  expect(
    within(nav).getByRole('link', { name: 'Preguntar' }).getAttribute('aria-current'),
  ).toBeNull();
});
