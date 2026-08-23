import { useEffect, useState } from "react";
import {
  getGovernanceStatus,
  GovernanceStatus,
} from "../services/governanceApi";

export function useGovernanceStatus() {
  const [data, setData] = useState<GovernanceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    getGovernanceStatus()
      .then((result) => {
        if (mounted) setData(result);
      })
      .catch((requestError: Error) => {
        if (mounted) setError(requestError.message);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return { data, loading, error };
}
