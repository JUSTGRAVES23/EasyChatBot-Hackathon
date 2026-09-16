import { useCallback, useEffect, useState } from "react";
import {
  DeveloperAdministrator,
  grantDeveloperAdministrator,
  listDeveloperAdministrators,
  revokeDeveloperAdministrator,
} from "../../lib/api/developerAdministrators";
import styles from "./ConfigurationOperationsCenter.module.css";

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={styles.icon}>
      <path d="M12 3 19 6v5c0 4.7-2.8 8.4-7 10-4.2-1.6-7-5.3-7-10V6l7-3Z" fill="none" stroke="currentColor" strokeWidth="1.7"/>
      <path d="m9 12 2 2 4-4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function DatabaseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={styles.icon}>
      <ellipse cx="12" cy="5" rx="7" ry="3" fill="none" stroke="currentColor" strokeWidth="1.7"/>
      <path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7" fill="none" stroke="currentColor" strokeWidth="1.7"/>
    </svg>
  );
}

function UsersIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={styles.icon}>
      <circle cx="9" cy="8" r="3" fill="none" stroke="currentColor" strokeWidth="1.7"/>
      <path d="M3.8 19c.5-3.1 2.2-5 5.2-5s4.7 1.9 5.2 5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/>
      <circle cx="17" cy="9" r="2.3" fill="none" stroke="currentColor" strokeWidth="1.7"/>
      <path d="M15.1 14.5c2.5-.1 4.2 1.4 4.8 3.8" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/>
    </svg>
  );
}

export default function ConfigurationOperationsCenter() {
  const [administrators, setAdministrators] = useState<DeveloperAdministrator[]>([]);
  const [userId, setUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listDeveloperAdministrators();
      setAdministrators(result.administrators);
    } catch (err) {
      const e = err as Error & { status?: number };
      setError(
        e.status === 403
          ? "Your authenticated account does not have developer_admin.manage. The initial developer administrator must be bootstrapped through the controlled backend/database path."
          : e.message,
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function grant() {
    const normalized = userId.trim();
    if (!normalized) return;
    setBusy(`grant:${normalized}`);
    setError(null);
    setNotice(null);
    try {
      const created = await grantDeveloperAdministrator(normalized);
      setAdministrators((current) => [
        ...current.filter((item) => item.user_id !== created.user_id),
        created,
      ]);
      setUserId("");
      setNotice(`${created.email} is now a Developer Administrator.`);
    } catch (err) {
      const e = err as Error;
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  async function revoke(admin: DeveloperAdministrator) {
    if (
      !window.confirm(
        `Revoke Developer Administrator privileges from ${admin.email}?`,
      )
    ) return;

    setBusy(`revoke:${admin.user_id}`);
    setError(null);
    setNotice(null);
    try {
      await revokeDeveloperAdministrator(admin.user_id);
      setAdministrators((current) =>
        current.filter((item) => item.user_id !== admin.user_id),
      );
      setNotice(`${admin.email} is no longer a Developer Administrator.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.breadcrumb}>
        Operations Center <span>›</span> Configuration
      </div>

      <div className={styles.eyebrow}>CONFIGURATION CONTROL • DEVELOPMENT (DEV)</div>
      <div className={styles.titleRow}>
        <div>
          <h1>Configuration</h1>
          <p>Control authorized users, security roles and governed application configuration.</p>
        </div>
        <div className={styles.environmentBadge}>
          <span className={styles.liveDot} />
          Development (DEV)
        </div>
      </div>

      <nav className={styles.tabs} aria-label="Configuration sections">
        <button className={styles.activeTab}>Users &amp; Access</button>
        <button disabled>Application</button>
        <button disabled>Security</button>
        <button disabled>Integrations</button>
      </nav>

      {(error || notice) && (
        <div className={error ? styles.alert : styles.notice} role="status">
          <strong>{error ? "Configuration action blocked." : "Configuration updated."}</strong>
          <span>{error ?? notice}</span>
          {error && <button onClick={() => void load()}>Retry</button>}
        </div>
      )}

      <section className={styles.grid}>
        <article className={styles.heroCard}>
          <div className={styles.cardIcon}><UsersIcon /></div>
          <div>
            <div className={styles.cardKicker}>USERS &amp; ACCESS</div>
            <h2>Developer Users</h2>
            <p>
              Manage the small, explicitly authorized developer population allowed
              to administer EasyWorld development infrastructure.
            </p>
          </div>
          <div className={styles.controlBadge}>
            <span>Controlled</span>
            <small>developer_admin.manage</small>
          </div>
        </article>

        <article className={styles.infoCard}>
          <div className={styles.infoIcon}><ShieldIcon /></div>
          <div>
            <h3>Authorization boundary</h3>
            <p>
              Role assignment remains server-authoritative. The frontend never
              grants permission locally and never bypasses a 403.
            </p>
          </div>
        </article>

        <article className={styles.infoCard}>
          <div className={styles.infoIcon}><DatabaseIcon /></div>
          <div>
            <h3>PostgreSQL role source</h3>
            <p>
              Developer Administrator assignments are persisted in the existing
              <code> auth_user_roles </code> table.
            </p>
          </div>
        </article>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <div className={styles.cardKicker}>AUTHORIZED DEVELOPER ADMINISTRATORS</div>
            <h2>Developer access</h2>
            <p>Only active, verified users should be granted this role.</p>
          </div>
          <button className={styles.secondaryButton} onClick={() => void load()} disabled={loading}>
            ↻ Refresh
          </button>
        </div>

        {loading ? (
          <div className={styles.emptyState}>Loading authorized developers…</div>
        ) : administrators.length === 0 ? (
          <div className={styles.emptyState}>
            <strong>No Developer Administrators are currently returned by the API.</strong>
            <span>This can indicate that the initial development administrator has not yet been bootstrapped.</span>
          </div>
        ) : (
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Status</th>
                  <th>Email verification</th>
                  <th>Role</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {administrators.map((admin) => (
                  <tr key={admin.user_id}>
                    <td>
                      <strong>{admin.email}</strong>
                      <small>{admin.username}</small>
                    </td>
                    <td><span className={styles.status}>{admin.status}</span></td>
                    <td>{admin.email_verified ? "Verified" : "Not verified"}</td>
                    <td><span className={styles.role}>Developer Admin</span></td>
                    <td>
                      <button
                        className={styles.dangerButton}
                        disabled={busy !== null || administrators.length <= 1}
                        title={administrators.length <= 1 ? "The last Developer Administrator cannot be removed." : undefined}
                        onClick={() => void revoke(admin)}
                      >
                        {busy === `revoke:${admin.user_id}` ? "Revoking…" : "Revoke"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className={styles.grantBox}>
          <div>
            <h3>Grant Developer Administrator</h3>
            <p>
              Enter the existing user UUID. The backend validates that the user
              exists, is active and has a verified email before changing PostgreSQL.
            </p>
          </div>
          <div className={styles.grantForm}>
            <input
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="User UUID"
              aria-label="User UUID"
            />
            <button
              className={styles.primaryButton}
              disabled={!userId.trim() || busy !== null}
              onClick={() => void grant()}
            >
              {busy?.startsWith("grant:") ? "Granting…" : "Grant access"}
            </button>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <span>EasyWorld • Configuration Control</span>
        <span>Changes are governed and auditable.</span>
      </footer>
    </main>
  );
}
