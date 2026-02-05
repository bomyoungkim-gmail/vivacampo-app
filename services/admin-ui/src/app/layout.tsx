import type { Metadata } from "next";
import { Fira_Sans, Fira_Code } from "next/font/google";
import "./globals.css";

const firaSans = Fira_Sans({
    subsets: ["latin"],
    weight: ["300", "400", "500", "600", "700"],
    variable: "--font-sans",
    display: "swap",
});

const firaCode = Fira_Code({
    subsets: ["latin"],
    weight: ["400", "500", "600"],
    variable: "--font-mono",
    display: "swap",
});

export const metadata: Metadata = {
    title: "VivaCampo Admin - System Administration",
    description: "Admin portal for VivaCampo platform management",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="pt-BR">
            <body className={`${firaSans.variable} ${firaCode.variable} font-sans`}>
                {children}
            </body>
        </html>
    );
}
