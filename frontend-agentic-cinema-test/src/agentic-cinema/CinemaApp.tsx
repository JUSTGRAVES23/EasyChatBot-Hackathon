 "use client";

import { useMemo, useState } from "react";
import styles from "./CinemaApp.module.css";

type Source = { title: string; url?: string; snippet?: string };
type CinemaResult = {
  success?: boolean;
  result?: string;
  intelligence?: string;
  summary?: string;
  sources?: Source[];
  learning_challenge?: { prompt?: string; answer?: string; vocabulary?: string[] };
  personalisation?: string | { applied?: boolean; message?: string };
  error?: string;
};

type View = "home" | "chat" | "results" | "challenge" | "academy" | "profile";

const prompts = [
  "What are the most important developments in the film industry this week?",
  "What are critics saying about the latest cinema trends?",
  "What streaming trends should filmmakers watch this month?",
  "Recommend a French-language film topic for me.",
  "Explain a current film-industry story in simple French."
];

export function CinemaApp() {
  const [view, setView] = useState<View>("home");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CinemaResult | null>(null);
  const [saved, setSaved] = useState(() => window.localStorage.getItem("easychatbot.cinema.saved") === "true");
  const [actionMessage, setActionMessage] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [hintOpen, setHintOpen] = useState(false);

  const intelligenceText = useMemo(() => {
    if (!result) return "";
    return result.intelligence || result.summary || result.result || "";
  }, [result]);

  async function runCinema(question = message) {
    const clean = question.trim();
    if (!clean || loading) return;

    setMessage(clean);
    setLoading(true);
    setResult(null);
    setView("results");

    try {
      const response = await fetch("/api/cinema", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: clean,
          userId: "hackathon-judge",
          language: "French",
          learnerLevel: "B2"
        })
      });

      const data = (await response.json()) as CinemaResult;
      setResult(data);
    } catch {
      setResult({ success: false, error: "Unable to reach the cinema service." });
    } finally {
      setLoading(false);
    }
  }

  function openChat(prefill = "") {
    setMessage(prefill);
    setView("chat");
  }

  async function runAction(action: "save" | "challenge", payload: Record<string, unknown>) {
    const response = await fetch("/api/cinema/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, payload })
    });
    return (await response.json()) as { success?: boolean; configured?: boolean; error?: string };
  }

  function saveResult() {
    if (!result || saved) return;
    window.localStorage.setItem("easychatbot.cinema.saved", "true");
    setSaved(true);
    setActionMessage("Saved on this device.");
  }

  function shareResult() {
    const text = intelligenceText.slice(0, 900);
    if (typeof navigator !== "undefined" && navigator.share) {
      navigator.share({ title: "EasyChatBot · Agentic Cinema", text }).catch(() => undefined);
      return;
    }
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => undefined);
    }
  }

  function nav(next: View) {
    setView(next);
    if (next !== "profile") setProfileOpen(false);
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <Brand />
        <nav className={styles.sideNav} aria-label="Primary navigation">
          <NavButton active={view === "home"} icon="⌂" label="Home" onClick={() => nav("home")} />
          <NavButton active={view === "chat"} icon="◌" label="Chat" onClick={() => nav("chat")} />
          <NavButton active={view === "home"} icon="✦" label="Agentic Cinema" onClick={() => nav("home")} accent />
          <NavButton icon="♜" label="Academy" onClick={() => nav("academy")} />
          <NavButton icon="◫" label="Progress" onClick={() => nav("academy")} />
          <NavButton icon="✧" label="Memory" onClick={() => nav("academy")} />
          <NavButton icon="☆" label="Recommendations" onClick={() => nav("home")} />
          <NavButton icon="♧" label="Notifications" badge="5" onClick={() => setNotificationsOpen(true)} />
          <NavButton icon="♙" label="Profile" onClick={() => nav("profile")} />
          <NavButton icon="⚙" label="Settings" onClick={() => setProfileOpen(true)} />
        </nav>
        <ProfileMini onClick={() => nav("profile")} />
      </aside>

      <main className={styles.main}>
        <header className={styles.topbar}>
          <button className={styles.mobileBrand} onClick={() => nav("home")}>✦ EasyChatBot</button>
          <div className={styles.topActions}>
            <button className={styles.academyPill} onClick={() => nav("academy")}>♜ Your Academy</button>
            <button className={styles.iconButton} aria-label="Notifications" onClick={() => setNotificationsOpen(true)}>♧<span>5</span></button>
            <button className={styles.avatarButton} onClick={() => nav("profile")}>L</button>
          </div>
        </header>

        {view === "home" && (
          <HomeScreen
            onStart={() => openChat()}
            onPrompt={(p) => runCinema(p)}
            onAcademy={() => nav("academy")}
          />
        )}

        {view === "chat" && (
          <ChatScreen
            message={message}
            setMessage={setMessage}
            loading={loading}
            onRun={() => runCinema()}
            onPrompt={(p) => setMessage(p)}
            onBack={() => nav("home")}
          />
        )}

        {view === "results" && (
          <ResultsScreen
            question={message}
            loading={loading}
            result={result}
            intelligenceText={intelligenceText}
            saved={saved}
            onBack={() => nav("chat")}
            onChallenge={() => nav("challenge")}
            onSave={saveResult}
            onShare={shareResult}
            actionMessage={actionMessage}
            onRunAgain={() => nav("chat")}
          />
        )}

        {view === "challenge" && (
          <ChallengeScreen result={result} onBack={() => nav("results")} />
        )}

        {view === "academy" && (
          <AcademyScreen saved={saved} onBack={() => nav("home")} />
        )}

        {view === "profile" && (
          <ProfileScreen onBack={() => nav("home")} />
        )}

        {notificationsOpen && (
          <div className={styles.modalBackdrop} role="presentation" onClick={() => setNotificationsOpen(false)}>
            <section className={styles.notificationPanel} role="dialog" aria-modal="true" aria-labelledby="notifications-title" onClick={(e) => e.stopPropagation()}>
              <div className={styles.modalHeader}><div><span className={styles.eyebrow}>ACADEMY</span><h2 id="notifications-title">Notifications</h2></div><button onClick={() => setNotificationsOpen(false)} className={styles.closeButton}>×</button></div>
              <div className={styles.notificationItem}><span>✦</span><div><strong>New Cinema Mission</strong><p>Run a live intelligence workflow and turn the result into French practice.</p></div></div>
              <div className={styles.notificationItem}><span>♜</span><div><strong>Academy Progress</strong><p>Your B2 cinema-learning journey is ready for the next step.</p></div></div>
              <div className={styles.notificationItem}><span>✧</span><div><strong>Memory</strong><p>Save a completed intelligence result to continue your personalised journey.</p></div></div>
              <button className={styles.primaryButtonSmall} onClick={() => { setNotificationsOpen(false); nav("chat"); }}>Start a Mission →</button>
            </section>
          </div>
        )}

        {profileOpen && (
          <div className={styles.toast}>
            <strong>Settings</strong>
            <span>Configuration remains in the application/backend layer.</span>
            <button onClick={() => setProfileOpen(false)}>Close</button>
          </div>
        )}
      </main>

      <MobileNav view={view} onNavigate={nav} />
    </div>
  );
}

function HomeScreen({
  onStart,
  onPrompt,
  onAcademy
}: {
  onStart: () => void;
  onPrompt: (p: string) => void;
  onAcademy: () => void;
}) {
  return (
    <section className={styles.content}>
      <div className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}>✦ EASYCHATBOT · LIVING AI WORLD</span>
          <h1>AGENTIC <em>CINEMA</em></h1>
          <p>Live intelligence. Real stories. Your AI research crew for the studio.</p>
          <div className={styles.capabilities}>
            <span>✓ Real-time research with Parallel</span>
            <span>✓ AI reasoning with Gemini</span>
            <span>✓ Personalised to your learning profile</span>
            <span>✓ Turn insights into learning</span>
          </div>
          <div className={styles.heroActions}>
            <button className={styles.primaryButton} onClick={onStart}>Start Exploring →</button>
            <button className={styles.secondaryButton} onClick={() => onPrompt("What are the most important developments in the film industry this week?")}>▷ Try a question</button>
          </div>
        </div>
        <CharacterArt />
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <span className={styles.eyebrow}>YOUR CINEMA CREW</span>
          <h2>Choose where to explore</h2>
        </div>
      </div>

      <div className={styles.featureGrid}>
        <FeatureCard icon="▣" title="Movies & TV" text="Latest news and analysis" onClick={() => onPrompt("What are the biggest current movies and TV developments?")} />
        <FeatureCard icon="♜" title="Industry Trends" text="Business, streaming & awards" onClick={() => onPrompt("What industry trends should filmmakers watch right now?")} />
        <FeatureCard icon="♡" title="Personalised Picks" text="Tailored to your profile" onClick={() => onPrompt("Recommend a current cinema topic based on my interests.")} />
        <FeatureCard icon="☷" title="Learn & Grow" text="Turn insights into French practice" onClick={() => onPrompt("Give me a current film-industry story I can practise in French.")} />
      </div>

      <div className={styles.lowerGrid}>
        <Panel title="Today's Mission ✨">
          <p>Complete a real conversation with your Cinema Intelligence Agent.</p>
          <button className={styles.primaryButtonSmall} onClick={onStart}>Start Mission ▶</button>
        </Panel>
        <Panel title="Academy Progress ☀">
          <div className={styles.progressRow}><span>French World · B2</span><strong>68%</strong></div>
          <div className={styles.progress}><i style={{ width: "68%" }} /></div>
          <button className={styles.linkButton} onClick={onAcademy}>View Academy →</button>
        </Panel>
        <Panel title="Luminate's Pick ☆">
          <p>“Great content sparks ideas and opens new worlds.”</p>
          <button className={styles.linkButton} onClick={() => onPrompt("What current story would you recommend for my learning journey?")}>Explore Pick →</button>
        </Panel>
      </div>
    </section>
  );
}

function ChatScreen({
  message, setMessage, loading, onRun, onPrompt, onBack
}: {
  message: string; setMessage: (v: string) => void; loading: boolean; onRun: () => void; onPrompt: (p: string) => void; onBack: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button className={styles.backButton} onClick={onBack}>← Back</button>
      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>✦</span>
        <div><span className={styles.eyebrow}>AGENTIC CINEMA</span><h1>Ask your Cinema Intelligence Agent</h1></div>
      </div>

      <div className={styles.chatCard}>
        <div className={styles.messageAgent}>
          <CharacterAvatar />
          <div>
            <strong>Luminate · Cinema Intelligence</strong>
            <p>Hi! I’m your Cinema Intelligence Agent. Ask me anything about movies, TV, the film industry, or a current story you want to understand.</p>
          </div>
        </div>

        <div className={styles.promptList}>
          {prompts.map((prompt) => (
            <button key={prompt} onClick={() => onPrompt(prompt)}>{prompt}<span>→</span></button>
          ))}
        </div>

        <div className={styles.composer}>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onRun(); } }}
            placeholder="Ask anything about movies, TV, or the industry…"
            rows={3}
          />
          <button className={styles.sendButton} onClick={onRun} disabled={loading || !message.trim()}>{loading ? "…" : "➤"}</button>
        </div>
        <div className={styles.trustLine}>Secure application boundary · Gemini reasoning · Parallel live research · No browser-side secrets</div>
      </div>
    </section>
  );
}

function ResultsScreen({
  question, loading, result, intelligenceText, saved, onBack, onChallenge, onSave, onRunAgain
}: {
  question: string; loading: boolean; result: CinemaResult | null; intelligenceText: string; saved: boolean; onBack: () => void; onChallenge: () => void; onSave: () => void; onRunAgain: () => void;
}) {
  return (
    <section className={styles.contentNarrow}>
      <button className={styles.backButton} onClick={onBack}>← Ask another question</button>
      <div className={styles.pageTitle}>
        <span className={styles.agentIcon}>✦</span>
        <div><span className={styles.eyebrow}>AGENTIC CINEMA · RESULT</span><h1>Your personalised cinema intelligence</h1></div>
      </div>

      <div className={styles.statusBar}>
        <span>● Parallel</span><span>● Gemini</span><span>● Memory</span><span>● Personalisation</span>
      </div>

      {loading && (
        <div className={styles.loadingCard} aria-live="polite">
          <div className={styles.spinner} />
          <h2>Your research crew is working…</h2>
          <p>Searching live sources with Parallel, analysing with Gemini, and preparing your personalised learning result.</p>
          <div className={styles.loadingSteps}><span>✓ Live research</span><span>✓ Gemini analysis</span><span>◌ Personalisation</span></div>
        </div>
      )}

      {!loading && result?.error && (
        <div className={styles.errorCard}>
          <strong>The cinema service could not complete the request.</strong>
          <p>{result.error}</p>
          <button className={styles.primaryButtonSmall} onClick={onRunAgain}>Try Again</button>
        </div>
      )}

      {!loading && result && !result.error && (
        <>
          <article className={styles.resultCard}>
            <div className={styles.resultHeader}>
              <div><span className={styles.resultTag}>LIVE INTELLIGENCE</span><h2>{question || "Cinema Intelligence"}</h2><small>Generated from the connected application workflow</small></div>
              <span className={styles.liveBadge}>LIVE</span>
            </div>
            <div className={styles.resultBody}>
              {intelligenceText.split(/\n+/).filter(Boolean).map((line, i) => <p key={i}>{line}</p>)}
            </div>
            {result.sources && result.sources.length > 0 && (
              <div className={styles.sources}>
                <h3>Research sources</h3>
                {result.sources.map((source, i) => (
                  <a key={`${source.title}-${i}`} href={source.url || "#"} target="_blank" rel="noreferrer">
                    <span>{i + 1}</span><strong>{source.title}</strong><small>{source.snippet || "Live source used by the workflow"}</small>↗
                  </a>
                ))}
              </div>
            )}
            <div className={styles.resultActions}>
              <button className={styles.primaryButtonSmall} onClick={onChallenge}>Turn this into a learning challenge →</button>
              <button className={styles.secondaryButtonSmall} onClick={onSave}>{saved ? "✓ Saved on this device" : "☆ Save on this device"}</button>
              <button className={styles.secondaryButtonSmall} onClick={() => window.print()}>PDF / Print</button>
              <button className={styles.secondaryButtonSmall} onClick={onShare}>Share</button>
            </div>
            {actionMessage && <div className={styles.actionMessage} role="status">{actionMessage}</div>}
          </article>
        </>
      )}
    </section>
  );
}

function ChallengeScreen({ result, onBack }: { result: CinemaResult | null; onBack: () => void }) {
  const challenge = result?.learning_challenge;
  const [answer, setAnswer] = useState("");
  const [checked, setChecked] = useState(false);
  const [checking, setChecking] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [hintOpen, setHintOpen] = useState(false);

  async function checkAnswer() {
    setChecking(true);
    try {
      const response = await fetch("/api/cinema/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "challenge",
          payload: {
            user_id: "hackathon-judge",
            answer,
            challenge: challenge ?? null
          }
        })
      });
      const data = (await response.json()) as { success?: boolean; feedback?: string; error?: string };
      setChecked(true);
      setFeedback(data.feedback || (data.success ? "Answer evaluated by the connected application." : "Evaluation endpoint is not configured yet."));
    } catch {
      setChecked(true);
      setFeedback("The evaluation service could not be reached.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <section className={styles.contentNarrow}>
      <button className={styles.backButton} onClick={onBack}>← Back to intelligence</button>
      <div className={styles.pageTitle}><span className={styles.agentIcon}>☷</span><div><span className={styles.eyebrow}>LEARNING CHALLENGE · B2</span><h1>Turn real-world insight into progress</h1></div></div>
      <div className={styles.challengeCard}>
        <div className={styles.challengeHeader}><span>✦ Learning Challenge</span><b>B1 · B2</b></div>
        <p className={styles.challengeIntro}>Based on today&apos;s live intelligence, practise your French with the real content you just explored.</p>
        <div className={styles.task}>
          <span>▣ TASK</span>
          <h2>{challenge?.prompt || "Summarise the main development in French in 4–6 sentences."}</h2>
          <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Write your answer in French…" maxLength={500} />
          <div className={styles.answerMeta}>{answer.length}/500</div>
          <div className={styles.challengeActions}>
            <button className={styles.primaryButtonSmall} onClick={checkAnswer} disabled={checking || !answer.trim()}>{checking ? "Checking…" : "Check My Answer →"}</button>
            <button className={styles.secondaryButtonSmall} onClick={() => setHintOpen((v) => !v)}>💡 {hintOpen ? "Hide hint" : "Get a hint"}</button>
          </div>
          {hintOpen && <div className={styles.hint}>💡 Try using: {(challenge?.vocabulary || ["production", "industrie", "innovation"]).slice(0, 3).join(" · ")}.</div>}
          {checked && <div className={styles.feedback}>✓ {feedback || "Answer received."}</div>}
        </div>
        <div className={styles.vocabulary}>
          <h3>Useful vocabulary</h3>
          <div>{(challenge?.vocabulary || ["festival", "catégorie", "production", "industrie", "innovation", "créativité"]).map(v => <span key={v}>{v}</span>)}</div>
        </div>
      </div>
    </section>
  );
}

function AcademyScreen({ saved, onBack }: { saved: boolean; onBack: () => void }) {
  return (
    <section className={styles.content}>
      <button className={styles.backButton} onClick={onBack}>← Back</button>
      <div className={styles.pageTitle}><span className={styles.agentIcon}>♜</span><div><span className={styles.eyebrow}>YOUR ACADEMY</span><h1>Saved cinema intelligence</h1></div></div>
      <div className={styles.academyGrid}>
        <Panel title="Memory">
          <strong className={styles.bigNumber}>{saved ? "13" : "12"}</strong><p>Memories saved from your learning journey.</p>
        </Panel>
        <Panel title="Learning Progress">
          <strong className={styles.bigNumber}>68%</strong><p>French World · B2</p><div className={styles.progress}><i style={{ width: "68%" }} /></div>
        </Panel>
        <Panel title="Current Mission">
          <strong>Real-world French</strong><p>Use current cinema stories to build vocabulary and express opinions.</p>
        </Panel>
      </div>
      <div className={styles.savedBanner}>✦ {saved ? "Your latest intelligence has been saved on this device." : "Save a result locally to keep your current demo journey."}</div>
    </section>
  );
}

function ProfileScreen({ onBack }: { onBack: () => void }) {
  const interests = ["Movies", "TV Series", "Film Industry", "French Cinema", "Streaming", "Animation", "Documentaries", "Awards"];
  return (
    <section className={styles.contentNarrow}>
      <button className={styles.backButton} onClick={onBack}>← Back</button>
      <div className={styles.pageTitle}><span className={styles.agentIcon}>♙</span><div><span className={styles.eyebrow}>YOUR PROFILE</span><h1>Personalisation</h1></div></div>
      <div className={styles.profileCard}>
        <div className={styles.profileHero}><CharacterAvatar large /><div><h2>Learner</h2><p>French · B2 · Cinema Explorer</p><div className={styles.progress}><i style={{ width: "68%" }} /></div></div></div>
        <h3>Your interests</h3><div className={styles.tags}>{interests.map(x => <span key={x}>{x}</span>)}</div>
        <h3>Learning goals</h3>
        <div className={styles.goalList}><span>◉ Improve French (B2)</span><span>◉ Discover new content</span><span>◉ Learn industry vocabulary</span><span>◉ Build cultural knowledge</span></div>
      </div>
    </section>
  );
}

function Brand() {
  return <div className={styles.brand}><span className={styles.brandIcon}>✦</span><div><strong>EasyChatBot</strong><em>Growing With You.</em></div></div>;
}

function CharacterArt() {
  return <div className={styles.characterStage}><div className={styles.stars} /><div className={styles.mountain} /><div className={styles.character}><div className={styles.characterHead}>L</div><div className={styles.characterBody}>✦</div><div className={styles.bulb}>●</div></div><div className={styles.characterQuote}>Great stories<br />start with<br /><em>curious minds.</em></div></div>;
}

function CharacterAvatar({ large = false }: { large?: boolean }) {
  return <span className={`${styles.characterAvatar} ${large ? styles.largeAvatar : ""}`}>L</span>;
}

function ProfileMini({ onClick }: { onClick: () => void }) {
  return <button className={styles.profileMini} onClick={onClick}><CharacterAvatar /><span><strong>Learner</strong><small>Level B2</small></span><span className={styles.xp}><i /></span><small>1,350 XP</small></button>;
}

function NavButton({ icon, label, active, accent, badge, onClick }: { icon: string; label: string; active?: boolean; accent?: boolean; badge?: string; onClick: () => void }) {
  return <button className={`${styles.navButton} ${active ? styles.active : ""} ${accent ? styles.accent : ""}`} onClick={onClick}><span>{icon}</span>{label}{badge && <b>{badge}</b>}</button>;
}

function FeatureCard({ icon, title, text, onClick }: { icon: string; title: string; text: string; onClick: () => void }) {
  return <button className={styles.featureCard} onClick={onClick}><span>{icon}</span><strong>{title}</strong><small>{text}</small><i>→</i></button>;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <article className={styles.panel}><h3>{title}</h3>{children}</article>;
}

function MobileNav({ view, onNavigate }: { view: View; onNavigate: (v: View) => void }) {
  return <nav className={styles.mobileNav}><button onClick={() => onNavigate("home")} className={view === "home" ? styles.mobileActive : ""}>⌂<small>Home</small></button><button onClick={() => onNavigate("chat")} className={view === "chat" || view === "results" ? styles.mobileActive : ""}>◌<small>Chat</small></button><button onClick={() => onNavigate("academy")} className={view === "academy" ? styles.mobileActive : ""}>♜<small>Academy</small></button><button onClick={() => onNavigate("home")} className={view === "home" ? styles.mobileActive : ""}>✦<small>Cinema</small></button><button onClick={() => onNavigate("profile")} className={view === "profile" ? styles.mobileActive : ""}>♙<small>Profile</small></button></nav>;
}
