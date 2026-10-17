import { useState } from 'react';
import type { SourceDocument } from '../api/types';
import styles from './sources.module.css';

const LONG_EXCERPT = 200;

function pageLabel(source: SourceDocument): string | null {
  const page = source.metadata.pagina;
  return typeof page === 'number' ? `Página ${page + 1}` : null;
}

function SourceItem({ source }: { source: SourceDocument }) {
  const [expanded, setExpanded] = useState(false);
  const page = pageLabel(source);
  const long = source.page_content.length > LONG_EXCERPT;
  return (
    <li className={styles.item}>
      {page && <span className={styles.page}>{page}</span>}
      <p className={expanded || !long ? styles.excerpt : `${styles.excerpt} ${styles.clamped}`}>
        {source.page_content}
      </p>
      {long && (
        <button
          type="button"
          className={styles.toggle}
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? 'Mostrar menos' : 'Mostrar más'}
        </button>
      )}
    </li>
  );
}

interface SourcesProps {
  sources: SourceDocument[];
}

/** Collapsible list of the passages an answer came from, or a note when there are none. */
export function Sources({ sources }: SourcesProps) {
  if (sources.length === 0) {
    return <p className={styles.note}>No se devolvieron fuentes.</p>;
  }
  return (
    <details className={styles.sources}>
      <summary className={styles.summary}>Fuentes ({sources.length})</summary>
      <ul className={styles.list}>
        {sources.map((source, index) => (
          // Sources are a fixed, ordered list per answer.
          // biome-ignore lint/suspicious/noArrayIndexKey: the list never reorders
          <SourceItem key={index} source={source} />
        ))}
      </ul>
    </details>
  );
}
