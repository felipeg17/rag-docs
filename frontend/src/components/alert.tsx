import type { ReactNode } from 'react';
import styles from './alert.module.css';
import { Button } from './button';

export type AlertVariant = 'error' | 'success' | 'info';

interface AlertAction {
  label: string;
  onClick: () => void;
}

interface AlertProps {
  variant: AlertVariant;
  children: ReactNode;
  action?: AlertAction;
}

function Icon({ variant }: { variant: AlertVariant }) {
  const path =
    variant === 'success'
      ? 'M5 12.5l4.5 4.5L19 7.5'
      : variant === 'error'
        ? 'M12 7v6M12 16.5v.5'
        : 'M12 11v6M12 7.5v.5';
  return (
    <svg
      className={styles.icon}
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {variant !== 'success' && <circle cx="12" cy="12" r="9.5" />}
      <path d={path} />
    </svg>
  );
}

/** Inline message. Errors use `role="alert"`; success and info use `role="status"`. */
export function Alert({ variant, children, action }: AlertProps) {
  return (
    <div
      className={`${styles.alert} ${styles[variant]}`}
      role={variant === 'error' ? 'alert' : 'status'}
    >
      <Icon variant={variant} />
      <p className={styles.message}>{children}</p>
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
