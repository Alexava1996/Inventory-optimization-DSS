import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Scorta | Il tuo magazzino, sotto controllo",
  description:
    "Gestisci articoli, scorte e previsioni di riordino con il motore Inventory DSS.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
