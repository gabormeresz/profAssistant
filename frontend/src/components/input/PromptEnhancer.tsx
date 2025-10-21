import { useState } from "react";
import { Sparkles } from "lucide-react";
import { enhancePrompt } from "../../services";
import { PROMPT_ENHANCEMENT } from "../../utils/constants";

interface PromptEnhancerProps {
  message: string;
  topic: string;
  numberOfClasses: number;
  onMessageChange: (message: string) => void;
}

export default function PromptEnhancer({
  message,
  topic,
  numberOfClasses,
  onMessageChange
}: PromptEnhancerProps) {
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [error, setError] = useState("");

  const isDisabled =
    isEnhancing ||
    message.trim().length < PROMPT_ENHANCEMENT.MIN_LENGTH ||
    !topic.trim();

  const handleEnhance = async () => {
    setIsEnhancing(true);
    setError("");

    try {
      const result = await enhancePrompt({
        message,
        topic,
        numberOfClasses
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
        {isEnhancing ? "Enhancing..." : "Enhance Prompt"}
      </button>
      {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
    </div>
  );
}
