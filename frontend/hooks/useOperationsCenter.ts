import { useEffect, useState } from "react";
import {
  getGovernanceStatus,
  getGovernanceTimeline,
  getProviderStatus,
} from "../services/operationsCenterService";

export function useOperationsCenter() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getGovernanceStatus(),
      getGovernanceTimeline(),
      getProviderStatus(),
    ])
      .then(([governance, timeline, provider]) => {
        setData({ governance, timeline, provider });
      })
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}