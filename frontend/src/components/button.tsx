import type { ComponentProps } from 'react';
import styles from './button.module.css';
import { Spinner } from './spinner';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends ComponentProps<'button'> {
  variant?: ButtonVariant;
  loading?: boolean;
}

export function Button({
  variant = 'secondary',
  loading = false,
  disabled,
  type = 'button',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      className={`${styles.button} ${styles[variant]}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      <span className={loading ? styles.labelHidden : undefined}>{children}</span>
      {loading && (
        <span className={styles.spinner}>
          <Spinner />
        </span>
      )}
    </button>
  );
}
