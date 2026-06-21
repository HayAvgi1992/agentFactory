"use client";

import type { KnowledgeBaseResponse } from "@/lib/api";

interface KnowledgeBasePanelProps {
  knowledge: KnowledgeBaseResponse | null;
}

export function KnowledgeBasePanel({ knowledge }: KnowledgeBasePanelProps) {
  if (!knowledge) {
    return <p className="empty">Knowledge base unavailable.</p>;
  }

  return (
    <div className="knowledge-base">
      <p className="knowledge-base-meta">
        {knowledge.total_documents} documents ·{" "}
        {knowledge.valid ? "structure valid" : "missing folders"}
      </p>
      <div className="knowledge-sources">
        {knowledge.sources.map((source) => (
          <div key={source.source} className="knowledge-source-card">
            <h4>{source.label}</h4>
            <p className="knowledge-simulates">Simulates: {source.simulates}</p>
            <p className="knowledge-docs">
              {source.document_count > 0
                ? source.documents.join(", ")
                : "No documents"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
