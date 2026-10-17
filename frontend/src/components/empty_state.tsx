import type { ReactNode } from 'react';
import styles from './empty_state.module.css';

interface EmptyStateProps {
  children: ReactNode;
  action?: ReactNode;
}

/** One sentence plus, optionally, the next action. */
export function EmptyState({ children, action }: EmptyStateProps) {
  return (
    <div className={styles.empty}>
      <p>{children}</p>
      {action}
    </div>
  );
}
