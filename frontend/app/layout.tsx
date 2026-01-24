import "./global.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sentinel V1",
  description: "Enterprise AI Operations Decision System (V1)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
