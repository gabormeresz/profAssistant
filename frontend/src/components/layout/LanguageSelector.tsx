import { useTranslation } from "react-i18next";
import { Globe, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import "flag-icons/css/flag-icons.min.css";

interface LanguageSelectorProps {
  variant?: "sidebar" | "header";
}

const LanguageSelector = ({ variant = "sidebar" }: LanguageSelectorProps) => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const languages = [
    { code: "en", label: "English", flag: "gb" },
    { code: "hu", label: "Magyar", flag: "hu" }
  ];

  const currentLanguage = languages.find((lang) => lang.code === i18n.language);

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem("language", lang);
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Sidebar styles
  if (variant === "sidebar") {
    return (
      <div className="mb-1">
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-[#cddaef] hover:text-white hover:bg-[#333f51] focus:outline-none focus:border-transparent cursor-pointer transition-colors"
          >
            <Globe className="w-5 h-5 opacity-70" />
            <div className="flex items-center justify-between flex-1">
              <div className="flex items-center gap-3">
                <span>{currentLanguage?.label}</span>
                <span
                  className={`fi fi-${currentLanguage?.flag} rounded-sm`}
                ></span>
              </div>
              <ChevronDown
                className={`w-4 h-4 transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </div>
          </button>

          {isOpen && (
            <div className="absolute z-10 w-full mt-1 bg-[#2a3342] border border-[#3d4a5c] rounded-md shadow-lg">
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageChange(lang.code)}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-[#333f51] hover:text-white first:rounded-t-md last:rounded-b-md transition-colors ${
                    i18n.language === lang.code
                      ? "bg-[#333f51] text-white font-medium"
                      : "text-[#cddaef]"
                  }`}
                >
                  <span className={`fi fi-${lang.flag} rounded-sm`}></span>
                  <span>{lang.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Header styles
  return (
    <div className="relative">
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none cursor-pointer transition-colors h-10"
        >
          <div className="flex items-center gap-2">
            <span
              className={`fi fi-${currentLanguage?.flag} rounded-sm`}
            ></span>
            <span className="whitespace-nowrap text-sm">
              {currentLanguage?.label}
            </span>
            <ChevronDown
              className={`w-4 h-4 transition-transform ${
                isOpen ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>

        {isOpen && (
          <div className="absolute z-10 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg min-w-[140px]">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-md last:rounded-b-md transition-colors ${
                  i18n.language === lang.code
                    ? "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white font-medium"
                    : "text-gray-700 dark:text-gray-300"
                }`}
              >
                <span className={`fi fi-${lang.flag} rounded-sm`}></span>
                <span>{lang.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LanguageSelector;
