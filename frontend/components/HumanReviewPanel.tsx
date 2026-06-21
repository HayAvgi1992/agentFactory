"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { Lead } from "@/lib/api";

interface HumanReviewPanelProps {
  lead: Lead;
  onUpdated: (lead: Lead) => void;
}

export function HumanReviewPanel({ lead, onUpdated }: HumanReviewPanelProps) {
  const needsReview = lead.results?.evaluation?.needs_human_review;
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!needsReview && !lead.human_review_status) {
    return null;
  }

  const submit = async (decision: "approve" | "reject") => {
    setLoading(true);
    setError("");
    try {
      const updated = await api.submitHumanReview(lead.id, decision, notes || undefined);
      onUpdated(updated);
    } catch {
      setError("Failed to submit review decision.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="human-review-panel">
      <h4>Human Review Required</h4>
      {lead.human_review_status ? (
        <p>
          Decision: <strong>{lead.human_review_status}</strong>
          {lead.human_review_notes && <> — {lead.human_review_notes}</>}
        </p>
      ) : (
        <>
          <p className="meta">
            Evaluation flagged this pipeline for human review before production action.
          </p>
          <textarea
            rows={2}
            placeholder="Optional review notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="review-actions">
            <button
              type="button"
              className="btn-primary"
              disabled={loading}
              onClick={() => submit("approve")}
            >
              Approve
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={loading}
              onClick={() => submit("reject")}
            >
              Reject
            </button>
          </div>
        </>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
