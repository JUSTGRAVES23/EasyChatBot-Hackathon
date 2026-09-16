import { useEffect, useMemo, useState } from "react";
import "./QuestionnaireSelectionPage.css";

type Questionnaire = {
  id: string;
  world_id: string;
  title: string;
  subtitle: string;
  description: string;
  recommended: boolean;
  recommendation_reason?: string | null;
};

type QuestionnaireResponse = {
  world_id: string;
  questionnaires: Questionnaire[];
  recommended_questionnaire_id: string | null;
};

type Props = {
  worldId?: string;
  onStart?: (questionnaire: Questionnaire) => void;
};

const WORLD_NAMES: Record<string, string> = {
  french: "French World",
  cybersecurity: "Cybersecurity World",
};

export default function QuestionnaireSelectionPage({
  worldId = "french",
  onStart,
}: Props) {
  const [data, setData] = useState<QuestionnaireResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadQuestionnaires() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/academy/worlds/${encodeURIComponent(worldId)}/questionnaires`,
        );

        if (!response.ok) {
          throw new Error(
            `Unable to load Academy assessments (${response.status}).`,
          );
        }

        const payload =
          (await response.json()) as QuestionnaireResponse;

        if (!cancelled) {
          setData(payload);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load Academy assessments.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadQuestionnaires();

    return () => {
      cancelled = true;
    };
  }, [worldId]);

  const recommended = useMemo(() => {
    if (!data?.recommended_questionnaire_id) {
      return null;
    }

    return (
      data.questionnaires.find(
        (item) => item.id === data.recommended_questionnaire_id,
      ) ?? null
    );
  }, [data]);

  const available = useMemo(
    () =>
      data?.questionnaires.filter(
        (item) => item.id !== recommended?.id,
      ) ?? [],
    [data, recommended],
  );

  function start(questionnaire: Questionnaire) {
    onStart?.(questionnaire);
  }

  if (loading) {
    return (
      <main className="academy-questionnaires">
        <section className="academy-questionnaires__shell">
          <div className="academy-questionnaires__loading">
            Opening the Academy doors…
          </div>
        </section>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="academy-questionnaires">
        <section className="academy-questionnaires__shell">
          <div className="academy-questionnaires__error">
            <span className="academy-questionnaires__eyebrow">
              Academy doors
            </span>

            <h1>Something got in the way.</h1>

            <p>
              We couldn't load your challenges right now.
              Please try again.
            </p>

            <button
              type="button"
              className="academy-button"
              onClick={() => window.location.reload()}
            >
              Try again
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="academy-questionnaires">
      <section className="academy-questionnaires__shell">
        <header className="academy-questionnaires__hero">
          <div>
            <span className="academy-questionnaires__eyebrow">
              Academy · {WORLD_NAMES[worldId] ?? worldId}
            </span>

            <h1>Choose your next challenge.</h1>

            <p className="academy-questionnaires__intro">
              Ahhh… you're back. 👀
              <br />
              We've been keeping an eye on your progress.
              <br />
              Let's find the challenge that makes your next step easier.
            </p>
          </div>

          <div
            className="academy-questionnaires__compass"
            aria-hidden="true"
          >
            🧭
          </div>
        </header>

        {recommended && (
          <section className="academy-section">
            <div className="academy-section__heading">
              <div>
                <span className="academy-section__eyebrow">
                  ✨ Recommended for you
                </span>

                <h2>Your Academy has a hunch.</h2>
              </div>
            </div>

            <article className="academy-recommendation">
              <div className="academy-recommendation__badge">
                Recommended
              </div>

              <div className="academy-recommendation__content">
                <span className="academy-card__world">🇫🇷</span>

                <h3>{recommended.title}</h3>

                <p className="academy-card__subtitle">
                  {recommended.subtitle}
                </p>

                <p className="academy-card__description">
                  {recommended.description}
                </p>

                {recommended.recommendation_reason && (
                  <p className="academy-card__reason">
                    {recommended.recommendation_reason}
                  </p>
                )}

                <button
                  type="button"
                  className="academy-button academy-button--primary"
                  onClick={() => start(recommended)}
                >
                  ⚡ Start this challenge
                </button>
              </div>
            </article>
          </section>
        )}

        {available.length > 0 && (
          <section className="academy-section">
            <div className="academy-section__heading">
              <div>
                <span className="academy-section__eyebrow">
                  🗺️ Other challenges waiting for you
                </span>

                <h2>Pick your adventure.</h2>
              </div>
            </div>

            <div className="academy-grid">
              {available.map((questionnaire) => (
                <article
                  className="academy-card"
                  key={questionnaire.id}
                >
                  <span className="academy-card__world">🇫🇷</span>

                  <h3>{questionnaire.title}</h3>

                  <p className="academy-card__subtitle">
                    {questionnaire.subtitle}
                  </p>

                  <p className="academy-card__description">
                    {questionnaire.description}
                  </p>

                  <button
                    type="button"
                    className="academy-button academy-button--secondary"
                    onClick={() => start(questionnaire)}
                  >
                    Take the challenge →
                  </button>
                </article>
              ))}
            </div>
          </section>
        )}

        <aside className="academy-hint">
          <span className="academy-hint__icon">🧭</span>

          <div>
            <strong>A little Academy hint</strong>

            <p>
              You don't have to choose the hardest one.
              Choose the one that will make your next
              conversation easier.
            </p>
          </div>
        </aside>
      </section>
    </main>
  );
}