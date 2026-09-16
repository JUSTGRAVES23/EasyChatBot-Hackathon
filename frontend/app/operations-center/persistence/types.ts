export type Environment = "dev" | "staging" | "production";

export type DatabaseStatus = {
  connected: boolean;
  environment: string;
  database: string | null;
  host: string | null;
  port: number | null;
  postgres_version: string | null;
  latency_ms: number | null;
  database_size_bytes: number | null;
  active_connections: number | null;
  max_connections: number | null;
  connection_utilisation_pct: number | null;
  uptime: string | null;
  ssl_enabled: boolean | null;
  checked_at: string;
  error: string | null;
};

export type MigrationStatus = {
  graph: "IN_SYNC" | "PENDING" | "INCONSISTENT" | "ERROR" | "UNKNOWN";
  database_revisions: string[];
  repository_heads: string[];
  missing_revisions: string[];
  pending_migrations: string[] | null;
  drift: boolean;
  migration_safety: Array<{ revision: string; risk: string; reasons: string[]; analysis_mode?: string }>;
  migration_history: Array<{ revision: string; down_revision: string[]; status: string }>;
  checked_at: string;
  error: string | null;
};

export type SchemaStatus = {
  state: "IN_SYNC" | "DRIFT_DETECTED" | "UNKNOWN" | "ERROR";
  tables_inspected: number;
  tables_with_drift: number;
  differences: Array<{
    table: string;
    kind: string;
    name: string;
    expected: string | null;
    actual: string | null;
  }>;
  checked_at: string;
  error: string | null;
};

export type CompatibilityStatus = {
  application_version: string | null;
  expected_schema_revision: string | null;
  actual_database_revisions: string[];
  state: "COMPATIBLE" | "OUT_OF_SYNC" | "NOT_CONFIGURED";
  source: string;
};

export type LastAction = {
  source: string;
  functionality_id: string;
  environment: string;
  action: string;
  availability: string;
  actor: string;
  reason: string | null;
  changed_at: string | null;
};

export type Recommendation = {
  severity: "INFO" | "MEDIUM" | "HIGH" | "CRITICAL";
  timing: "NO_ACTION_REQUIRED" | "BEFORE_NEXT_DEPLOYMENT" | "DO_NOW" | "STOP_DO_NOT_PROCEED";
  title: string;
  summary: string;
  why: string;
  impact: string;
  next_actions: string[];
  blocked_actions: string[];
};

export type PersistenceSnapshot = {
  environment: Environment;
  checked_at: string;
  database: DatabaseStatus;
  migration: MigrationStatus;
  schema: SchemaStatus;
  compatibility: CompatibilityStatus;
  last_action: LastAction | null;
  recommendation: Recommendation;
};

export type HealthSnapshot = {
  environment: Environment;
  checked_at: string;
  database: DatabaseStatus;
  status: string;
  error?: string | null;
  performance: {
    status: string;
    cache_hit_ratio_pct: number | null;
    transactions_committed: number | null;
    transactions_rolled_back: number | null;
    rows_returned: number | null;
    rows_fetched: number | null;
    query_statistics: string;
    slow_queries: Array<{ mean_ms: number; calls: number; total_ms: number; query: string }>;
  };
  locks: {
    status: string;
    blocking_detected: boolean;
    blocked_queries: Array<Record<string, unknown>>;
    long_running_transactions: Array<Record<string, unknown>>;
    active_transactions: number | null;
  };
  indexes: {
    status: string;
    total_indexes: number | null;
    unused_index_count: number | null;
    unused_indexes: Array<Record<string, unknown>>;
    invalid_indexes: number | null;
    largest_indexes: Array<Record<string, unknown>>;
  };
  maintenance: {
    status: string;
    tables: Array<Record<string, unknown>>;
    tables_with_dead_tuples: number | null;
    autovacuum: string | null;
    track_counts: string | null;
  };
  backup_recovery: {
    backup_integration: string;
    last_backup: string | null;
    backup_status: string;
    restore_verification: string;
    point_in_time_recovery: string;
    archive_mode: string | null;
    wal_level: string | null;
  };
  integrity: {
    status: string;
    foreign_key_constraints: number | null;
    check_constraints: number | null;
    application_integrity_checks: string;
  };
  security: {
    status: string;
    current_role: string | null;
    ssl_enabled: boolean | null;
    is_superuser: boolean | null;
    can_create_role: boolean | null;
    can_create_database: boolean | null;
    can_login: boolean | null;
    pg_hba_analysis: string;
  };
  replication: {
    status: string;
    is_standby: boolean | null;
    replica_count: number | null;
    wal_level: string | null;
    archive_mode: string | null;
  };
  recent_activity: Array<Record<string, unknown>>;
};
