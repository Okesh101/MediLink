import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      actorType: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: ({ user, actorType, accessToken, refreshToken }) =>
        set({
          user,
          actorType,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),

      setAccessToken: (accessToken) => set({ accessToken }),

      setUser: (user) => set({ user }),

      logout: () =>
        set({
          user: null,
          actorType: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),

      homePath: () => {
        const type = get().actorType;
        if (type === "hospital_admin") return "/hospital";
        if (type === "staff") return "/staff";
        if (type === "patient") return "/patient";
        return "/";
      },
    }),
    {
      name: "medilink-auth",
      partialize: (state) => ({
        user: state.user,
        actorType: state.actorType,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
