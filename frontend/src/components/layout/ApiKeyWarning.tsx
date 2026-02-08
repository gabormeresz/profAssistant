import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AlertTriangle } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

export default function ApiKeyWarning() {
  const { t } = useTranslation();
  const { settings, isLoadingSettings } = useAuth();

  if (isLoadingSettings || settings?.has_api_key) return null;

  return (
    <Link
      to="/profile"
      className="flex items-center gap-2 px-4 py-2 rounded-lg text-amber-400 hover:bg-[#333f51] transition-colors text-sm"
    >
      <AlertTriangle className="w-4 h-4 shrink-0" />
      <span>{t("sidebar.apiKeyMissing")}</span>
    </Link>
  );
}
