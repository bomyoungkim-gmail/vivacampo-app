import { AdminSidebar } from "@/components/AdminSidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-100 via-slate-200 to-slate-200">
            <AdminSidebar />
            <main className="flex-1 max-h-screen overflow-y-auto">
                <div className="container mx-auto p-8 animate-fade-in-up">
                    {children}
                </div>
            </main>
        </div>
    );
}
