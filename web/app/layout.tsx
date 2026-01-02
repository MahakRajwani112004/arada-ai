import type { Metadata } from "next";
import localFont from "next/font/local";
import { Toaster } from "sonner";
import { Providers } from "@/lib/providers";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "MagOneAI - Agent Platform",
  description: "Create and manage AI agents with MCP integrations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <Providers>
          {children}
          <Toaster
            position="bottom-right"
            toastOptions={{
              classNames: {
                toast: "bg-card border-border",
                title: "text-foreground",
                description: "text-muted-foreground",
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
