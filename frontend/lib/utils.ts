/** monday.com brand palette — https://www.brandcolorcode.com/monday-com */
export const MONDAY = {
  red: "#FB275D",
  yellow: "#FFCC00",
  green: "#00CA72",
  text: "#323338",
  textMuted: "#676879",
  bg: "#f6f7fb",
  border: "#d0d4e4",
} as const;

export const ACTION_LABELS: Record<
  string,
  { label: string; color: string; textColor?: string }
> = {
  book_meeting: { label: "Book Meeting", color: "hsla(240, 100%, 69.02%, 1)" },
  send_email: { label: "Send Email", color: MONDAY.red },
  nurture: { label: "Nurture", color: MONDAY.yellow, textColor: MONDAY.text },
  reject: { label: "Reject", color: MONDAY.red },
  human_review: { label: "Human Review", color: MONDAY.yellow, textColor: MONDAY.text },
};

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
