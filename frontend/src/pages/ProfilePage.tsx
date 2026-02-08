import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import { updateUserSettings } from "../services/authService";
import { LanguageSelector } from "../components";
import {
  User,
  Key,
  Check,
  Loader2,
  ShieldCheck,
  ShieldX,
  AlertTriangle,
  Home,
  Rocket
} from "lucide-react";

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user, logout, settings, isLoadingSettings, refreshSettings } =
    useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const isSetupMode = searchParams.get("setup") === "true";

  const [showSetupBanner, setShowSetupBanner] = useState(false);

  // API key form
  const [apiKey, setApiKey] = useState("");
  const [isSavingKey, setIsSavingKey] = useState(false);
  const [keySaveSuccess, setKeySaveSuccess] = useState(false);
  const [keySaveError, setKeySaveError] = useState("");

  useEffect(() => {
    if (!isLoadingSettings && settings) {
      if (isSetupMode && !settings.has_api_key && user?.role !== "admin") {
        setShowSetupBanner(true);
      }
    } else if (!isLoadingSettings && !settings) {
      if (isSetupMode && user?.role !== "admin") {
        setShowSetupBanner(true);
      }
    }
  }, [isLoadingSettings, settings, isSetupMode, user?.role]);

  const handleSaveApiKey = async () => {
    setKeySaveError("");
    setKeySaveSuccess(false);

    if (!apiKey.trim()) {
      setKeySaveError(t("profile.errors.emptyApiKey"));
      return;
    }

    setIsSavingKey(true);
    try {
      await updateUserSettings({ openai_api_key: apiKey });
      await refreshSettings();
      setApiKey("");
      setKeySaveSuccess(true);
      setShowSetupBanner(false);
      // Clear setup query param if present
      if (isSetupMode) {
        setSearchParams({}, { replace: true });
      }
      setTimeout(() => setKeySaveSuccess(false), 3000);
    } catch (err) {
      setKeySaveError(
        err instanceof Error ? err.message : t("profile.errors.saveFailed")
      );
    } finally {
      setIsSavingKey(false);
    }
  };

  const handleRemoveApiKey = async () => {
    setKeySaveError("");
    setIsSavingKey(true);
    try {
      await updateUserSettings({ openai_api_key: "" });
      await refreshSettings();
      setKeySaveSuccess(true);
      setTimeout(() => setKeySaveSuccess(false), 3000);
    } catch (err) {
      setKeySaveError(
        err instanceof Error ? err.message : t("profile.errors.saveFailed")
      );
    } finally {
      setIsSavingKey(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">
              Prof<span className="text-blue-600">Assistant</span>
            </h1>
          </Link>
          <div className="flex items-center gap-4">
            <div className="w-40">
              <LanguageSelector variant="header" />
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 text-red-600 hover:text-red-700 font-medium text-sm"
            >
              {t("profile.logout")}
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 max-w-2xl mx-auto w-full px-4 py-10">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">
          {t("profile.title")}
        </h2>

        {/* User info card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{user?.email}</p>
              <p className="text-sm text-gray-500">
                {t("profile.memberSince", {
                  date: user?.created_at
                    ? new Date(user.created_at).toLocaleDateString()
                    : ""
                })}
              </p>
            </div>
          </div>
        </div>

        {/* API Key Setup Banner (shown on first login for non-admin users) */}
        {showSetupBanner && (
          <div className="bg-amber-50 border-2 border-amber-400 rounded-2xl p-6 mb-6 animate-pulse-once">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-bold text-amber-800">
                  {t("profile.setupBanner.title")}
                </h3>
                <p className="text-sm text-amber-700 mt-1">
                  {t("profile.setupBanner.description")}
                </p>
              </div>
            </div>
            <ol className="list-decimal list-inside space-y-2 text-sm text-amber-800 ml-9 mb-4">
              <li>{t("profile.setupBanner.steps.step1")}</li>
              <li>{t("profile.setupBanner.steps.step2")}</li>
              <li>{t("profile.setupBanner.steps.step3")}</li>
            </ol>
            <div className="ml-9">
              <button
                onClick={() => {
                  setShowSetupBanner(false);
                  if (isSetupMode) {
                    setSearchParams({}, { replace: true });
                  }
                }}
                className="text-sm text-amber-600 hover:text-amber-800 underline"
              >
                {t("profile.setupBanner.dismiss")}
              </button>
            </div>
          </div>
        )}

        {/* API Key card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <Key className="w-5 h-5 text-gray-700" />
            <h3 className="text-lg font-semibold text-gray-900">
              {t("profile.apiKey.title")}
            </h3>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            {t("profile.apiKey.description")}
          </p>

          {/* Current status */}
          {!isLoadingSettings && (
            <div className="flex items-center gap-2 mb-4">
              {settings?.has_api_key ? (
                <>
                  <ShieldCheck className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-green-700 font-medium">
                    {t("profile.apiKey.keyStored")}
                  </span>
                  <button
                    onClick={handleRemoveApiKey}
                    disabled={isSavingKey}
                    className="ml-auto text-sm text-red-500 hover:text-red-700 font-medium"
                  >
                    {t("profile.apiKey.remove")}
                  </button>
                </>
              ) : (
                <>
                  <ShieldX className="w-4 h-4 text-amber-500" />
                  <span className="text-sm text-amber-600 font-medium">
                    {t("profile.apiKey.noKey")}
                  </span>
                </>
              )}
            </div>
          )}

          {/* API key input */}
          <div className="flex gap-3">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={t("profile.apiKey.placeholder")}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-sm"
            />
            <button
              onClick={handleSaveApiKey}
              disabled={isSavingKey || !apiKey.trim()}
              className="px-5 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2"
            >
              {isSavingKey ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : keySaveSuccess ? (
                <Check className="w-4 h-4" />
              ) : null}
              {keySaveSuccess ? t("profile.saved") : t("profile.apiKey.save")}
            </button>
          </div>

          {keySaveError && (
            <p className="mt-2 text-sm text-red-600">{keySaveError}</p>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex gap-4 mt-8">
          <Link
            to="/"
            className="flex-1 flex items-center justify-center gap-2 px-5 py-3 bg-white border border-gray-200 rounded-xl shadow-sm hover:bg-gray-50 transition-colors text-gray-700 font-medium"
          >
            <Home className="w-5 h-5" />
            {t("profile.navigation.home")}
          </Link>
          <Link
            to="/app"
            className="flex-1 flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 rounded-xl shadow-sm hover:bg-blue-700 transition-colors text-white font-medium"
          >
            <Rocket className="w-5 h-5" />
            {t("profile.navigation.openApp")}
          </Link>
        </div>
      </div>
    </div>
  );
}
