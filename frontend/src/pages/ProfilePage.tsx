import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";
import { fetchUserSettings, updateUserSettings } from "../services/authService";
import { LanguageSelector } from "../components";
import type { UserSettingsResponse } from "../types/auth";
import {
  ArrowLeft,
  User,
  Key,
  Cpu,
  Check,
  Loader2,
  ShieldCheck,
  ShieldX,
  AlertTriangle
} from "lucide-react";

const AVAILABLE_MODELS = [
  {
    value: "gpt-4o-mini",
    label: "GPT-4o Mini",
    description: "profile.models.gpt4oMiniDesc"
  },
  { value: "gpt-4o", label: "GPT-4o", description: "profile.models.gpt4oDesc" }
];

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const isSetupMode = searchParams.get("setup") === "true";

  const [settings, setSettings] = useState<UserSettingsResponse | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);
  const [showSetupBanner, setShowSetupBanner] = useState(false);

  // API key form
  const [apiKey, setApiKey] = useState("");
  const [isSavingKey, setIsSavingKey] = useState(false);
  const [keySaveSuccess, setKeySaveSuccess] = useState(false);
  const [keySaveError, setKeySaveError] = useState("");

  // Model form
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [isSavingModel, setIsSavingModel] = useState(false);
  const [modelSaveSuccess, setModelSaveSuccess] = useState(false);
  const [modelSaveError, setModelSaveError] = useState("");

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const s = await fetchUserSettings();
        setSettings(s);
        setSelectedModel(s.preferred_model);
        // Show setup banner for non-admin users without API key on first visit
        if (isSetupMode && !s.has_api_key && user?.role !== "admin") {
          setShowSetupBanner(true);
        }
      } catch {
        // Settings may not exist yet, that's ok
        if (isSetupMode && user?.role !== "admin") {
          setShowSetupBanner(true);
        }
      } finally {
        setIsLoadingSettings(false);
      }
    };
    loadSettings();
  }, [isSetupMode, user?.role]);

  const handleSaveApiKey = async () => {
    setKeySaveError("");
    setKeySaveSuccess(false);

    if (!apiKey.trim()) {
      setKeySaveError(t("profile.errors.emptyApiKey"));
      return;
    }

    setIsSavingKey(true);
    try {
      const updated = await updateUserSettings({ openai_api_key: apiKey });
      setSettings(updated);
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
      const updated = await updateUserSettings({ openai_api_key: "" });
      setSettings(updated);
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

  const handleSaveModel = async () => {
    setModelSaveError("");
    setModelSaveSuccess(false);
    setIsSavingModel(true);
    try {
      const updated = await updateUserSettings({
        preferred_model: selectedModel
      });
      setSettings(updated);
      setModelSaveSuccess(true);
      setTimeout(() => setModelSaveSuccess(false), 3000);
    } catch (err) {
      setModelSaveError(
        err instanceof Error ? err.message : t("profile.errors.saveFailed")
      );
    } finally {
      setIsSavingModel(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2">
            <ArrowLeft className="w-5 h-5 text-gray-500" />
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

        {/* Model selection card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Cpu className="w-5 h-5 text-gray-700" />
            <h3 className="text-lg font-semibold text-gray-900">
              {t("profile.model.title")}
            </h3>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            {t("profile.model.description")}
          </p>

          {isLoadingSettings ? (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">{t("common.processing")}</span>
            </div>
          ) : (
            <>
              <div className="space-y-3 mb-5">
                {AVAILABLE_MODELS.map((model) => (
                  <label
                    key={model.value}
                    className={`flex items-start gap-3 p-4 border rounded-xl cursor-pointer transition-colors ${
                      selectedModel === model.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="model"
                      value={model.value}
                      checked={selectedModel === model.value}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="mt-1 accent-blue-600"
                    />
                    <div>
                      <p className="font-medium text-gray-900">{model.label}</p>
                      <p className="text-sm text-gray-500">
                        {t(model.description)}
                      </p>
                    </div>
                  </label>
                ))}
              </div>

              <button
                onClick={handleSaveModel}
                disabled={
                  isSavingModel || selectedModel === settings?.preferred_model
                }
                className="px-5 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2"
              >
                {isSavingModel ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : modelSaveSuccess ? (
                  <Check className="w-4 h-4" />
                ) : null}
                {modelSaveSuccess
                  ? t("profile.saved")
                  : t("profile.model.save")}
              </button>

              {modelSaveError && (
                <p className="mt-2 text-sm text-red-600">{modelSaveError}</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
