import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import { loginUser, registerUser } from "../services/authService";
import { LanguageSelector } from "../components";
import { Eye, EyeOff, Mail, Lock, ArrowLeft, Sun, Moon } from "lucide-react";
import { useTheme } from "../hooks/useTheme";

type AuthMode = "login" | "signup";

export default function AuthPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { refreshUser, refreshSettings } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setError("");
    setSuccessMessage("");
  };

  const switchMode = (newMode: AuthMode) => {
    resetForm();
    setMode(newMode);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    // Validation
    if (!email.trim() || !password.trim()) {
      setError(t("auth.errors.emptyFields"));
      return;
    }

    if (mode === "signup") {
      if (password.length < 8) {
        setError(t("auth.errors.passwordTooShort"));
        return;
      }
      if (password !== confirmPassword) {
        setError(t("auth.errors.passwordMismatch"));
        return;
      }
    }

    setIsSubmitting(true);

    try {
      if (mode === "signup") {
        await registerUser({ email, password });
        setSuccessMessage(t("auth.signupSuccess"));
        // Auto-switch to login after successful registration
        setTimeout(() => {
          switchMode("login");
          setEmail(email); // Keep the email filled
        }, 1500);
      } else {
        await loginUser({ email, password });
        const [currentUser, userSettings] = await Promise.all([
          refreshUser(),
          refreshSettings()
        ]);

        // Check if user needs API key setup (non-admin without key)
        if (
          currentUser &&
          currentUser.role !== "admin" &&
          !userSettings?.has_api_key
        ) {
          navigate("/profile?setup=true");
          return;
        }

        navigate("/");
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(t("auth.errors.generic"));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2">
            <ArrowLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <h1 className="text-2xl font-bold dark:text-gray-200">
              Prof
              <span className="text-blue-600 dark:text-blue-400">
                Assistant
              </span>
            </h1>
          </Link>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
              aria-label={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
            >
              {theme === "dark" ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
            <div className="w-40">
              <LanguageSelector variant="header" />
            </div>
          </div>
        </div>
      </header>

      {/* Auth form */}
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
            {/* Tab switcher */}
            <div className="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-1 mb-8">
              <button
                type="button"
                className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-colors ${
                  mode === "login"
                    ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                }`}
                onClick={() => switchMode("login")}
              >
                {t("auth.loginTab")}
              </button>
              <button
                type="button"
                className={`flex-1 py-2.5 text-sm font-medium rounded-md transition-colors ${
                  mode === "signup"
                    ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                }`}
                onClick={() => switchMode("signup")}
              >
                {t("auth.signupTab")}
              </button>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-200 mb-2">
              {mode === "login" ? t("auth.loginTitle") : t("auth.signupTitle")}
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {mode === "login"
                ? t("auth.loginSubtitle")
                : t("auth.signupSubtitle")}
            </p>

            {/* Error / Success messages */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm rounded-lg">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="mb-4 p-3 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 text-sm rounded-lg">
                {successMessage}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                >
                  {t("auth.email")}
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t("auth.emailPlaceholder")}
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                >
                  {t("auth.password")}
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t("auth.passwordPlaceholder")}
                    className="w-full pl-10 pr-12 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
                    autoComplete={
                      mode === "login" ? "current-password" : "new-password"
                    }
                    required
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {mode === "signup" && (
                  <p className="mt-1 text-xs text-gray-400">
                    {t("auth.passwordHint")}
                  </p>
                )}
              </div>

              {/* Confirm password (signup only) */}
              {mode === "signup" && (
                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                  >
                    {t("auth.confirmPassword")}
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="confirmPassword"
                      type={showPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder={t("auth.confirmPasswordPlaceholder")}
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
                      autoComplete="new-password"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 bg-blue-600 dark:bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting
                  ? t("auth.submitting")
                  : mode === "login"
                    ? t("auth.loginButton")
                    : t("auth.signupButton")}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
