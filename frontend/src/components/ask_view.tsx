import type { KeyboardEvent } from 'react';
import { useEffect, useId, useRef, useState } from 'react';
import type { ApiClient } from '../api/client';
import { ApiError, errorMessage, isRetryable } from '../api/errors';
import type { SourceDocument, Strategy } from '../api/types';
import { validateTitle } from '../validation';
import { Alert } from './alert';
import styles from './ask_view.module.css';
import { Button } from './button';
import { EmptyState } from './empty_state';
import { Field, TextAreaField } from './field';
import { Message } from './message';
import { Sources } from './sources';
import { Skeleton } from './spinner';

const COPY_QUESTION_EMPTY = 'Escribe una pregunta.';
const COPY_NO_ANSWER = 'No se obtuvo respuesta.';

let lastTurnId = 0;

/** One question and its answer, kept in memory per document title. */
export interface Turn {
  id: number;
  question: string;
  answer: string | null;
  sources: SourceDocument[];
}

interface PendingQuestion {
  title: string;
  question: string;
}

interface AskViewProps {
  api: ApiClient;
  /** Titles uploaded in this page session, offered as suggestions. */
  titles: string[];
  title: string;
  onTitleChange: (title: string) => void;
  threads: Record<string, Turn[]>;
  onTurn: (title: string, turn: Turn) => void;
}

const STRATEGIES: { value: Strategy; label: string }[] = [
  { value: 'standard', label: 'Estándar' },
  { value: 'rerank', label: 'Rerank' },
];

export function AskView({ api, titles, title, onTitleChange, threads, onTurn }: AskViewProps) {
  const [question, setQuestion] = useState('');
  const [strategy, setStrategy] = useState<Strategy>('standard');
  const [titleError, setTitleError] = useState<string | null>(null);
  const [questionError, setQuestionError] = useState<string | null>(null);
  const [pending, setPending] = useState<PendingQuestion | null>(null);
  const [error, setError] = useState<unknown>(null);
  const listId = useId();
  const endRef = useRef<HTMLDivElement>(null);

  const trimmedTitle = title.trim();
  const thread = threads[trimmedTitle] ?? [];
  const visiblePending = pending != null && pending.title === trimmedTitle ? pending : null;
  const turnCount = thread.length;

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll whenever the thread grows or a question starts
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' });
  }, [turnCount, visiblePending]);

  async function submit() {
    const nextTitleError = validateTitle(title);
    const trimmedQuestion = question.trim();
    const nextQuestionError = trimmedQuestion === '' ? COPY_QUESTION_EMPTY : null;
    setTitleError(nextTitleError);
    setQuestionError(nextQuestionError);
    if (nextTitleError != null || nextQuestionError != null || pending != null) {
      return;
    }
    setError(null);
    setPending({ title: trimmedTitle, question: trimmedQuestion });
    try {
      const response = await api.ask(trimmedTitle, trimmedQuestion, strategy);
      lastTurnId += 1;
      onTurn(trimmedTitle, {
        id: lastTurnId,
        question: trimmedQuestion,
        answer: response.answer ?? null,
        sources: response.source_documents ?? [],
      });
      setQuestion('');
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 404) {
        setTitleError(errorMessage(caught));
      } else {
        setError(caught);
      }
    } finally {
      setPending(null);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void submit();
    }
  }

  const loading = pending != null;

  return (
    <section className={styles.view} aria-labelledby="ask-heading">
      <h1 id="ask-heading" className={styles.heading}>
        Preguntar
      </h1>
      <div className={styles.settings}>
        <Field
          label="Documento"
          value={title}
          error={titleError}
          list={listId}
          autoComplete="off"
          onChange={(event) => {
            onTitleChange(event.target.value);
            setTitleError(null);
            setError(null);
          }}
        />
        <datalist id={listId}>
          {titles.map((known) => (
            <option key={known} value={known} />
          ))}
        </datalist>
        <fieldset className={styles.strategy}>
          <legend className={styles.legend}>Estrategia</legend>
          <div className={styles.options}>
            {STRATEGIES.map((option) => (
              <label key={option.value} className={styles.option}>
                <input
                  type="radio"
                  name="strategy"
                  className={styles.radio}
                  value={option.value}
                  checked={strategy === option.value}
                  onChange={() => setStrategy(option.value)}
                />
                <span className={styles.optionLabel}>{option.label}</span>
              </label>
            ))}
          </div>
          {strategy === 'rerank' && <p className={styles.hint}>Rerank no devuelve fuentes.</p>}
        </fieldset>
      </div>

      <div className={styles.thread} aria-live="polite" aria-relevant="additions">
        {thread.length === 0 && visiblePending == null && (
          <EmptyState>Haz una pregunta sobre un documento subido.</EmptyState>
        )}
        {thread.map((turn) => (
          <article key={turn.id} className={styles.turn}>
            <Message variant="question">{turn.question}</Message>
            <Message variant="answer">{turn.answer ?? COPY_NO_ANSWER}</Message>
            <Sources sources={turn.sources} />
          </article>
        ))}
        {visiblePending && (
          <article className={styles.turn}>
            <Message variant="question">{visiblePending.question}</Message>
            <span className="visually-hidden">Buscando respuesta…</span>
            <Skeleton />
          </article>
        )}
        {error != null && !loading && (
          <Alert
            variant="error"
            action={
              isRetryable(error) ? { label: 'Reintentar', onClick: () => void submit() } : undefined
            }
          >
            {errorMessage(error)}
          </Alert>
        )}
        <div ref={endRef} />
      </div>

      <form
        className={styles.composer}
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <TextAreaField
          label="Pregunta"
          value={question}
          error={questionError}
          rows={2}
          hint={loading ? 'Esto puede tardar unos segundos.' : undefined}
          onKeyDown={handleKeyDown}
          onChange={(event) => {
            setQuestion(event.target.value);
            setQuestionError(null);
          }}
        />
        <Button type="submit" variant="primary" loading={loading}>
          Preguntar
        </Button>
      </form>
    </section>
  );
}
