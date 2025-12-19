import type { Metadata } from "next";
import { Header } from "@/components/Header";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIT Bible | AI Translation",
  description:
    "A fresh translation of the Bible from the original Greek, prioritizing accuracy and meaning over tradition.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning is required by next-themes
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen">
        <Providers>
          <Header />
          <main>{children}</main>
          <footer className="container-reading py-12 text-center text-sm text-neutral-500 dark:text-neutral-400">
            <p className="mb-2">
              © 2025 AIT Bible Project
            </p>
            <p className="text-xs">
              Translation licensed under{" "}
              <a
                href="https://creativecommons.org/licenses/by-nc-sa/4.0/"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-neutral-700 dark:hover:text-neutral-300"
              >
                CC BY-NC-SA 4.0
              </a>
            </p>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
