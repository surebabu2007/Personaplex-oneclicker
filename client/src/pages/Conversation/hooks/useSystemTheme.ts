import { useEffect, useState } from "react";

export type ThemeType = "light" | "dark";

export function useSystemTheme() {
  const getSystemPref = () =>
    window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";

  const [theme, setTheme] = useState<ThemeType>(getSystemPref);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    const applyTheme = (isDark: boolean) => {
      const newTheme = isDark ? "dark" : "light";
      setTheme(newTheme);
      document.documentElement.setAttribute("data-theme", newTheme);
    };

    // Initial apply (correct type: matches is boolean)
    applyTheme(media.matches);

    // Correct handler type
    const handleChange = (e: MediaQueryListEvent) => {
      applyTheme(e.matches);
    };

    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  return theme;
}