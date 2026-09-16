/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PRIVACY_GOVERNANCE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "*.css";
declare module "*.scss";
declare module "*.sass";