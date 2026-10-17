import { useEffect, useState } from 'react';
import type { ApiClient } from '../api/client';
import styles from './status_dot.module.css';

const RECHECK_MS = 30_000;

type Status = 'checking' | 'online' | 'offline';

const LABELS: Record<Status, string> = {
  checking: 'Comprobando…',
  online: 'Servidor en línea',
  offline: 'Servidor sin conexión',
};

interface StatusDotProps {
  api: Pick<ApiClient, 'health'>;
}

/** Backend status: a dot plus a text label (colour never stands alone). */
export function StatusDot({ api }: StatusDotProps) {
  const [status, setStatus] = useState<Status>('checking');

  useEffect(() => {
    let active = true;
    function check() {
      api.health().then(
        () => active && setStatus('online'),
        () => active && setStatus('offline'),
      );
    }
    check();
    const timer = setInterval(check, RECHECK_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [api]);

  return (
    <output className={styles.status}>
      <span className={`${styles.dot} ${styles[status]}`} aria-hidden="true" />
      <span className={styles.label}>{LABELS[status]}</span>
    </output>
  );
}
