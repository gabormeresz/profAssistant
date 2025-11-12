import { useState } from "react";
import { Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { enhancePrompt } from "../../services";
import { PROMPT_ENHANCEMENT } from "../../utils/constants";

interface PromptEnhancerProps {
  message: string;
  contextType: "course_outline" | "lesson_plan";
  additionalContext?: Record<string, unknown>;
  onMessageChange: (message: string) => void;
  onLoadingChange?: (isLoading: boolean) => void;
}

export default function PromptEnhancer({
  message,
  contextType,
  additionalContext,
  onMessageChange,
  onLoadingChange
}: PromptEnhancerProps) {
  const { t } = useTranslation();
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [error, setError] = useState("");

  const isDisabled =
    isEnhancing || message.trim().length < PROMPT_ENHANCEMENT.MIN_LENGTH;

  const handleEnhance = async () => {
    setIsEnhancing(true);
    onLoadingChange?.(true);
    setError("");

    try {
      const result = await enhancePrompt({
        message,
        contextType,
        additionalContext
      });

      if (result.error) {
        setError(result.error);
      } else if (result.enhanced_prompt) {
        onMessageChange(result.enhanced_prompt);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : PROMPT_ENHANCEMENT.ERROR_MESSAGES.GENERIC_ERROR
      );
    } finally {
      setIsEnhancing(false);
      onLoadingChange?.(false);
    }
  };

  return (
    <div className="mt-2 flex items-start gap-2">
      <button
        type="button"
        onClick={handleEnhance}
        disabled={isDisabled}
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Sparkles className="h-4 w-4" />
        {isEnhancing
          ? t("promptEnhancer.enhancing")
          : t("promptEnhancer.enhance")}
      </button>
      {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
    </div>
  );
}
