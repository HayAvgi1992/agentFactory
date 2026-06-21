import type { Metadata } from "next";
import { PersistedStatus } from "@/components/PersistedStatus";
import { Figtree } from "next/font/google";
import "./globals.css";

const figtree = Figtree({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "GTM Agent Factory — Portfolio Demo",
  description: "7-agent LangGraph GTM pipeline with RAG, observability, A/B prompts, and HITL",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" dir="ltr">
      <body className={figtree.className}>
        <header className="header">
          <div className="header-inner">
            <div className="logo">
              <div className="logo-dots" aria-hidden="true">
                <span className="dot dot-red" />
                <span className="dot dot-yellow" />
                <span className="dot dot-green" />
              </div>
              <div>
                <h1>
                  GTM Agent Factory
                  <span className="logo-by">by Hay Avgi - RevAI Developer on Monday</span>
                </h1>
                <p>Portfolio demo · 7-agent LangGraph · RAG · Observability · A/B · HITL</p>
              </div>
            </div>
            <nav className="nav-tags">
              <PersistedStatus />
              <span className="tag tag-red">FastAPI</span>
              <span className="tag tag-yellow">OpenAI</span>
              <span className="tag tag-green">Next.js</span>
            </nav>
          </div>
        </header>
        <main className="main">{children}</main>
      </body>
    </html>
  );
}
