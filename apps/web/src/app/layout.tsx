import { PageFooter } from "@/components/page-footer";
import { PageHeader } from "@/components/page-header";
import { AestheticBackground } from "@/components/ui/aesthetic-background";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const satoshi = localFont({
  src: "../styles/Satoshi-Variable.woff2",
  variable: "--font-satoshi",
  weight: "100 200 300 400 500 600 700 800 900",
  display: "swap",
  style: "normal",
});

const metadata: Metadata = {
  title: "Fact Checker | AI-powered factual verification",
  description:
    "Verify factual accuracy using our modular LangGraph system that extracts claims, cross-references them with real-world evidence, and provides a detailed verification report.",
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-icon.png",
  },
  keywords: [
    "fact checking",
    "AI verification",
    "claim extraction",
    "evidence analysis",
  ],
  authors: [{ name: "Fact Checker Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#ffffff",
};

const RootLayout = ({ children }: Readonly<React.PropsWithChildren>) => (
  <html lang="en" suppressHydrationWarning>
    <body
      className={cn(
        "bg-neutral-50 font-[family-name:var(--font-satoshi)] antialiased",
        "selection:bg-neutral-700 selection:text-white dark:selection:bg-white dark:selection:text-neutral-700",
        satoshi.variable,
        geistMono.variable
      )}
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-6 focus:top-6 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        Skip to main content
      </a>
      <AestheticBackground />
      <TooltipProvider>
        <div className="mx-auto flex min-h-screen max-w-5xl flex-col text-black">
          <PageHeader />
          {children}
          <PageFooter />
        </div>
      </TooltipProvider>
    </body>
  </html>
);

export default RootLayout;
