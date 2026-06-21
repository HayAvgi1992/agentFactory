"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function PersistedStatus() {
  const [leadCount, setLeadCount] = useState<number | null>(null);
  const [persisted, setPersisted] = useState(false);

  useEffect(() => {
    api
      .getHealth()
      .then((health) => {
        setLeadCount(health.lead_count);
        setPersisted(health.persisted);
      })
      .catch(() => {
        setLeadCount(null);
        setPersisted(false);
      });
  }, []);

  if (leadCount === null && !persisted) {
    return null;
  }

  const label =
    leadCount === 0
      ? "SQLite · no leads stored yet"
      : `${leadCount} lead${leadCount === 1 ? "" : "s"} stored in SQLite`;

  return (
    <div className="persisted-status" title="Leads survive page refresh and server restarts">
      <span className="persisted-dot" aria-hidden="true" />
      <span className="persisted-label">Persisted</span>
      <span className="persisted-count">{label}</span>
    </div>
  );
}
