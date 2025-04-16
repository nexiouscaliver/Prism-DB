import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrismDB | Transform Natural Language into Data Insights",
  description: "A multi-agent framework that acts as a contextual prism for databases, transforming raw natural language queries into structured insights, visual reports, and actionable diagrams.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-black">
        {children}
      </body>
    </html>
  );
}
