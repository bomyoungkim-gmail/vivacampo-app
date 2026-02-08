import { AdminSidebar } from "@/components/AdminSidebar";
import { ErrorBoundary } from "@/components/ErrorBoundary";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen bg-background">
            <AdminSidebar />
            <main className="flex-1 max-h-screen overflow-y-auto">
                <ErrorBoundary>
                    <div className="container mx-auto p-8 animate-fade-in-up">
                        {children}
                    </div>
                </ErrorBoundary>
            </main>
        </div>
    );
}
