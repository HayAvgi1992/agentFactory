"use client";

import { useEffect, useState } from "react";
import type { Lead } from "@/lib/api";
import { PIPELINE_STEP_MS } from "@/lib/api";

const STEPS = [
  {
    id: "input",
    icon: "📥",
    label: "Lead Input",
    output: "company, industry, size, message",
  },
  {
    id: "planner",
    icon: "🗺️",
    label: "Planner Agent",
    output: "required_sources",
  },
  {
    id: "research",
    icon: "🔍",
    label: "Research Agent",
    output: "retrieved documents",
  },
  {
    id: "qualification",
    icon: "📊",
    label: "Qualification Agent",
    output: "score · signals · risks",
  },
  {
    id: "product_fit",
    icon: "📦",
    label: "Product Fit Agent",
    output: "recommended product",
  },
  {
    id: "outreach",
    icon: "✉️",
    label: "Outreach Agent",
    output: "email · linkedin · questions",
  },
  {
    id: "recommendation",
    icon: "🎯",
    label: "Recommendation Agent",
    output: "next_action",
  },
  {
    id: "evaluation",
    icon: "✅",
    label: "Evaluation Agent",
    output: "confidence · human review",
  },
] as const;

type StepVisualStatus = "idle" | "active" | "done" | "failed";

interface PipelineDiagramProps {
  activeLead?: Lead | null;
  isProcessing?: boolean;
  failedStep?: number | null;
}

function getStepStatus(
  index: number,
  currentStep: number,
  isProcessing: boolean,
  completed: boolean,
  failedStep: number | null,
): StepVisualStatus {
  if (failedStep !== null) {
    if (index < failedStep) return "done";
    if (index === failedStep) return "failed";
    return "idle";
  }
  if (completed) return "done";
  if (!isProcessing) return "idle";
  if (index < currentStep) return "done";
  if (index === currentStep) return "active";
  return "idle";
}

export function PipelineDiagram({
  activeLead,
  isProcessing = false,
  failedStep = null,
}: PipelineDiagramProps) {
  const results = activeLead?.results;
  const completed = Boolean(results) && failedStep === null && !isProcessing;
  const [currentStep, setCurrentStep] = useState(-1);

  useEffect(() => {
    if (failedStep !== null || !isProcessing) {
      if (!isProcessing && !completed && failedStep === null) {
        setCurrentStep(-1);
      }
      return;
    }

    setCurrentStep(0);
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev >= STEPS.length - 1 ? prev : prev + 1));
    }, PIPELINE_STEP_MS);

    return () => clearInterval(interval);
  }, [isProcessing, completed, failedStep]);

  useEffect(() => {
    if (completed) {
      setCurrentStep(STEPS.length - 1);
    }
  }, [completed]);

  return (
    <div className="pipeline-diagram">
      <p className="pipeline-diagram-intro">
        8-step agentic workflow — each step runs for ~2s. Green = progress, red = failure.
      </p>

      <div className="pipeline-track">
        {STEPS.map((step, index) => {
          const status = getStepStatus(
            index,
            currentStep,
            isProcessing,
            completed,
            failedStep,
          );

          return (
            <div key={step.id} className="pipeline-track-item">
              <div className={`pipeline-node pipeline-node-${status}`}>
                {status === "active" && (
                  <span className="pipeline-node-loader" aria-hidden="true" />
                )}
                <span className="pipeline-node-icon">{step.icon}</span>
                <span className="pipeline-node-label">{step.label}</span>
                <span className="pipeline-node-output">{step.output}</span>
                {completed && results && step.id === "qualification" && (
                  <span className="pipeline-node-result">
                    {results.qualification.score}/100 ·{" "}
                    {results.qualification.qualified ? "Qualified" : "Not qualified"}
                  </span>
                )}
                {completed && results && step.id === "product_fit" && results.product_fit && (
                  <span className="pipeline-node-result">
                    → {results.product_fit.recommended_product}
                  </span>
                )}
                {completed && results && step.id === "recommendation" && results.recommendation && (
                  <span className="pipeline-node-result">
                    → {results.recommendation.next_action.replace(/_/g, " ")}
                  </span>
                )}
                {completed && results && step.id === "evaluation" && results.evaluation && (
                  <span className="pipeline-node-result">
                    {Math.round(results.evaluation.confidence * 100)}% confidence
                  </span>
                )}
                {status === "failed" && (
                  <span className="pipeline-node-error">Step failed</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="pipeline-legend">
        <span className="legend-item">
          <span className="legend-dot idle" /> Pending
        </span>
        <span className="legend-item">
          <span className="legend-dot active" /> Running
        </span>
        <span className="legend-item">
          <span className="legend-dot done" /> Complete
        </span>
        <span className="legend-item">
          <span className="legend-dot failed" /> Failed
        </span>
      </div>
    </div>
  );
}
