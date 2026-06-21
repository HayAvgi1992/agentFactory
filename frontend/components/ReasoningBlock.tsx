"use client";

function ReasoningBlock({
  reasoning,
  patterns,
  tradeoffs,
  extra,
}: {
  reasoning?: string;
  patterns?: string[];
  tradeoffs?: string[];
  extra?: React.ReactNode;
}) {
  if (!reasoning && !patterns?.length && !tradeoffs?.length && !extra) {
    return null;
  }
  return (
    <div className="reasoning-block">
      {reasoning && <p className="reasoning-text">{reasoning}</p>}
      {patterns && patterns.length > 0 && (
        <p>
          <strong>Patterns:</strong> {patterns.join(" · ")}
        </p>
      )}
      {tradeoffs && tradeoffs.length > 0 && (
        <p>
          <strong>Tradeoffs:</strong> {tradeoffs.join(" · ")}
        </p>
      )}
      {extra}
    </div>
  );
}

export { ReasoningBlock };
