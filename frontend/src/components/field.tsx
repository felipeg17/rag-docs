import type { ComponentProps, ReactNode } from 'react';
import { useId } from 'react';
import styles from './field.module.css';

interface FieldFrameProps {
  label: string;
  hint?: string;
  error?: string | null;
}

interface FrameRenderProps {
  id: string;
  describedBy?: string;
  invalid: boolean;
}

function FieldFrame({
  label,
  hint,
  error,
  render,
}: FieldFrameProps & { render: (props: FrameRenderProps) => ReactNode }) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ');
  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>
        {label}
      </label>
      {render({ id, describedBy: describedBy || undefined, invalid: Boolean(error) })}
      {hint && (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className={styles.error}>
          {error}
        </p>
      )}
    </div>
  );
}

type InputFieldProps = FieldFrameProps & Omit<ComponentProps<'input'>, 'id'>;

/** Single-line text field: label above, optional hint and error below. */
export function Field({ label, hint, error, ...rest }: InputFieldProps) {
  return (
    <FieldFrame
      label={label}
      hint={hint}
      error={error}
      render={({ id, describedBy, invalid }) => (
        <input
          {...rest}
          id={id}
          className={styles.control}
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
        />
      )}
    />
  );
}

type TextAreaFieldProps = FieldFrameProps & Omit<ComponentProps<'textarea'>, 'id'>;

/** Multi-line variant of `Field`. */
export function TextAreaField({ label, hint, error, ...rest }: TextAreaFieldProps) {
  return (
    <FieldFrame
      label={label}
      hint={hint}
      error={error}
      render={({ id, describedBy, invalid }) => (
        <textarea
          {...rest}
          id={id}
          className={`${styles.control} ${styles.textarea}`}
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
        />
      )}
    />
  );
}
