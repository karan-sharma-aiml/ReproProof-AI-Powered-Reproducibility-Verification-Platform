import type { Metadata } from "next";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { ThemeProvider } from "@/hooks/useTheme";
import { ToastProvider } from "@/hooks/useToast";
import { ToastContainer } from "@/components/ui/ToastContainer";
import "./globals.css";

export const metadata: Metadata = {
    title: "ReproProof | Reproducibility verification",
    description: "Autonomous research reproducibility verification platform.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body>
                <ThemeProvider>
                    <ToastProvider>
                        <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,0.1),_transparent_32rem)] dark:bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,0.15),_transparent_32rem)]">
                            <Header />
                            {children}
                            <Footer />
                        </div>
                        <ToastContainer />
                    </ToastProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}