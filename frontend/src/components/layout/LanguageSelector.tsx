import { useTranslation } from "react-i18next";
import { Globe } from "lucide-react";

const LanguageSelector = () => {
  const { i18n, t } = useTranslation();

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem("language", lang);
  };

  return (
    <div className="mb-6 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center gap-2 mb-2">
        <Globe className="w-4 h-4 text-gray-600" />
        <span className="text-xs font-semibold text-gray-700">
          {t("languageSelector.selectLanguage")}
        </span>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => handleLanguageChange("en")}
          className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
            i18n.language === "en"
              ? "bg-blue-600 text-white font-medium"
              : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
          }`}
        >
          {t("languageSelector.english")}
        </button>
        <button
          onClick={() => handleLanguageChange("hu")}
          className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
            i18n.language === "hu"
              ? "bg-blue-600 text-white font-medium"
              : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
          }`}
        >
          {t("languageSelector.hungarian")}
        </button>
      </div>
    </div>
  );
};

export default LanguageSelector;
