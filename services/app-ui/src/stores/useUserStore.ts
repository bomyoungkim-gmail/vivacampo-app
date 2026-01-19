import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User } from '../lib/types'; // Assuming User type is exported from lib/types

interface UserState {
  user: User | null;
  token: string | null;
  _hasHydrated: boolean;
  actions: {
    login: (user: User, token: string) => void;
    logout: () => void;
    setUser: (user: User) => void;
    setHasHydrated: (state: boolean) => void;
  };
}

const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      _hasHydrated: false,
      actions: {
        login: (user, token) => {
          set({ user, token });
          // The token itself is persisted by the middleware
        },
        logout: () => {
          set({ user: null, token: null });
          // The middleware will clear the persisted token
        },
        setUser: (user) => set({ user }),
        setHasHydrated: (state) => set({ _hasHydrated: state }),
      },
    }),
    {
      name: 'auth-storage', // name of the item in storage (must be unique)
      storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
      partialize: (state) => ({
        token: state.token,
        user: state.user
      }), // Persist token AND user profile
      onRehydrateStorage: () => (state) => {
        state?.actions.setHasHydrated(true);
      },
    }
  )
);

export const useUserActions = () => useUserStore((state) => state.actions);
export const useUser = () => useUserStore((state) => state.user);
export const useAuthToken = () => useUserStore((state) => state.token);
export const useHasHydrated = () => useUserStore((state) => state._hasHydrated);

export default useUserStore;