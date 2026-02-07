import { useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { clearAuthCookie } from '@/app/actions/auth';
import { routes } from './navigation';
import useUserStore, { useUser, useAuthToken, useUserActions, useHasHydrated } from '@/stores/useUserStore';
import { User } from './types'; // Assuming User type is now in lib/types

/**
 * Custom hook for authentication protection.
 * Reads auth state from the central Zustand store and redirects to login if unauthenticated.
 *
 * @returns Object with authentication state and user data from the store.
 */
export function useAuthProtection() {
    const router = useRouter();
    const token = useAuthToken();
    const user = useUser();

    // isLoading is true until the store is hydrated from localStorage
    const hasHydrated = useHasHydrated();
    const isLoading = !hasHydrated;

    useEffect(() => {
        // DEBUG: Trace client-side auth check
        console.log(`[useAuthProtection] Hydrated: ${!isLoading}, Token: ${!!token}`)

        // Once hydration is complete, check for token
        if (!isLoading && !token) {
            router.push(routes.login);
        }
    }, [token, isLoading, router]);

    return {
        isAuthenticated: !!token,
        isLoading: isLoading, // Return the local variable directly (true if not hydrated)
        user,
    };
}

/**
 * Logout function - clears all authentication data by calling the store action.
 */
export async function logout() {
    // Clear state from Zustand store (which also clears localStorage)
    useUserStore.getState().actions.logout();

    // Clear server-side cookie
    await clearAuthCookie();

    window.location.href = routes.login;
}

/**
 * Set authentication data in the Zustand store.
 * The store's persist middleware will handle localStorage.
 *
 * Note: Cookie is set separately via server action (setAuthCookie)
 */
export function setAuthData(token: string, user: User) {
    useUserStore.getState().actions.login(user, token);
}

export function decodeRoleFromToken(token?: string): string | null {
    if (!token) return null;
    try {
        const payload = token.split('.')[1];
        const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
        const decoded = JSON.parse(atob(base64));
        return decoded.role || null;
    } catch {
        return null;
    }
}

export function useAuthRole(): string | null {
    const token = useAuthToken();
    return useMemo(() => decodeRoleFromToken(token ?? undefined), [token]);
}

/**
 * TODO: SECURITY WARNING - For production:
 * 1. Use httpOnly cookies for token storage
 * 2. Implement refresh token rotation
 * 3. Add CSRF protection
 * 4. Use secure session management
 */
// The old getAuthToken and getCurrentUser functions are now removed.
// Components should use the hooks: useAuthToken() and useUser().
