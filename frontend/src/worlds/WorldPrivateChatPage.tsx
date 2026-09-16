import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useParams } from "react-router-dom";

import {
  getWorldBySlug,
  type WorldCatalogueEntry,
} from "./worldCatalogue";

import {
  createPrivateChatConversation,
  sendPrivateChatMessage,
} from "./worldPrivateChatApi";

import {
  getWorldPresentation,
  type WorldPresentation,
} from "./worldPresentation";

import styles from "./WorldPrivateChatPage.module.css";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

function applyPresentationTheme(presentation: WorldPresentation) {
  return {
    "--ecb-study-primary": presentation.primary,
    "--ecb-study-secondary": presentation.secondary,
    "--ecb-study-accent": presentation.accent,
    "--ecb-study-bg": presentation.background,
    "--ecb-study-surface": presentation.surface,
    "--ecb-study-surface-alt": presentation.surfaceAlt,
    "--ecb-study-text": presentation.text,
    "--ecb-study-muted": presentation.muted,
    "--ecb-study-atmosphere": presentation.atmosphere,
  } as React.CSSProperties;
}

export default function WorldPrivateChatPage() {
  const { worldSlug } = useParams<{
    worldSlug: string;
  }>();

  const world = useMemo<WorldCatalogueEntry | undefined>(
    () => getWorldBySlug(worldSlug ?? ""),
    [worldSlug],
  );

  const presentation = useMemo(
    () => getWorldPresentation(worldSlug ?? ""),
    [worldSlug],
  );

  const [conversationId, setConversationId] =
    useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loadingConversation, setLoadingConversation] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function initialiseConversation() {
      if (!world) {
        setLoadingConversation(false);
        return;
      }

      setLoadingConversation(true);
      setError(null);
      setConversationId(null);
      setMessages([]);

      try {
        const conversation =
          await createPrivateChatConversation(world.worldId);

        if (!active) return;

        setConversationId(conversation.conversation_id);
      } catch (cause) {
        if (!active) return;

        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to create the private conversation.",
        );
      } finally {
        if (active) {
          setLoadingConversation(false);
        }
      }
    }

    void initialiseConversation();

    return () => {
      active = false;
    };
  }, [world]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const message = draft.trim();

    if (!message || !conversationId || sending) {
      return;
    }

    setSending(true);
    setError(null);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
    };

    setMessages((current) => [...current, userMessage]);
    setDraft("");

    try {
      const result =
        await sendPrivateChatMessage(
          conversationId,
          message,
        );

      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: result.response,
        },
      ]);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to send the message.",
      );
    } finally {
      setSending(false);
    }
  }

  function usePrompt(prompt: string) {
    setDraft(prompt);
  }

  if (!world) {
    return (
      <main className={styles.studyRoom}>
        <div className={styles.studyShell}>
          <section className={styles.chatPanel}>
            <div className={styles.chatHeader}>
              <div className={styles.chatHeaderIdentity}>
                <div className={styles.avatar}>?</div>
                <div>
                  <strong>EasyChatBot</strong>
                  <span>Learning World</span>
                </div>
              </div>
            </div>
            <div className={styles.messages}>
              <h1>World not found</h1>
              <p>
                The requested Learning World is not available.
              </p>
            </div>
          </section>
        </div>
      </main>
    );
  }

  const style = applyPresentationTheme(presentation);

  return (
    <main
      className={styles.studyRoom}
      style={style}
      aria-label={`${world.name} private study room`}
    >
      <div className={styles.studyShell}>
        <header className={styles.studyTopbar}>
          <div className={styles.brand} aria-label="EasyChatBot">
            <div className={styles.brandMark} aria-hidden="true">
              💬
            </div>
            <div className={styles.brandCopy}>
              <strong>EasyChatBot</strong>
              <span>Growing With You.</span>
            </div>
          </div>

          <div className={styles.worldBadge}>
            <span aria-hidden="true">{presentation.flag}</span>
            <span>{presentation.name}</span>
          </div>
        </header>

        <section className={styles.hero}>
          <div className={styles.heroContent}>
            <p className={styles.eyebrow}>EasyChatBot · Study Mode</p>
            <h1>{presentation.name}</h1>
            <p className={styles.heroSubtitle}>
              {presentation.subtitle}
            </p>

            <div className={styles.heroTags}>
              {presentation.decorative.map((item) => (
                <span
                  className={styles.heroTag}
                  key={item}
                >
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className={styles.heroCompanion}>
            <span className={styles.companionCaption}>
              {presentation.companionName}
            </span>
            <div
              className={styles.companionHalo}
              aria-hidden="true"
            />
            <div
              className={styles.companionPlaceholder}
              aria-label={presentation.companionRole}
              title={presentation.companionRole}
            >
              {presentation.flag}
            </div>
          </div>
        </section>

        <div className={styles.workspace}>
          <section className={styles.chatPanel}>
            <header className={styles.chatHeader}>
              <div className={styles.chatHeaderIdentity}>
                <div className={styles.avatar}>
                  {presentation.flag}
                </div>
                <div>
                  <strong>{presentation.companionName}</strong>
                  <span>{presentation.companionRole}</span>
                </div>
              </div>

              <span className={styles.chatHeaderBadge}>
                Private chat
              </span>
            </header>

            {loadingConversation && (
              <p
                className={styles.status}
                role="status"
              >
                Creating your private conversation…
              </p>
            )}

            {error && (
              <p
                className={styles.error}
                role="alert"
              >
                {error}
              </p>
            )}

            <section
              className={styles.messages}
              aria-label="Conversation"
            >
              {messages.length === 0 &&
                !loadingConversation && (
                  <div className={styles.messageRow}>
                    <article className={styles.message}>
                      <div className={styles.messageMeta}>
                        {presentation.companionName}
                      </div>
                      <p className={styles.messageText}>
                        Let&apos;s learn together. Choose a study
                        prompt or write your own message to begin.
                      </p>
                    </article>
                  </div>
                )}

              {messages.map((message) => (
                <div
                  className={`${styles.messageRow} ${
                    message.role === "user"
                      ? styles.messageRowUser
                      : ""
                  }`}
                  key={message.id}
                >
                  <article
                    className={`${styles.message} ${
                      message.role === "user"
                        ? styles.messageUser
                        : ""
                    }`}
                    aria-label={message.role}
                  >
                    <div className={styles.messageMeta}>
                      {message.role === "user"
                        ? "You"
                        : presentation.companionName}
                    </div>
                    <p className={styles.messageText}>
                      {message.content}
                    </p>
                  </article>
                </div>
              ))}
            </section>

            <form
              className={styles.composer}
              onSubmit={handleSubmit}
            >
              <div className={styles.composerRow}>
                <textarea
                  className={styles.textarea}
                  id="private-chat-message"
                  value={draft}
                  onChange={(event) =>
                    setDraft(event.target.value)
                  }
                  disabled={
                    loadingConversation ||
                    !conversationId ||
                    sending
                  }
                  rows={3}
                  maxLength={10000}
                  placeholder={`Write a message in ${world.name}…`}
                  aria-label="Message"
                />

                <button
                  className={styles.sendButton}
                  type="submit"
                  disabled={
                    loadingConversation ||
                    !conversationId ||
                    sending ||
                    !draft.trim()
                  }
                >
                  {sending ? "Sending…" : "Send"}
                </button>
              </div>

              <p className={styles.helper}>
                Enter to send · Shift + Enter for a new line
              </p>
            </form>
          </section>

          <aside
            className={styles.studyPanel}
            aria-label="Study prompts"
          >
            <h2>Study with me</h2>
            <p className={styles.studyLead}>
              Start with a guided prompt or ask anything about
              this World.
            </p>

            <div className={styles.promptList}>
              {presentation.prompts.map((prompt) => (
                <button
                  className={styles.promptButton}
                  type="button"
                  key={prompt}
                  onClick={() => usePrompt(prompt)}
                  disabled={
                    loadingConversation ||
                    !conversationId ||
                    sending
                  }
                >
                  {prompt}
                </button>
              ))}
            </div>

            <div className={styles.studyDivider} />

            <div className={styles.studyFacts}>
              <div className={styles.studyFact}>
                <strong>World</strong>
                <span>{world.name}</span>
              </div>

              <div className={styles.studyFact}>
                <strong>Language</strong>
                <span>
                  {presentation.languageCode.toUpperCase()}
                </span>
              </div>

              <div className={styles.studyFact}>
                <strong>Conversation</strong>
                <span>
                  Private and owned by the authenticated learner.
                </span>
              </div>
            </div>
          </aside>
        </div>

        <footer className={styles.footer}>
          <span>EasyChatBot · One core experience. Many Worlds.</span>
          <span>{presentation.name} · Study Mode</span>
        </footer>
      </div>
    </main>
  );
}
