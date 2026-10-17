import type { ReactNode } from 'react';
import styles from './message.module.css';

export type MessageVariant = 'question' | 'answer';

interface MessageProps {
  variant: MessageVariant;
  children: ReactNode;
}

/** A chat turn. Children are rendered as text; line breaks are preserved by CSS. */
export function Message({ variant, children }: MessageProps) {
  return <div className={`${styles.message} ${styles[variant]}`}>{children}</div>;
}
