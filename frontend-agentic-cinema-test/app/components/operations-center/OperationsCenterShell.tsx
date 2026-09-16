import type { ReactNode } from "react";
import OperationsCenterLayout from "./OperationsCenterLayout";
import OperationsCenterSidebar from "./navigation/OperationsCenterSidebar";
import styles from "./OperationsCenterShell.module.css";

interface OperationsCenterShellProps {
  children: ReactNode;
}

export default function OperationsCenterShell({ children }: OperationsCenterShellProps) {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <OperationsCenterSidebar />
      </aside>
      <div className={styles.main}>
        <OperationsCenterLayout>{children}</OperationsCenterLayout>
      </div>
    </div>
  );
}
