import type { ReactNode } from "react";
import styles from "./OperationsCenterLayout.module.css";

interface OperationsCenterLayoutProps {
  children: ReactNode;
}

export default function OperationsCenterLayout({ children }: OperationsCenterLayoutProps) {
  return (
    <main className={styles.canvas}>
      <div className={styles.container}>{children}</div>
    </main>
  );
}
