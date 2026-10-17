import type { DragEvent } from 'react';
import { useRef, useState } from 'react';
import { formatBytes } from '../validation';
import { Button } from './button';
import styles from './dropzone.module.css';

interface DropzoneProps {
  file: File | null;
  error?: string | null;
  disabled?: boolean;
  onSelect: (file: File) => void;
  onRemove: () => void;
}

/** Drop or browse for one PDF. Validation is the parent's job (it is async). */
export function Dropzone({ file, error, disabled = false, onSelect, onRemove }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped && !disabled) {
      onSelect(dropped);
    }
  }

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={`${styles.zone} ${dragging ? styles.dragging : ''}`}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? 'dropzone-error' : undefined}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        Arrastra un PDF aquí o selecciona un archivo
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        aria-label="Archivo PDF"
        hidden
        onChange={(event) => {
          const chosen = event.target.files?.[0];
          if (chosen) {
            onSelect(chosen);
          }
          // Allow choosing the same file again after removing it.
          event.target.value = '';
        }}
      />
      {file && (
        <div className={styles.file}>
          <span className={styles.name}>{file.name}</span>
          <span className={styles.size}>{formatBytes(file.size)}</span>
          <Button variant="ghost" disabled={disabled} onClick={onRemove}>
            Quitar
          </Button>
        </div>
      )}
      {error && (
        <p id="dropzone-error" className={styles.error}>
          {error}
        </p>
      )}
    </div>
  );
}
