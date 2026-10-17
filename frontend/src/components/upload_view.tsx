import { useRef, useState } from 'react';
import type { ApiClient } from '../api/client';
import { ApiError, errorMessage, isRetryable } from '../api/errors';
import { fileToBase64, validatePdf, validateTitle } from '../validation';
import { Alert } from './alert';
import { Button } from './button';
import { Dropzone } from './dropzone';
import { Field } from './field';
import styles from './upload_view.module.css';

const COPY_SELECT_PDF = 'Selecciona un archivo PDF.';
const COPY_INDEXING = 'Indexando… los PDF grandes pueden tardar un minuto.';

type Phase = 'idle' | 'loading' | 'success' | 'error';

interface UploadResult {
  title: string;
  updated: boolean;
}

interface UploadViewProps {
  api: ApiClient;
  /** Called with the trimmed title after a 201 or 200 response. */
  onUploaded: (title: string) => void;
  /** Opens the Ask view for that title. */
  onAsk: (title: string) => void;
}

export function UploadView({ api, onUploaded, onAsk }: UploadViewProps) {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const latestFile = useRef<File | null>(null);

  async function selectFile(chosen: File) {
    latestFile.current = chosen;
    setFile(chosen);
    setFileError(null);
    setPhase('idle');
    setResult(null);
    setError(null);
    const problem = await validatePdf(chosen);
    // Ignore a stale result if the user already picked another file or removed this one.
    if (latestFile.current === chosen) {
      setFileError(problem);
    }
  }

  function removeFile() {
    latestFile.current = null;
    setFile(null);
    setFileError(null);
  }

  async function submit() {
    const nextTitleError = validateTitle(title);
    const nextFileError = file == null ? COPY_SELECT_PDF : await validatePdf(file);
    setTitleError(nextTitleError);
    setFileError(nextFileError);
    if (nextTitleError != null || nextFileError != null || file == null) {
      return;
    }
    const trimmed = title.trim();
    setPhase('loading');
    setResult(null);
    setError(null);
    try {
      const response = await api.ingestDocument(trimmed, await fileToBase64(file));
      setResult({ title: trimmed, updated: response.status === 'updated' });
      setPhase('success');
      onUploaded(trimmed);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 413) {
        setFileError(errorMessage(caught));
        setPhase('idle');
        return;
      }
      setError(caught);
      setPhase('error');
    }
  }

  const loading = phase === 'loading';

  return (
    <section className={styles.view} aria-labelledby="upload-heading">
      <h1 id="upload-heading" className={styles.heading}>
        Subir PDF
      </h1>
      <form
        className={styles.form}
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <Field
          label="Título"
          value={title}
          error={titleError}
          disabled={loading}
          autoComplete="off"
          onChange={(event) => {
            setTitle(event.target.value);
            setTitleError(null);
          }}
        />
        <Dropzone
          file={file}
          error={fileError}
          disabled={loading}
          onSelect={(chosen) => void selectFile(chosen)}
          onRemove={removeFile}
        />
        <div className={styles.actions}>
          <Button type="submit" variant="primary" loading={loading}>
            Subir PDF
          </Button>
          {loading && (
            <p className={styles.progress} role="status">
              {COPY_INDEXING}
            </p>
          )}
        </div>
      </form>
      {phase === 'success' && result && (
        <Alert
          variant="success"
          action={{ label: 'Hacer una pregunta →', onClick: () => onAsk(result.title) }}
        >
          <strong>{result.title}</strong> {result.updated ? 'ya estaba indexado.' : 'indexado.'}
        </Alert>
      )}
      {phase === 'error' && (
        <Alert
          variant="error"
          action={
            isRetryable(error) ? { label: 'Reintentar', onClick: () => void submit() } : undefined
          }
        >
          {errorMessage(error)}
        </Alert>
      )}
    </section>
  );
}
