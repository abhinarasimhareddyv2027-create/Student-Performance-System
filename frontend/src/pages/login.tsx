import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Eye, EyeOff, LockKeyhole, UserRound } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { useAuth } from "../services/auth";

const schema = z.object({ username: z.string().min(1, "Enter your username."), password: z.string().min(1, "Enter your password.") });
type LoginValues = z.infer<typeof schema>;

export function LoginPage() {
  const { signIn } = useAuth();
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<LoginValues>({ resolver: zodResolver(schema) });

  const submit = handleSubmit(async ({ username, password }) => {
    setError("");
    setSubmitting(true);
    try {
      await signIn(username, password);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed.");
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <main className="login-page">
      <section className="login-art" aria-label="Campus performance overview">
        <div className="art-grid" />
        <div className="art-topline"><span className="brand-mark"><span>SP</span></span><span>NORTHSTAR / 01</span></div>
        <div className="art-content"><p className="eyebrow">STUDENT & EMPLOYEE PERFORMANCE</p><h1>Measure what<br /><em>moves you forward.</em></h1><p className="art-desc">A clear view of learning, contribution, and progress across your institution.</p>
          <div className="art-stat-row"><div><strong>01</strong><span>Connected workspace</span></div><div><strong>LIVE</strong><span>Secure records</span></div></div>
        </div>
        <div className="art-foot"><span>PERFORMANCE OFFICE</span><span>EST. 2026</span></div>
      </section>
      <section className="login-panel">
        <div className="login-panel-top"><span className="login-mark"><UserRound className="size-4" /></span><span>STAFF PORTAL</span></div>
        <div className="login-form-wrap"><p className="eyebrow">WELCOME BACK</p><h2>Sign in to your<br />workspace</h2><p className="login-help">Use the administrator or staff account configured for this system.</p>
          <form className="login-form" onSubmit={submit}>
            <label htmlFor="username">Username</label><div className="field-shell"><UserRound className="field-icon size-4" /><Input id="username" autoComplete="username" placeholder="Your username" aria-invalid={Boolean(errors.username)} {...register("username")} /></div>
            {errors.username && <span className="field-error">{errors.username.message}</span>}
            <label htmlFor="password">Password</label><div className="field-shell"><LockKeyhole className="field-icon size-4" /><Input id="password" autoComplete="current-password" type={showPassword ? "text" : "password"} placeholder="Your password" aria-invalid={Boolean(errors.password)} {...register("password")} /><button className="password-toggle" type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div>
            {errors.password && <span className="field-error">{errors.password.message}</span>}
            {error && <div role="alert" className="form-alert">{error}</div>}
            <Button type="submit" className="login-submit" disabled={submitting}>{submitting ? "Signing in…" : "Continue"}<ArrowRight className="size-4" /></Button>
          </form>
        </div>
        <div className="login-panel-foot"><span>LOCAL INSTITUTIONAL ACCESS</span><span>© 2026 NORTHSTAR</span></div>
      </section>
    </main>
  );
}