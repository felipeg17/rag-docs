import styles from './spinner.module.css';

/** Decorative: the surrounding control carries `aria-busy`. */
export function Spinner() {
  return <span className={styles.spinner} aria-hidden="true" />;
}

/** Three placeholder lines for content that is loading. */
export function Skeleton() {
  return (
    <div className={styles.skeleton} aria-hidden="true">
      <span className={styles.line} />
      <span className={styles.line} />
      <span className={styles.line} />
    </div>
  );
}
