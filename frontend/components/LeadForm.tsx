"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Lead } from "@/lib/api";

interface LeadFormProps {
  onSubmitted: (lead: Lead) => void;
  onProcessingChange?: (processing: boolean) => void;
  onPipelineStart?: () => void;
  onPipelineFailure?: (failedStep: number) => void;
}

const SAMPLE_LEADS = [
  {
    company_name: "Acme",
    industry: "SaaS",
    company_size: "100",
    message: "We are looking for a project management solution.",
  },
  {
    company_name: "GreenEnergy Ltd",
    industry: "CleanTech",
    company_size: "10-50",
    message: "Saw your product mentioned in a blog. Can you send more info?",
  },
];

export function LeadForm({
  onSubmitted,
  onProcessingChange,
  onPipelineStart,
  onPipelineFailure,
}: LeadFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    company_name: "",
    industry: "",
    company_size: "",
    message: "",
  });

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const loadSample = (index: number) => {
    setForm(SAMPLE_LEADS[index]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    onPipelineStart?.();
    onProcessingChange?.(true);
    setError("");
    try {
      const lead = await api.submitLead({
        company_name: form.company_name,
        industry: form.industry || null,
        company_size: form.company_size || null,
        message: form.message,
      });
      onSubmitted(lead);
      setForm({ company_name: "", industry: "", company_size: "", message: "" });
    } catch (err) {
      if (err instanceof ApiError && err.failedStep !== undefined) {
        onPipelineFailure?.(err.failedStep);
      } else if (err instanceof ApiError) {
        onPipelineFailure?.(0);
      }
      setError(err instanceof Error ? err.message : "Failed to submit lead");
    } finally {
      setLoading(false);
      onProcessingChange?.(false);
    }
  };

  return (
    <form className="lead-form" onSubmit={handleSubmit}>
      <div className="sample-buttons">
        <button type="button" className="btn-secondary" onClick={() => loadSample(0)}>
          Load: Acme (from vision doc)
        </button>
        <button type="button" className="btn-secondary" onClick={() => loadSample(1)}>
          Load: Weak Lead
        </button>
      </div>

      <div className="form-grid">
        <label>
          Company Name *
          <input
            required
            value={form.company_name}
            onChange={(e) => update("company_name", e.target.value)}
            placeholder="Acme"
          />
        </label>
        <label>
          Industry
          <input
            value={form.industry}
            onChange={(e) => update("industry", e.target.value)}
            placeholder="SaaS"
          />
        </label>
        <label>
          Company Size (Employees)
          <input
            value={form.company_size}
            onChange={(e) => update("company_size", e.target.value)}
            placeholder="100"
          />
        </label>
      </div>

      <label>
        Lead Message *
        <textarea
          required
          rows={4}
          value={form.message}
          onChange={(e) => update("message", e.target.value)}
          placeholder="We are looking for a project management solution."
        />
      </label>

      {error && <p className="error">{error}</p>}

      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? "Running Agents..." : "Submit Lead"}
      </button>
    </form>
  );
}
