import { useMemo, useState } from "react";

import {
  getSpotifySearchUrl,
  runCinema,
  runCinemaAction,
  type CinemaResult,
} from "./cinemaApi";

import styles from "./AgenticCinemaPage.module.css";

type View =
  | "home"
  | "chat"
  | "results"
  | "challenge"
  | "academy"
  | "recommendations"
  | "memory"
  | "luminate"
  | "profile";

const PROMPTS = [
  "What are the most important developments in the film industry this week?",
  "What streaming trends should filmmakers watch this month?",
  "What are critics saying about current cinema trends?",
  "Recommend a French-language film topic for me.",
];

export default function AgenticCinemaPage() {
  const [view, setView] = useState<View>("home");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<CinemaResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [actionMessage, setActionMessage] = useState("");
  const [challengeAnswer, setChallengeAnswer] = useState("");
  const [challengeFeedback, setChallengeFeedback] = useState("");
  const [challengeLoading, setChallengeLoading] = useState(false);

  const intelligenceText = useMemo(() => {
    if (!result) {
      return "";
    }

    return (
      result.intelligence ||
      result.summary ||
      result.result ||
      ""
    );
  }, [result]);

  async function executeCinema(question: string) {
    const clean = question.trim();

    if (!clean || loading) {
      return;
    }

    setMessage(clean);
    setLoading(true);
    setResult(null);
    setActionMessage("");
    setView("results");

    try {
      const data = await runCinema(clean);
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        error:
          error instanceof Error
            ? error.message
            : "Unable to reach the cinema service.",
      });
    } finally {
      setLoading(false);
    }
  }

  async function saveToMemory() {
    if (!result || saved) {
      return;
    }

    setActionMessage("");

    try {
      const response = await runCinemaAction("save", {
        user_id: "hackathon-judge",
        question: message,
        result,
      });

      if (response.success) {
        setSaved(true);
        setActionMessage("Saved to Academy Memory.");
      } else {
        setActionMessage(
          response.error ||
            "Memory service is not configured.",
        );
      }
    } catch (error) {
      setActionMessage(
        error instanceof Error
          ? error.message
          : "Memory service could not be reached.",
      );
    }
  }

  async function evaluateChallenge() {
    if (!result?.learning_challenge) {
      return;
    }

    setChallengeLoading(true);
    setChallengeFeedback("");

    try {
      const response = await runCinemaAction(
        "challenge",
        {
          user_id: "hackathon-judge",
          answer: challengeAnswer,
          challenge: result.learning_challenge,
        },
      );

      setChallengeFeedback(
        response.feedback ||
          response.error ||
          "Challenge evaluation completed.",
      );
    } catch (error) {
      setChallengeFeedback(
        error instanceof Error
          ? error.message
          : "Evaluation service could not be reached.",
      );
    } finally {
      setChallengeLoading(false);
    }
  }

  function openSpotify() {
    const query =
      message ||
      "cinematic film soundtrack French cinema";

    window.open(
      getSpotifySearchUrl(query),
      "_blank",
      "noopener,noreferrer",
    );
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <span className={styles.brandMark}>✦</span>

          <div>
            <strong>EasyChatBot</strong>
            <small>Growing With You.</small>
          </div>
        </div>

        <nav
          className={styles.navigation}
          aria-label="Cinema navigation"
        >
          <NavigationButton
            icon="⌂"
            label="Home"
            active={view === "home"}
            onClick={() => setView("home")}
          />

          <NavigationButton
            icon="○"
            label="Chat"
            active={view === "chat"}
            onClick={() => setView("chat")}
          />

          <NavigationButton
            icon="✦"
            label="Agentic Cinema"
            active
            accent
            onClick={() => setView("home")}
          />

          <NavigationButton
            icon="♜"
            label="Academy"
            active={view === "academy"}
            onClick={() => setView("academy")}
          />

          <NavigationButton
            icon="▣"
            label="Progress"
            onClick={() => setView("academy")}
          />

          <NavigationButton
            icon="✧"
            label="Memory"
            active={view === "memory"}
            onClick={() => setView("memory")}
          />

          <NavigationButton
            icon="★"
            label="Recommendations"
            active={view === "recommendations"}
            onClick={() => setView("recommendations")}
          />

          <NavigationButton
            icon="♧"
            label="Notifications"
            onClick={() => {
              setActionMessage(
                "Your Cinema Mission is ready.",
              );
            }}
          />

          <NavigationButton
            icon="✦"
            label="Luminate"
            active={view === "luminate"}
            accent
            onClick={() => setView("luminate")}
          />

          <NavigationButton
            icon="♙"
            label="Profile"
            active={view === "profile"}
            onClick={() => setView("profile")}
          />
        </nav>

        <button
          className={styles.luminateMini}
          onClick={() => setView("luminate")}
        >
          <div className={styles.avatarSmall}>L</div>

          <div>
            <strong>Luminate</strong>
            <small>Your Cinema Guide</small>
          </div>
        </button>
      </aside>

      <main className={styles.main}>
        <header className={styles.topbar}>
          <div>
            <span className={styles.topEyebrow}>
              EASYCHATBOT · LIVING AI WORLD
            </span>
            <strong>Agentic Cinema</strong>
          </div>

          <div className={styles.topActions}>
            <button
              className={styles.academyButton}
              onClick={() => setView("academy")}
            >
              ♜ Your Academy
            </button>

            <button
              className={styles.avatarButton}
              onClick={() => setView("luminate")}
              aria-label="Open Luminate"
            >
              L
            </button>
          </div>
        </header>

        {view === "home" && (
          <Home
            onStart={() => setView("chat")}
            onPrompt={executeCinema}
            onRecommendations={() =>
              setView("recommendations")
            }
            onLuminate={() => setView("luminate")}
          />
        )}

        {view === "chat" && (
          <Chat
            message={message}
            setMessage={setMessage}
            loading={loading}
            onSubmit={() => executeCinema(message)}
            onBack={() => setView("home")}
          />
        )}

        {view === "results" && (
          <Results
            question={message}
            result={result}
            loading={loading}
            intelligenceText={intelligenceText}
            saved={saved}
            actionMessage={actionMessage}
            onBack={() => setView("chat")}
            onSave={saveToMemory}
            onChallenge={() => setView("challenge")}
            onRecommendations={() =>
              setView("recommendations")
            }
            onSpotify={openSpotify}
            onRunAgain={() => setView("chat")}
          />
        )}

        {view === "challenge" && (
          <Challenge
            result={result}
            answer={challengeAnswer}
            setAnswer={setChallengeAnswer}
            feedback={challengeFeedback}
            loading={challengeLoading}
            onEvaluate={evaluateChallenge}
            onBack={() => setView("results")}
          />
        )}

        {view === "recommendations" && (
          <Recommendations
            topic={message}
            onSpotify={openSpotify}
            onBack={() => setView("home")}
          />
        )}

        {view === "academy" && (
          <Academy
            result={result}
            onChallenge={() => setView("challenge")}
            onBack={() => setView("home")}
          />
        )}

        {view === "memory" && (
          <Memory
            saved={saved}
            onBack={() => setView("home")}
          />
        )}

        {view === "luminate" && (
          <Luminate
            onStart={() => setView("chat")}
            onRecommendations={() =>
              setView("recommendations")
            }
            onBack={() => setView("home")}
          />
        )}

        {view === "profile" && (
          <Profile
            onBack={() => setView("home")}
          />
        )}

        {actionMessage && (
          <div
            className={styles.toast}
            role="status"
          >
            <span>{actionMessage}</span>

            <button
              onClick={() => setActionMessage("")}
            >
              ×
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

function Home({
  onStart,
  onPrompt,
  onRecommendations,
  onLuminate,
}: {
  onStart: () => void;
  onPrompt: (prompt: string) => void;
  onRecommendations: () => void;
  onLuminate: () => void;
}) {
  return (
    <section className={styles.content}>
      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}>
            ✦ EASYCHATBOT · LIVING AI WORLD
          </span>

          <h1>
            AGENTIC <em>CINEMA</em>
          </h1>

          <p>
            Live intelligence. Real stories. Your AI
            research crew for the studio.
          </p>

          <div className={styles.capabilities}>
            <span>✓ Real-time research with Parallel</span>
            <span>✓ AI reasoning with Gemini</span>
            <span>✓ Personalised to your profile</span>
            <span>✓ Turn insights into learning</span>
          </div>

          <div className={styles.actions}>
            <button
              className={styles.primaryButton}
              onClick={onStart}
            >
              Start Exploring →
            </button>

            <button
              className={styles.secondaryButton}
              onClick={() =>
                onPrompt(PROMPTS[0])
              }
            >
              ▷ Try a question
            </button>
          </div>
        </div>

        <button
          className={styles.luminateHero}
          onClick={onLuminate}
          aria-label="Open Luminate"
        >
          <div className={styles.characterOrb}>
            L
          </div>

          <div>
            <strong>Luminate</strong>
            <span>Great stories start with curious minds.</span>
          </div>
        </button>
      </section>

      <section>
        <span className={styles.eyebrow}>
          YOUR CINEMA CREW
        </span>

        <h2>Choose where to explore</h2>

        <div className={styles.cardGrid}>
          <ActionCard
            icon="▣"
            title="Movies & TV"
            description="Latest news and analysis"
            onClick={() =>
              onPrompt(
                "What are the biggest current movies and TV developments?",
              )
            }
          />

          <ActionCard
            icon="♜"
            title="Industry Trends"
            description="Business, streaming & awards"
            onClick={() =>
              onPrompt(
                "What industry trends should filmmakers watch right now?",
              )
            }
          />

          <ActionCard
            icon="♡"
            title="Personalised Picks"
            description="Tailored to your profile"
            onClick={onRecommendations}
          />

          <ActionCard
            icon="☷"
            title="Learn & Grow"
            description="Turn insights into French practice"
            onClick={() =>
              onPrompt(
                "Give me a current film-industry story I can practise in French.",
              )
            }
          />
        </div>
      </section>

      <section className={styles.bottomGrid}>
        <InfoCard title="Today's Mission ✨">
          <p>
            Complete a real conversation with your
            Cinema Intelligence Agent.
          </p>

          <button
            className={styles.primarySmall}
            onClick={onStart}
          >
            Start Mission →
          </button>
        </InfoCard>

        <InfoCard title="Academy Progress ✦">
          <p>French World · B2</p>

          <div className={styles.progress}>
            <span style={{ width: "68%" }} />
          </div>

          <strong>68%</strong>
        </InfoCard>

        <InfoCard title="Luminate's Pick ★">
          <p>
            Discover something connected to your
            current Cinema journey.
          </p>

          <button
            className={styles.linkButton}
            onClick={onRecommendations}
          >
            Explore Pick →
          </button>
        </InfoCard>
      </section>
    </section>
  );
}

function Chat({
  message,
  setMessage,
  loading,
  onSubmit,
  onBack,
}: {
  message: string;
  setMessage: (value: string) => void;
  loading: boolean;
  onSubmit: () => void;
  onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <span className={styles.eyebrow}>
        CINEMA INTELLIGENCE AGENT
      </span>

      <h1>What would you like to explore?</h1>

      <p className={styles.lead}>
        Ask about cinema, film, streaming, media,
        trends or a current industry story.
      </p>

      <div className={styles.chatBox}>
        <textarea
          value={message}
          onChange={(event) =>
            setMessage(event.target.value)
          }
          placeholder="Ask your Cinema Intelligence Agent..."
          rows={5}
          disabled={loading}
        />

        <div className={styles.promptRow}>
          {PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => setMessage(prompt)}
              disabled={loading}
            >
              {prompt}
            </button>
          ))}
        </div>

        <button
          className={styles.primaryButton}
          onClick={onSubmit}
          disabled={loading || !message.trim()}
        >
          {loading
            ? "Researching..."
            : "Run Cinema Intelligence →"}
        </button>
      </div>
    </section>
  );
}

function Results({
  question,
  result,
  loading,
  intelligenceText,
  saved,
  actionMessage,
  onBack,
  onSave,
  onChallenge,
  onRecommendations,
  onSpotify,
  onRunAgain,
}: {
  question: string;
  result: CinemaResult | null;
  loading: boolean;
  intelligenceText: string;
  saved: boolean;
  actionMessage: string;
  onBack: () => void;
  onSave: () => void;
  onChallenge: () => void;
  onRecommendations: () => void;
  onSpotify: () => void;
  onRunAgain: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back to Chat
      </button>

      {loading && (
        <div className={styles.loadingCard}>
          <div className={styles.spinner} />

          <h2>Your research crew is working...</h2>

          <p>
            Searching live sources with Parallel,
            analysing with Gemini and preparing your
            personalised result.
          </p>
        </div>
      )}

      {!loading && result?.error && (
        <div className={styles.errorCard}>
          <h2>Research could not be completed</h2>

          <p>{result.error}</p>

          <button
            className={styles.primarySmall}
            onClick={onRunAgain}
          >
            Try Again
          </button>
        </div>
      )}

      {!loading && result && !result.error && (
        <>
          <div className={styles.resultHeader}>
            <span className={styles.liveBadge}>
              ● LIVE INTELLIGENCE
            </span>

            <h1>{question}</h1>

            <p>
              Generated by the connected Cinema
              application workflow.
            </p>
          </div>

          <article className={styles.resultCard}>
            {intelligenceText
              .split(/\n+/)
              .filter(Boolean)
              .map((line, index) => (
                <p key={`${line}-${index}`}>
                  {line}
                </p>
              ))}
          </article>

          {result.sources &&
            result.sources.length > 0 && (
              <section>
                <h2>Research Sources</h2>

                <div className={styles.sources}>
                  {result.sources.map(
                    (source, index) => (
                      <a
                        key={`${source.title}-${index}`}
                        href={source.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <span>{index + 1}</span>

                        <div>
                          <strong>
                            {source.title}
                          </strong>

                          <small>
                            {source.snippet ||
                              "Live source used by the workflow."}
                          </small>
                        </div>

                        <span>↗</span>
                      </a>
                    ),
                  )}
                </div>
              </section>
            )}

          <div className={styles.actionGrid}>
            <button
              className={styles.primaryButton}
              onClick={onChallenge}
            >
              Turn into Learning Challenge →
            </button>

            <button
              className={styles.secondaryButton}
              onClick={onSave}
            >
              {saved
                ? "✓ Saved to Memory"
                : "✦ Save to Memory"}
            </button>

            <button
              className={styles.secondaryButton}
              onClick={onRecommendations}
            >
              ★ Recommendations
            </button>

            <button
              className={styles.secondaryButton}
              onClick={onSpotify}
            >
              ♪ Explore on Spotify
            </button>
          </div>

          {actionMessage && (
            <p
              className={styles.actionMessage}
              role="status"
            >
              {actionMessage}
            </p>
          )}
        </>
      )}
    </section>
  );
}

function Challenge({
  result,
  answer,
  setAnswer,
  feedback,
  loading,
  onEvaluate,
  onBack,
}: {
  result: CinemaResult | null;
  answer: string;
  setAnswer: (value: string) => void;
  feedback: string;
  loading: boolean;
  onEvaluate: () => void;
  onBack: () => void;
}) {
  const challenge = result?.learning_challenge;

  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back to Result
      </button>

      <span className={styles.eyebrow}>
        FRENCH LEARNING MISSION
      </span>

      <h1>Turn intelligence into learning.</h1>

      {!challenge ? (
        <div className={styles.errorCard}>
          <p>
            This result did not provide a learning
            challenge.
          </p>
        </div>
      ) : (
        <div className={styles.challengeCard}>
          <h2>{challenge.prompt}</h2>

          {challenge.vocabulary &&
            challenge.vocabulary.length > 0 && (
              <div className={styles.vocabulary}>
                {challenge.vocabulary.map((word) => (
                  <span key={word}>{word}</span>
                ))}
              </div>
            )}

          <textarea
            value={answer}
            onChange={(event) =>
              setAnswer(event.target.value)
            }
            placeholder="Write your answer in French..."
            rows={7}
          />

          <button
            className={styles.primaryButton}
            onClick={onEvaluate}
            disabled={
              loading || !answer.trim()
            }
          >
            {loading
              ? "Evaluating..."
              : "Evaluate My Answer →"}
          </button>

          {feedback && (
            <div
              className={styles.feedback}
              role="status"
            >
              {feedback}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function Recommendations({
  topic,
  onSpotify,
  onBack,
}: {
  topic: string;
  onSpotify: () => void;
  onBack: () => void;
}) {
  const searchTopic =
    topic ||
    "cinema French film soundtrack";

  const spotifyUrl =
    getSpotifySearchUrl(searchTopic);

  return (
    <section className={styles.content}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <span className={styles.eyebrow}>
        LUMINATE · PERSONAL RECOMMENDATIONS
      </span>

      <h1>Recommendations for your Cinema journey</h1>

      <div className={styles.recommendationGrid}>
        <article className={styles.recommendationCard}>
          <span className={styles.recommendationIcon}>
            ♪
          </span>

          <h2>Spotify</h2>

          <p>
            Explore music connected to your current
            cinema research and language-learning
            journey.
          </p>

          <a
            href={spotifyUrl}
            target="_blank"
            rel="noreferrer"
            className={styles.primarySmall}
          >
            Search Spotify →
          </a>
        </article>

        <article className={styles.recommendationCard}>
          <span className={styles.recommendationIcon}>
            🎬
          </span>

          <h2>Explore Cinema</h2>

          <p>
            Ask the Cinema Intelligence Agent to
            discover current stories related to your
            interests.
          </p>

          <button
            className={styles.secondaryButton}
            onClick={onBack}
          >
            Start Research →
          </button>
        </article>

        <article className={styles.recommendationCard}>
          <span className={styles.recommendationIcon}>
            ✦
          </span>

          <h2>Luminate's Pick</h2>

          <p>
            Recommendations should connect your
            current topic, memory and learning goals.
          </p>

          <button
            className={styles.secondaryButton}
            onClick={onSpotify}
          >
            Explore →
          </button>
        </article>
      </div>
    </section>
  );
}

function Academy({
  result,
  onChallenge,
  onBack,
}: {
  result: CinemaResult | null;
  onChallenge: () => void;
  onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <span className={styles.eyebrow}>
        YOUR ACADEMY
      </span>

      <h1>French World · B2</h1>

      <div className={styles.progressCard}>
        <div className={styles.progressLarge}>
          <span style={{ width: "68%" }} />
        </div>

        <strong>68%</strong>

        <p>
          Your Cinema Intelligence journey can turn
          current media research into practical French
          learning.
        </p>

        {result?.learning_challenge && (
          <button
            className={styles.primaryButton}
            onClick={onChallenge}
          >
            Continue Learning Challenge →
          </button>
        )}
      </div>
    </section>
  );
}

function Memory({
  saved,
  onBack,
}: {
  saved: boolean;
  onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <span className={styles.eyebrow}>
        ACADEMY MEMORY
      </span>

      <h1>Your Cinema Memory</h1>

      <div className={styles.memoryCard}>
        <span className={styles.avatarSmall}>L</span>

        <div>
          <h2>
            {saved
              ? "Latest intelligence saved"
              : "No Cinema result saved yet"}
          </h2>

          <p>
            Saved intelligence can be used by the
            application to personalise future learning.
          </p>
        </div>
      </div>
    </section>
  );
}

function Luminate({
  onStart,
  onRecommendations,
  onBack,
}: {
  onStart: () => void;
  onRecommendations: () => void;
  onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <div className={styles.luminateProfile}>
        <div className={styles.characterLarge}>
          L
        </div>

        <span className={styles.eyebrow}>
          YOUR CINEMA COMPANION
        </span>

        <h1>Meet Luminate.</h1>

        <p>
          I help you explore current cinema stories,
          connect ideas, practise French and discover
          recommendations that fit your journey.
        </p>

        <div className={styles.actions}>
          <button
            className={styles.primaryButton}
            onClick={onStart}
          >
            Talk to Cinema Intelligence →
          </button>

          <button
            className={styles.secondaryButton}
            onClick={onRecommendations}
          >
            See My Recommendations
          </button>
        </div>
      </div>
    </section>
  );
}

function Profile({
  onBack,
}: {
  onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button
        className={styles.backButton}
        onClick={onBack}
      >
        ← Back
      </button>

      <span className={styles.eyebrow}>
        LEARNER PROFILE
      </span>

      <h1>Your Cinema Profile</h1>

      <div className={styles.profileCard}>
        <div className={styles.characterOrb}>
          L
        </div>

        <div>
          <h2>Learner</h2>
          <p>French · B2</p>
          <p>1,350 XP</p>
        </div>
      </div>
    </section>
  );
}

function NavigationButton({
  icon,
  label,
  active,
  accent,
  onClick,
}: {
  icon: string;
  label: string;
  active?: boolean;
  accent?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={[
        styles.navigationButton,
        active ? styles.navigationActive : "",
        accent ? styles.navigationAccent : "",
      ].join(" ")}
      onClick={onClick}
    >
      <span>{icon}</span>
      {label}
    </button>
  );
}

function ActionCard({
  icon,
  title,
  description,
  onClick,
}: {
  icon: string;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      className={styles.actionCard}
      onClick={onClick}
    >
      <span>{icon}</span>
      <strong>{title}</strong>
      <small>{description}</small>
      <i>→</i>
    </button>
  );
}

function InfoCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article className={styles.infoCard}>
      <h3>{title}</h3>
      {children}
    </article>
  );
}