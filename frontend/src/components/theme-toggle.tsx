import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "./ui/button";

export function ThemeToggle() {
  const [light, setLight] = useState(false);

  useEffect(() => {
    const saved = window.localStorage.getItem("spms-theme");
    const isLight = saved === "light";
    setLight(isLight);
    document.documentElement.classList.toggle("light", isLight);
  }, []);

  const toggle = () => {
    const next = !light;
    setLight(next);
    document.documentElement.classList.toggle("light", next);
    window.localStorage.setItem("spms-theme", next ? "light" : "dark");
  };

  return <Button variant="ghost" size="icon" aria-label={`Switch to ${light ? "dark" : "light"} theme`} onClick={toggle}>{light ? <Moon className="size-4" /> : <Sun className="size-4" />}</Button>;
}