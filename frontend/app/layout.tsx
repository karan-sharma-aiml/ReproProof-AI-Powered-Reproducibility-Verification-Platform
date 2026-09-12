import type { Metadata } from "next";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { LayoutEnhancements } from "@/components/layout/LayoutEnhancements";
import { FloatingAssistant } from "@/components/layout/FloatingAssistant";
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
                        <div className="min-h-screen bg-slate-50 dark:bg-[#070B17]">
                            <Header />
                            {children}
                            <Footer />
                        </div>
                        <ToastContainer />
                        <LayoutEnhancements />
                        <FloatingAssistant />
                    </ToastProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}