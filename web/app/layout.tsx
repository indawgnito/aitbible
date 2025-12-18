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
          <footer className="container-reading py-12 text-center text-sm text-neutral-500">
            <p>
              AIT Bible Translation · Built with care for accuracy and meaning
            </p>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
