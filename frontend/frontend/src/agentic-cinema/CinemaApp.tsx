import { Component, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import styles from "./CinemaApp.module.css";
import {
  runCinema,
  runCinemaAction,
  type CinemaResult,
} from "./cinemaApi";

type CinemaErrorBoundaryProps = {
  children: ReactNode;
};

type CinemaErrorBoundaryState = {
  hasError: boolean;
  message: string;
};

class CinemaErrorBoundary extends Component<
  CinemaErrorBoundaryProps,
  CinemaErrorBoundaryState
> {
  state: CinemaErrorBoundaryState = { hasError: false, message: "" };

  static getDerivedStateFromError(error: unknown): CinemaErrorBoundaryState {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : "Unknown Cinema render error.",
    };
  }

  componentDidCatch(error: unknown) {
    console.error("[Agentic Cinema] render error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <section style={{ padding: "48px", maxWidth: "900px", margin: "0 auto" }}>
          <h1>Agentic Cinema could not render this screen.</h1>
          <p>The Cinema application caught a UI rendering error instead of going blank.</p>
          <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{this.state.message}</pre>
          <button type="button" onClick={() => this.setState({ hasError: false, message: "" })}>
            Try again
          </button>
        </section>
      );
    }

    return this.props.children;
  }
}

type View =
  | "home"
  | "chat"
  | "results"
  | "challenge"
  | "academy"
  | "recommendations"
  | "profile";

const LUMINATE_IMAGE = "/characters/luminate/Luminate-template.png";

const prompts = [
  "What are the most important developments in the film industry this week?",
  "What are critics saying about the latest cinema trends?",
  "What streaming trends should filmmakers watch this month?",
  "Recommend a French-language film topic for me.",
  "Explain a current film-industry story in simple French.",
];

type TimedFlashcard = {
  id: string;
  provider: "Shopping Center" | "French Market";
  eyebrow: string;
  title: string;
  message: string;
  cta: string;
  icon: string;
  imageSrc: string;
};

const CINEMA_FLASHCARDS: TimedFlashcard[] = [
  {
    id: "iphone-yeti-deal",
    provider: "Shopping Center",
    eyebrow: "YETI RECOMMENDS · MEMORY PICK",
    title: "Yeti's iPhone Deal",
    message:
      "A memory-informed shopping discovery is ready. Explore Yeti's French-learning vocabulary and the featured offer.",
    cta: "Explore Shopping Center",
    icon: "✦",
    imageSrc: "/cinema/flashcards/Yeti-iphone-deal.png",
  },
  {
    id: "yeti-french-market",
    provider: "French Market",
    eyebrow: "YETI RECOMMENDS · MEMORY PICK",
    title: "Yeti's French Market Pick",
    message:
      "A second memory-informed recommendation is ready: explore the French Market flashcard and learn useful vocabulary while discovering the offer.",
    cta: "Explore French Market",
    icon: "✦",
    imageSrc: "/cinema/flashcards/Yeti-French-Market-Flashcard.png",
  },
];

export function CinemaApp() {
  const [view, setView] = useState<View>("home");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CinemaResult | null>(null);
  const [saved, setSaved] = useState(
    () =>
      window.localStorage.getItem("easychatbot.cinema.saved") === "true",
  );
  const [actionMessage, setActionMessage] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [flashcards, setFlashcards] = useState<TimedFlashcard[]>([]);
  const [activeFlashcard, setActiveFlashcard] =
    useState<TimedFlashcard | null>(null);

  useEffect(() => {
    let index = 0;

    const showNextFlashcard = () => {
      const card = CINEMA_FLASHCARDS[index % CINEMA_FLASHCARDS.length];
      index += 1;

      setFlashcards((current) =>
        current.some((item) => item.id === card.id)
          ? current
          : [...current, card],
      );
      setActiveFlashcard(card);
    };

    const timer = window.setInterval(showNextFlashcard, 20_000);

    return () => window.clearInterval(timer);
  }, []);

  function dismissFlashcard(id: string) {
    setActiveFlashcard((current) =>
      current?.id === id ? null : current,
    );
  }

  function openFlashcardRecommendations() {
    setActiveFlashcard(null);
    setNotificationsOpen(false);
    navigate("recommendations");
  }

  const intelligenceText = useMemo(() => {
    if (!result) {
      return "";
    }

    const candidate =
      result.intelligence ?? result.summary ?? result.result ?? "";

    if (typeof candidate === "string") {
      return candidate;
    }

    if (candidate == null) {
      return "";
    }

    try {
      return JSON.stringify(candidate, null, 2);
    } catch {
      return String(candidate);
    }
  }, [result]);

  async function executeCinema(question = message) {
    const clean = question.trim();

    if (!clean || loading) {
      return;
    }

    setMessage(clean);
    setLoading(true);
    setResult(null);
    setActionMessage("");

    // Keep the user on the stable Chat screen while the long-running
    // Agent Runtime workflow executes. Only transition to Results after
    // the request has completed, so there is never an empty intermediate
    // screen during the live Parallel + Gemini workflow.
    setView("chat");

    try {
      const data = await runCinema(clean);
      setResult(data);
      setLoading(false);
      setView("results");
    } catch (error) {
      setResult({
        success: false,
        error:
          error instanceof Error
            ? error.message
            : "Unable to reach the cinema service.",
      });
      setLoading(false);
      setView("results");
    }
  }

  function openChat(prefill = "") {
    setMessage(prefill);
    setResult(null);
    setActionMessage("");
    setView("chat");
  }

  function navigate(next: View) {
    setView(next);

    if (next !== "profile") {
      setProfileOpen(false);
    }
  }

  async function saveResult() {
    if (!result || saved) {
      return;
    }

    try {
      const response = await runCinemaAction("save", {
        user_id: "hackathon-judge",
        result,
      });

      if (response.success === false) {
        throw new Error(
          response.error || "The save service could not complete the action.",
        );
      }

      window.localStorage.setItem(
        "easychatbot.cinema.saved",
        "true",
      );

      setSaved(true);
      setActionMessage("Saved to your Cinema learning journey.");
    } catch {
      // Keep the demo journey functional even if the optional
      // persistence endpoint is unavailable.
      window.localStorage.setItem(
        "easychatbot.cinema.saved",
        "true",
      );

      setSaved(true);
      setActionMessage("Saved on this device.");
    }
  }

  function shareResult() {
    const text = intelligenceText.slice(0, 900);

    if (
      typeof navigator !== "undefined" &&
      typeof navigator.share === "function"
    ) {
      navigator
        .share({
          title: "EasyChatBot · Agentic Cinema",
          text,
        })
        .catch(() => undefined);

      return;
    }

    if (
      typeof navigator !== "undefined" &&
      navigator.clipboard
    ) {
      navigator.clipboard
        .writeText(text)
        .then(() => setActionMessage("Result copied to clipboard."))
        .catch(() => undefined);
    }
  }

  function renderView(): ReactNode {
    switch (view) {
      case "home":
        return (
          <HomeScreen
            onStart={() => openChat()}
            onPrompt={(prompt) => openChat(prompt)}
            onAcademy={() => navigate("academy")}
            onRecommendations={() => navigate("recommendations")}
          />
        );

      case "chat":
        return (
          <ChatScreen
            message={message}
            setMessage={setMessage}
            loading={loading}
            onRun={() => executeCinema()}
            onPrompt={(prompt) => setMessage(prompt)}
            onBack={() => navigate("home")}
          />
        );

      case "results":
        return (
          <ResultsScreen
            question={message}
            loading={loading}
            result={result}
            intelligenceText={intelligenceText}
            saved={saved}
            actionMessage={actionMessage}
            onBack={() => navigate("chat")}
            onChallenge={() => navigate("challenge")}
            onSave={saveResult}
            onShare={shareResult}
            onRunAgain={() => navigate("chat")}
          />
        );

      case "challenge":
        return (
          <ChallengeScreen
            result={result}
            onBack={() => navigate("results")}
          />
        );

      case "academy":
        return (
          <AcademyScreen
            saved={saved}
            onBack={() => navigate("home")}
          />
        );

      case "recommendations":
        return (
          <RecommendationsScreen
            onBack={() => navigate("home")}
          />
        );

      case "profile":
        return (
          <ProfileScreen
            onBack={() => navigate("home")}
          />
        );

      default:
        return (
          <HomeScreen
            onStart={() => openChat()}
            onPrompt={(prompt) => openChat(prompt)}
            onAcademy={() => navigate("academy")}
            onRecommendations={() => navigate("recommendations")}
          />
        );
    }
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <Brand />

        <nav
          className={styles.sideNav}
          aria-label="Primary navigation"
        >
          <NavButton
            active={view === "home"}
            icon="⌂"
            label="Home"
            onClick={() => (loading ? openChat() : navigate("home"))}
          />

          <NavButton
            active={
              view === "chat" ||
              view === "results" ||
              view === "challenge"
            }
            icon="○"
            label="Chat"
            onClick={() => openChat()}
          />

          <NavButton
            active={view === "home"}
            icon="✦"
            label="Agentic Cinema"
            onClick={() => navigate("home")}
            accent
          />

          <NavButton
            active={view === "academy"}
            icon="♜"
            label="Academy"
            onClick={() => navigate("academy")}
          />

          <NavButton
            active={view === "academy"}
            icon="◫"
            label="Progress"
            onClick={() => navigate("academy")}
          />

          <NavButton
            active={view === "academy"}
            icon="✧"
            label="Memory"
            onClick={() => navigate("academy")}
          />

          <NavButton
            active={view === "recommendations"}
            icon="☆"
            label="Recommendations"
            onClick={() => navigate("recommendations")}
          />

          <NavButton
            icon="♧"
            label="Notifications"
            badge={String(5 + flashcards.length)}
            onClick={() => setNotificationsOpen(true)}
          />

          <NavButton
            active={view === "profile"}
            icon="♙"
            label="Profile"
            onClick={() => navigate("profile")}
          />

          <NavButton
            icon="⚙"
            label="Settings"
            onClick={() => setProfileOpen(true)}
          />
        </nav>

        <ProfileMini onClick={() => navigate("profile")} />
      </aside>

      <main className={styles.main}>
        <header className={styles.topbar}>
          <button
            type="button"
            className={styles.mobileBrand}
            onClick={() => navigate("home")}
          >
            ✦ EasyChatBot
          </button>

          <div className={styles.topActions}>
            <button
              type="button"
              className={styles.academyPill}
              onClick={() => navigate("academy")}
            >
              ♜ Your Academy
            </button>

            <button
              type="button"
              className={styles.iconButton}
              aria-label="Notifications"
              onClick={() => setNotificationsOpen(true)}
            >
              ♧
              <span>{5 + flashcards.length}</span>
            </button>

            <button
              type="button"
              className={styles.avatarButton}
              onClick={() => navigate("profile")}
            >
              L
            </button>
          </div>
        </header>

        <div>
          <CinemaErrorBoundary>{renderView()}</CinemaErrorBoundary>
        </div>

        {notificationsOpen && (
          <div
            className={styles.modalBackdrop}
            role="presentation"
            onClick={() => setNotificationsOpen(false)}
          >
            <section
              className={styles.notificationPanel}
              role="dialog"
              aria-modal="true"
              aria-labelledby="notifications-title"
              onClick={(event) => event.stopPropagation()}
            >
              <div className={styles.modalHeader}>
                <div>
                  <span className={styles.eyebrow}>
                    ACADEMY
                  </span>

                  <h2 id="notifications-title">
                    Notifications
                  </h2>
                </div>

                <button
                  type="button"
                  onClick={() => setNotificationsOpen(false)}
                  className={styles.closeButton}
                  aria-label="Close notifications"
                >
                  ×
                </button>
              </div>

              <div className={styles.notificationItem}>
                <span>✦</span>

                <div>
                  <strong>New Cinema Mission</strong>

                  <p>
                    Run a live intelligence workflow and turn
                    the result into French practice.
                  </p>
                </div>
              </div>

              <div className={styles.notificationItem}>
                <span>♜</span>

                <div>
                  <strong>Academy Progress</strong>

                  <p>
                    Your B2 cinema-learning journey is ready
                    for the next step.
                  </p>
                </div>
              </div>

              <div className={styles.notificationItem}>
                <span>✧</span>

                <div>
                  <strong>Memory</strong>

                  <p>
                    Save a completed intelligence result to
                    continue your personalised journey.
                  </p>
                </div>
              </div>

              {flashcards.map((card) => (
                <button
                  key={card.id}
                  type="button"
                  className={styles.notificationRecommendation}
                  onClick={openFlashcardRecommendations}
                >
                  <span>{card.icon}</span>
                  <div>
                    <strong>{card.title}</strong>
                    <p>
                      {card.provider} recommendation · personalised
                      from your Cinema profile.
                    </p>
                  </div>
                  <b>→</b>
                </button>
              ))}

              <button
                type="button"
                className={styles.primaryButtonSmall}
                onClick={() => {
                  setNotificationsOpen(false);
                  openChat();
                }}
              >
                Start a Mission →
              </button>
            </section>
          </div>
        )}

        {activeFlashcard && (
          <FlashcardToast
            card={activeFlashcard}
            onOpen={openFlashcardRecommendations}
            onDismiss={() => dismissFlashcard(activeFlashcard.id)}
          />
        )}

        {profileOpen && (
          <div className={styles.toast}>
            <strong>Settings</strong>

            <span>
              Configuration remains in the application/backend
              layer.
            </span>

            <button
              type="button"
              onClick={() => setProfileOpen(false)}
            >
              Close
            </button>
          </div>
        )}
      </main>

      <MobileNav
        view={view}
        onNavigate={navigate}
      />
    </div>
  );
}

function FlashcardToast({
  card,
  onOpen,
  onDismiss,
}: {
  card: TimedFlashcard;
  onOpen: () => void;
  onDismiss: () => void;
}) {
  return (
    <div className={styles.cinemaFlashcardLayer}>
      <div className={styles.cinemaFlashcardBackdrop} aria-hidden="true" />

      <aside
        className={styles.flashcardToast}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cinema-flashcard-title"
        aria-describedby="cinema-flashcard-message"
      >
        <div className={styles.flashcardVisual}>
          <img
            src={card.imageSrc}
            alt=""
            className={styles.flashcardImage}
          />
        </div>

        <div className={styles.flashcardContent}>
          <button
            type="button"
            className={styles.flashcardClose}
            onClick={onDismiss}
            aria-label="Close recommendation"
          >
            ×
          </button>

          <span className={styles.flashcardEyebrow}>
            {card.eyebrow}
          </span>

          <h2 id="cinema-flashcard-title">{card.title}</h2>

          <p id="cinema-flashcard-message">{card.message}</p>

          <div className={styles.flashcardActions}>
            <button
              type="button"
              className={styles.primaryButtonSmall}
              onClick={onOpen}
            >
              {card.cta} →
            </button>

            <button
              type="button"
              className={styles.flashcardDismiss}
              onClick={onDismiss}
            >
              Later
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
}

function HomeScreen({
  onStart,
  onPrompt,
  onAcademy,
  onRecommendations,
}: {
  onStart: () => void;
  onPrompt: (prompt: string) => void;
  onAcademy: () => void;
  onRecommendations: () => void;
}) {
  return (
    <section className={styles.content}>
      <div className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}>
            ✦ EASYCHATBOT · LIVING AI WORLD
          </span>

          <h1>
            AGENTIC <em>CINEMA</em>
          </h1>

          <p>
            Live intelligence. Real stories. Your AI research
            crew for the studio.
          </p>

          <div className={styles.capabilities}>
            <span>✓ Real-time research with Parallel</span>
            <span>✓ AI reasoning with Gemini</span>
            <span>✓ Personalised to your learning profile</span>
            <span>✓ Turn insights into learning</span>
          </div>

          <div className={styles.heroActions}>
            <button
              type="button"
              className={styles.primaryButton}
              onClick={onStart}
            >
              Start Exploring →
            </button>

            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() =>
                onPrompt(
                  "What are the most important developments in the film industry this week?",
                )
              }
            >
              ▷ Try a question
            </button>
          </div>
        </div>

        <CharacterArt />
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <span className={styles.eyebrow}>
            YOUR CINEMA CREW
          </span>

          <h2>Choose where to explore</h2>
        </div>
      </div>

      <div className={styles.featureGrid}>
        <FeatureCard
          icon="▣"
          title="Movies & TV"
          text="Latest news and analysis"
          onClick={() =>
            onPrompt(
              "What are the biggest current movies and TV developments?",
            )
          }
        />

        <FeatureCard
          icon="♜"
          title="Industry Trends"
          text="Business, streaming & awards"
          onClick={() =>
            onPrompt(
              "What industry trends should filmmakers watch right now?",
            )
          }
        />

        <FeatureCard
          icon="♡"
          title="Personalised Picks"
          text="Music & video for your profile"
          onClick={() => onRecommendations()}
        />

        <FeatureCard
          icon="☷"
          title="Learn & Grow"
          text="Turn insights into French practice"
          onClick={() =>
            onPrompt(
              "Give me a current film-industry story I can practise in French.",
            )
          }
        />
      </div>

      <div className={styles.lowerGrid}>
        <Panel title="Today's Mission ✨">
          <p>
            Complete a real conversation with your Cinema
            Intelligence Agent.
          </p>

          <button
            type="button"
            className={styles.primaryButtonSmall}
            onClick={onStart}
          >
            Start Mission ▶
          </button>
        </Panel>

        <Panel title="Academy Progress ☀">
          <div className={styles.progressRow}>
            <span>French World · B2</span>
            <strong>68%</strong>
          </div>

          <div className={styles.progress}>
            <i style={{ width: "68%" }} />
          </div>

          <button
            type="button"
            className={styles.linkButton}
            onClick={onAcademy}
          >
            View Academy →
          </button>
        </Panel>

        <Panel title="Luminate's Pick ☆">
          <p>
            “Great content sparks ideas and opens new worlds.”
          </p>

          <button
            type="button"
            className={styles.linkButton}
            onClick={() =>
              onPrompt(
                "What current story would you recommend for my learning journey?",
              )
            }
          >
            Explore Pick →
          </button>
        </Panel>
      </div>
    </section>
  );
}

function ChatScreen({
  message,
  setMessage,
  loading,
  onRun,
  onPrompt,
  onBack,
}: {
  message: string;
  setMessage: (value: string) => void;
  loading: boolean;
  onRun: () => void;
  onPrompt: (prompt: string) => void;
  onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        type="button"
        className={styles.backButton}
        onClick={onBack}
        disabled={loading}
        aria-disabled={loading}
      >
        {loading ? "Research in progress…" : "← Back"}
      </button>

      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>✦</span>

        <div>
          <span className={styles.eyebrow}>
            AGENTIC CINEMA
          </span>

          <h1>
            Ask your Cinema Intelligence Agent
          </h1>
        </div>
      </div>

      {loading ? (
        <div className={styles.loadingCard} aria-live="polite">
          <div className={styles.spinner} />

          <h2>Your research crew is working…</h2>

          <p>
            Searching live sources with Parallel, analysing with Gemini,
            and preparing your personalised learning result.
          </p>

          <div className={styles.loadingSteps}>
            <span>✓ Live research</span>
            <span>✓ Gemini analysis</span>
            <span>◌ Personalisation</span>
          </div>

          <p>
            You can stay on this screen. The result will appear automatically
            when the workflow is complete.
          </p>
        </div>
      ) : (
        <div className={styles.chatCard}>
          <div className={styles.messageAgent}>
          <CharacterAvatar />

          <div>
            <strong>
              Luminate · Cinema Intelligence
            </strong>

            <p>
              Hi! I’m your Cinema Intelligence Agent.
              Ask me anything about movies, TV, the film
              industry, or a current story you want to
              understand.
            </p>
          </div>
        </div>

        <div className={styles.promptList}>
          {prompts.map((prompt) => (
            <button
              type="button"
              key={prompt}
              onClick={() => onPrompt(prompt)}
            >
              {prompt}
              <span>→</span>
            </button>
          ))}
        </div>

        <div className={styles.composer}>
          <textarea
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();
                onRun();
              }
            }}
            placeholder="Ask anything about movies, TV, or the industry…"
            rows={3}
          />

          <button
            type="button"
            className={styles.sendButton}
            onClick={onRun}
            disabled={loading || !message.trim()}
            aria-label="Send question"
          >
            {loading ? "…" : "➤"}
          </button>
        </div>

          <div className={styles.trustLine}>
            Secure application boundary · Gemini reasoning ·
            Parallel live research · No browser-side secrets
          </div>
        </div>
      )}
    </section>
  );
}

function ResultsScreen({
  question,
  loading,
  result,
  intelligenceText,
  saved,
  actionMessage,
  onBack,
  onChallenge,
  onSave,
  onShare,
  onRunAgain,
}: {
  question: string;
  loading: boolean;
  result: CinemaResult | null;
  intelligenceText: string;
  saved: boolean;
  actionMessage: string;
  onBack: () => void;
  onChallenge: () => void;
  onSave: () => void;
  onShare: () => void;
  onRunAgain: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        type="button"
        className={styles.backButton}
        onClick={onBack}
      >
        ← Ask another question
      </button>

      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>✦</span>

        <div>
          <span className={styles.eyebrow}>
            AGENTIC CINEMA · RESULT
          </span>

          <h1>
            Your personalised cinema intelligence
          </h1>
        </div>
      </div>

      <div className={styles.statusBar}>
        <span>● Parallel</span>
        <span>● Gemini</span>
        <span>● Memory</span>
        <span>● Personalisation</span>
      </div>

      {loading && (
        <div
          className={styles.loadingCard}
          aria-live="polite"
        >
          <div className={styles.spinner} />

          <h2>
            Your research crew is working…
          </h2>

          <p>
            Searching live sources with Parallel,
            analysing with Gemini, and preparing your
            personalised learning result.
          </p>

          <div className={styles.loadingSteps}>
            <span>✓ Live research</span>
            <span>✓ Gemini analysis</span>
            <span>◌ Personalisation</span>
          </div>
        </div>
      )}

      {!loading && result?.error && (
        <div className={styles.errorCard}>
          <strong>
            The cinema service could not complete the
            request.
          </strong>

          <p>{result.error}</p>

          <button
            type="button"
            className={styles.primaryButtonSmall}
            onClick={onRunAgain}
          >
            Try Again
          </button>
        </div>
      )}

      {!loading && result && !result.error && (
        <article className={styles.resultCard}>
          <div className={styles.resultHeader}>
            <div>
              <span className={styles.resultTag}>
                LIVE INTELLIGENCE
              </span>

              <h2>
                {question || "Cinema Intelligence"}
              </h2>

              <small>
                Generated from the connected application
                workflow
              </small>
            </div>

            <span className={styles.liveBadge}>
              LIVE
            </span>
          </div>

          <div className={styles.resultBody}>
            {intelligenceText
              .split(/\n+/)
              .filter(Boolean)
              .map((line, index) => (
                <p key={`${index}-${line}`}>
                  {line}
                </p>
              ))}
          </div>

          {result.sources &&
            result.sources.length > 0 && (
              <div className={styles.sources}>
                <h3>Research sources</h3>

                {result.sources.map((source, index) => (
                  <a
                    key={`${source.title}-${index}`}
                    href={source.url || "#"}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <span>{index + 1}</span>

                    <strong>{source.title}</strong>

                    <small>
                      {source.snippet ||
                        "Live source used by the workflow"}
                    </small>

                    →
                  </a>
                ))}
              </div>
            )}

          <div className={styles.resultActions}>
            <button
              type="button"
              className={styles.primaryButtonSmall}
              onClick={onChallenge}
            >
              Turn this into a learning challenge →
            </button>

            <button
              type="button"
              className={styles.secondaryButtonSmall}
              onClick={onSave}
            >
              {saved
                ? "✓ Saved on this device"
                : "☆ Save on this device"}
            </button>

            <button
              type="button"
              className={styles.secondaryButtonSmall}
              onClick={() => window.print()}
            >
              PDF / Print
            </button>

            <button
              type="button"
              className={styles.secondaryButtonSmall}
              onClick={onShare}
            >
              Share
            </button>
          </div>

          {actionMessage && (
            <div
              className={styles.actionMessage}
              role="status"
            >
              {actionMessage}
            </div>
          )}
        </article>
      )}
    </section>
  );
}

function ChallengeScreen({
  result,
  onBack,
}: {
  result: CinemaResult | null;
  onBack: () => void;
}) {
  const challenge = result?.learning_challenge;

  const [answer, setAnswer] = useState("");
  const [checked, setChecked] = useState(false);
  const [checking, setChecking] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [hintOpen, setHintOpen] = useState(false);

  async function checkAnswer() {
    if (!answer.trim()) {
      return;
    }

    setChecking(true);

    try {
      const response = await runCinemaAction(
        "challenge",
        {
          user_id: "hackathon-judge",
          answer,
          challenge: challenge ?? null,
        },
      );

      setChecked(true);

      setFeedback(
        response.feedback ||
          (response.success
            ? "Answer evaluated by the connected application."
            : "Evaluation endpoint is not configured yet."),
      );
    } catch {
      setChecked(true);
      setFeedback(
        "The evaluation service could not be reached.",
      );
    } finally {
      setChecking(false);
    }
  }

  return (
    <section className={styles.contentNarrow}>
      <button
        type="button"
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back to intelligence
      </button>

      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>☷</span>

        <div>
          <span className={styles.eyebrow}>
            LEARNING CHALLENGE · B2
          </span>

          <h1>
            Turn real-world insight into progress
          </h1>
        </div>
      </div>

      <div className={styles.challengeCard}>
        <div className={styles.challengeHeader}>
          <span>✦ Learning Challenge</span>
          <b>B1 · B2</b>
        </div>

        <p className={styles.challengeIntro}>
          Based on today's live intelligence, practise
          your French with the real content you just
          explored.
        </p>

        <div className={styles.task}>
          <span>▣ TASK</span>

          <h2>
            {challenge?.prompt ||
              "Summarise the main development in French in 4–6 sentences."}
          </h2>

          <textarea
            value={answer}
            onChange={(event) =>
              setAnswer(event.target.value)
            }
            placeholder="Write your answer in French…"
            maxLength={500}
          />

          <div className={styles.answerMeta}>
            {answer.length}/500
          </div>

          <div className={styles.challengeActions}>
            <button
              type="button"
              className={styles.primaryButtonSmall}
              onClick={checkAnswer}
              disabled={
                checking || !answer.trim()
              }
            >
              {checking
                ? "Checking…"
                : "Check My Answer →"}
            </button>

            <button
              type="button"
              className={styles.secondaryButtonSmall}
              onClick={() =>
                setHintOpen((value) => !value)
              }
            >
              💡 {hintOpen ? "Hide hint" : "Get a hint"}
            </button>
          </div>

          {hintOpen && (
            <div className={styles.hint}>
              💡 Try using:{" "}
              {(
                challenge?.vocabulary || [
                  "production",
                  "industrie",
                  "innovation",
                ]
              )
                .slice(0, 3)
                .join(" · ")}
              .
            </div>
          )}

          {checked && (
            <div className={styles.feedback}>
              ✓ {feedback || "Answer received."}
            </div>
          )}
        </div>

        <div className={styles.vocabulary}>
          <h3>Useful vocabulary</h3>

          <div>
            {(
              challenge?.vocabulary || [
                "festival",
                "catégorie",
                "production",
                "industrie",
                "innovation",
                "créativité",
              ]
            ).map((word) => (
              <span key={word}>{word}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}


type Recommendation = {
  title: string;
  subtitle: string;
  reason: string;
  tags: string[];
  kind: "spotify" | "youtube";
  query: string;
};

const spotifyRecommendations: Recommendation[] = [
  {
    title: "French Cinema Soundtracks",
    subtitle: "Spotify · curated listening",
    reason:
      "Build French listening familiarity through the music and atmosphere surrounding French cinema.",
    tags: ["French", "Cinema", "Listening"],
    kind: "spotify",
    query: "French cinema soundtracks",
  },
  {
    title: "Film Scores & Storytelling",
    subtitle: "Spotify · instrumental focus",
    reason:
      "Explore how score, mood and storytelling connect — a natural extension of your film-industry interests.",
    tags: ["Film", "Scores", "Storytelling"],
    kind: "spotify",
    query: "film scores cinematic music",
  },
  {
    title: "French Culture & Cinema Podcasts",
    subtitle: "Spotify · spoken French",
    reason:
      "A B2-friendly way to practise sustained listening while staying inside your cinema and culture interests.",
    tags: ["B2", "French", "Culture"],
    kind: "spotify",
    query: "French cinema podcast culture",
  },
];

const youtubeRecommendations: Recommendation[] = [
  {
    title: "French Cinema Analysis",
    subtitle: "YouTube · video learning",
    reason:
      "Watch film discussion in French to connect cultural knowledge with practical B2 listening.",
    tags: ["B2", "French", "Analysis"],
    kind: "youtube",
    query: "French cinema analysis film",
  },
  {
    title: "Film Industry & Streaming",
    subtitle: "YouTube · industry intelligence",
    reason:
      "Follow current conversations around streaming and the film business, matching your industry interests.",
    tags: ["Industry", "Streaming", "Trends"],
    kind: "youtube",
    query: "film industry streaming trends",
  },
  {
    title: "Filmmaking Interviews",
    subtitle: "YouTube · creators & craft",
    reason:
      "Hear filmmakers explain their work and pick up authentic professional vocabulary.",
    tags: ["Filmmaking", "Vocabulary", "Listening"],
    kind: "youtube",
    query: "filmmaker interview French cinema",
  },
];

function RecommendationsScreen({
  onBack,
}: {
  onBack: () => void;
}) {
  function openRecommendation(item: Recommendation) {
    const encoded = encodeURIComponent(item.query);
    const url =
      item.kind === "spotify"
        ? `https://open.spotify.com/search/${encoded}`
        : `https://www.youtube.com/results?search_query=${encoded}`;

    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <section className={styles.content}>
      <button
        type="button"
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back to Cinema
      </button>

      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>☆</span>

        <div>
          <span className={styles.eyebrow}>
            MEMORY-INFORMED RECOMMENDATIONS
          </span>

          <h1>Your Cinema Shelf</h1>
        </div>
      </div>

      <div className={styles.recommendationIntro}>
        <div>
          <strong>Picked for your learning journey.</strong>
          <p>
            Your current profile combines French B2 learning with
            cinema, film-industry, streaming and cultural interests.
            These recommendations turn those interests into listening
            and viewing practice.
          </p>
        </div>

        <div className={styles.recommendationMemory}>
          <span>✧ MEMORY</span>
          <strong>French · B2 · Cinema Explorer</strong>
          <small>
            Personalisation is based on the learner profile currently
            available to the Cinema experience.
          </small>
        </div>
      </div>

      <div className={styles.recommendationSection}>
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.eyebrow}>LISTEN</span>
            <h2>Spotify recommendations</h2>
          </div>
          <span className={styles.recommendationProvider}>
            Spotify search
          </span>
        </div>

        <div className={styles.recommendationGrid}>
          {spotifyRecommendations.map((item) => (
            <RecommendationCard
              key={item.title}
              item={item}
              onOpen={() => openRecommendation(item)}
            />
          ))}
        </div>
      </div>

      <div className={styles.recommendationSection}>
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.eyebrow}>WATCH</span>
            <h2>YouTube recommendations</h2>
          </div>
          <span className={styles.recommendationProvider}>
            YouTube search
          </span>
        </div>

        <div className={styles.recommendationGrid}>
          {youtubeRecommendations.map((item) => (
            <RecommendationCard
              key={item.title}
              item={item}
              onOpen={() => openRecommendation(item)}
            />
          ))}
        </div>
      </div>

      <div className={styles.recommendationNote}>
        <span>✦</span>
        <div>
          <strong>Why these are personalised</strong>
          <p>
            The screen uses the Cinema learner profile as its current
            memory signal. Later, the same recommendation contract can
            consume persisted memory records and agent-generated
            recommendations without changing the UI boundary.
          </p>
        </div>
      </div>
    </section>
  );
}

function RecommendationCard({
  item,
  onOpen,
}: {
  item: Recommendation;
  onOpen: () => void;
}) {
  const spotify = item.kind === "spotify";

  return (
    <article className={styles.recommendationCard}>
      <div
        className={`${styles.recommendationLogo} ${
          spotify
            ? styles.recommendationSpotify
            : styles.recommendationYoutube
        }`}
        aria-hidden="true"
      >
        {spotify ? "♫" : "▶"}
      </div>

      <div className={styles.recommendationBody}>
        <span className={styles.recommendationKind}>
          {item.subtitle}
        </span>

        <h3>{item.title}</h3>

        <p>{item.reason}</p>

        <div className={styles.recommendationTags}>
          {item.tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>

        <button
          type="button"
          className={styles.primaryButtonSmall}
          onClick={onOpen}
        >
          Open recommendation →
        </button>
      </div>
    </article>
  );
}

function AcademyScreen({
  saved,
  onBack,
}: {
  saved: boolean;
  onBack: () => void;
}) {
  return (
    <section className={styles.content}>
      <button
        type="button"
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>♜</span>

        <div>
          <span className={styles.eyebrow}>
            YOUR ACADEMY
          </span>

          <h1>Saved cinema intelligence</h1>
        </div>
      </div>

      <div className={styles.academyGrid}>
        <Panel title="Memory">
          <strong className={styles.bigNumber}>
            {saved ? "13" : "12"}
          </strong>

          <p>
            Memories saved from your learning journey.
          </p>
        </Panel>

        <Panel title="Learning Progress">
          <strong className={styles.bigNumber}>
            68%
          </strong>

          <p>French World · B2</p>

          <div className={styles.progress}>
            <i style={{ width: "68%" }} />
          </div>
        </Panel>

        <Panel title="Current Mission">
          <strong>Real-world French</strong>

          <p>
            Use current cinema stories to build vocabulary
            and express opinions.
          </p>
        </Panel>
      </div>

      <div className={styles.savedBanner}>
        ✦{" "}
        {saved
          ? "Your latest intelligence has been saved on this device."
          : "Save a result locally to keep your current demo journey."}
      </div>
    </section>
  );
}

function ProfileScreen({
  onBack,
}: {
  onBack: () => void;
}) {
  const interests = [
    "Movies",
    "TV Series",
    "Film Industry",
    "French Cinema",
    "Streaming",
    "Animation",
    "Documentaries",
    "Awards",
  ];

  return (
    <section className={styles.contentNarrow}>
      <button
        type="button"
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>♙</span>

        <div>
          <span className={styles.eyebrow}>
            YOUR PROFILE
          </span>

          <h1>Personalisation</h1>
        </div>
      </div>

      <div className={styles.profileCard}>
        <div className={styles.profileHero}>
          <CharacterAvatar large />

          <div>
            <h2>Learner</h2>

            <p>French · B2 · Cinema Explorer</p>

            <div className={styles.progress}>
              <i style={{ width: "68%" }} />
            </div>
          </div>
        </div>

        <h3>Your interests</h3>

        <div className={styles.tags}>
          {interests.map((interest) => (
            <span key={interest}>{interest}</span>
          ))}
        </div>

        <h3>Learning goals</h3>

        <div className={styles.goalList}>
          <span>◉ Improve French (B2)</span>
          <span>◉ Discover new content</span>
          <span>◉ Learn industry vocabulary</span>
          <span>◉ Build cultural knowledge</span>
        </div>
      </div>
    </section>
  );
}

function Brand() {
  return (
    <div className={styles.brand}>
      <span className={styles.brandIcon}>✦</span>

      <div>
        <strong>EasyChatBot</strong>
        <em>Growing With You.</em>
      </div>
    </div>
  );
}

function CharacterArt() {
  return (
    <div className={styles.characterStage}>
      <div className={styles.stars} />
      <div className={styles.mountain} />

      <div className={styles.character}>
        <img
          src={LUMINATE_IMAGE}
          alt="Luminate, the Cinema Intelligence character"
          className={styles.characterImage}
        />
      </div>

      <div className={styles.characterQuote}>
        Great stories
        <br />
        start with
        <br />
        <em>curious minds.</em>
      </div>
    </div>
  );
}

function CharacterAvatar({
  large = false,
}: {
  large?: boolean;
}) {
  return (
    <span
      className={`${styles.characterAvatar} ${
        large ? styles.largeAvatar : ""
      }`}
    >
      <img
        src={LUMINATE_IMAGE}
        alt="Luminate"
        className={styles.avatarImage}
      />
    </span>
  );
}

function ProfileMini({
  onClick,
}: {
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={styles.profileMini}
      onClick={onClick}
    >
      <CharacterAvatar />

      <span>
        <strong>Learner</strong>
        <small>Level B2</small>
      </span>

      <span className={styles.xp}>
        <i />
      </span>

      <small>1,350 XP</small>
    </button>
  );
}

function NavButton({
  icon,
  label,
  active,
  accent,
  badge,
  onClick,
}: {
  icon: string;
  label: string;
  active?: boolean;
  accent?: boolean;
  badge?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`${styles.navButton} ${
        active ? styles.active : ""
      } ${accent ? styles.accent : ""}`}
      onClick={onClick}
    >
      <span>{icon}</span>
      {label}
      {badge && <b>{badge}</b>}
    </button>
  );
}

function FeatureCard({
  icon,
  title,
  text,
  onClick,
}: {
  icon: string;
  title: string;
  text: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={styles.featureCard}
      onClick={onClick}
    >
      <span>{icon}</span>
      <strong>{title}</strong>
      <small>{text}</small>
      <i>→</i>
    </button>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <article className={styles.panel}>
      <h3>{title}</h3>
      {children}
    </article>
  );
}

function MobileNav({
  view,
  onNavigate,
}: {
  view: View;
  onNavigate: (view: View) => void;
}) {
  return (
    <nav className={styles.mobileNav}>
      <button
        type="button"
        onClick={() => onNavigate("home")}
        className={
          view === "home"
            ? styles.mobileActive
            : ""
        }
      >
        ⌂
        <small>Home</small>
      </button>

      <button
        type="button"
        onClick={() => onNavigate("chat")}
        className={
          view === "chat" ||
          view === "results" ||
          view === "challenge"
            ? styles.mobileActive
            : ""
        }
      >
        ○
        <small>Chat</small>
      </button>

      <button
        type="button"
        onClick={() => onNavigate("academy")}
        className={
          view === "academy"
            ? styles.mobileActive
            : ""
        }
      >
        ♜
        <small>Academy</small>
      </button>

      <button
        type="button"
        onClick={() => onNavigate("home")}
        className={
          view === "home"
            ? styles.mobileActive
            : ""
        }
      >
        ✦
        <small>Cinema</small>
      </button>

      <button
        type="button"
        onClick={() => onNavigate("profile")}
        className={
          view === "profile"
            ? styles.mobileActive
            : ""
        }
      >
        ♙
        <small>Profile</small>
      </button>
    </nav>
  );
}