import { useCallback, useEffect, useState } from 'react';
import type { ApiClient } from './api/client';
import { apiClient } from './api/index';
import styles from './app.module.css';
import type { Turn } from './components/ask_view';
import { AskView } from './components/ask_view';
import { StatusDot } from './components/status_dot';
import { UploadView } from './components/upload_view';

type View = 'upload' | 'ask';

function readView(): View {
  return window.location.hash === '#ask' ? 'ask' : 'upload';
}

interface AppProps {
  api?: ApiClient;
}

export function App({ api = apiClient }: AppProps) {
  const [view, setView] = useState<View>(readView);
  // Session state lives here so it survives switching views. Nothing is persisted.
  const [uploadedTitles, setUploadedTitles] = useState<string[]>([]);
  const [askTitle, setAskTitle] = useState('');
  const [threads, setThreads] = useState<Record<string, Turn[]>>({});

  useEffect(() => {
    function handleHashChange() {
      setView(readView());
    }
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleUploaded = useCallback((title: string) => {
    setUploadedTitles((current) => (current.includes(title) ? current : [...current, title]));
  }, []);

  const handleAsk = useCallback((title: string) => {
    setAskTitle(title);
    window.location.hash = '#ask';
  }, []);

  const handleTurn = useCallback((title: string, turn: Turn) => {
    setThreads((current) => ({ ...current, [title]: [...(current[title] ?? []), turn] }));
  }, []);

  return (
    <>
      <header className={styles.header}>
        <div className={styles.bar}>
          <span className={styles.brand}>RAG Docs</span>
          <nav className={styles.nav} aria-label="Principal">
            <a
              className={styles.link}
              href="#upload"
              aria-current={view === 'upload' ? 'page' : undefined}
            >
              Subir PDF
            </a>
            <a
              className={styles.link}
              href="#ask"
              aria-current={view === 'ask' ? 'page' : undefined}
            >
              Preguntar
            </a>
          </nav>
          <StatusDot api={api} />
        </div>
      </header>
      <main className={styles.main}>
        {view === 'upload' ? (
          <UploadView api={api} onUploaded={handleUploaded} onAsk={handleAsk} />
        ) : (
          <AskView
            api={api}
            titles={uploadedTitles}
            title={askTitle}
            onTitleChange={setAskTitle}
            threads={threads}
            onTurn={handleTurn}
          />
        )}
      </main>
    </>
  );
}
