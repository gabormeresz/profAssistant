import { useState } from "react";
import { Upload, File as FileIcon, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { validateFiles, formatFileSize } from "../../utils";
import { FILE_UPLOAD } from "../../utils/constants";

interface FileUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
  compact?: boolean;
}

export default function FileUpload({
  files,
  onFilesChange,
  disabled = false,
  compact = false
}: FileUploadProps) {
  const { t } = useTranslation();
  const [error, setError] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList) return;

    const { validFiles, error: validationError } = validateFiles(fileList);

    if (validationError) {
      setError(validationError);
    } else {
      setError("");
    }

    if (validFiles.length > 0) {
      onFilesChange([...files, ...validFiles]);
    }

    // Reset input
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  if (compact) {
    // Compact version for follow-up input
    return (
      <div>
        {/* Uploaded files list */}
        {files.length > 0 && (
          <div className="space-y-2 mb-3">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <FileIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                  <span className="text-sm text-gray-700 truncate">
                    {file.name}
                  </span>
                  <span className="text-xs text-gray-500 flex-shrink-0">
                    ({formatFileSize(file.size)})
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-2 p-1 hover:bg-gray-200 rounded transition-colors flex-shrink-0"
                  type="button"
                  disabled={disabled}
                >
                  <X className="h-4 w-4 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Error message */}
        {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

        {/* Upload button (compact) */}
        <label className="cursor-pointer flex-shrink-0">
          <div className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <Upload className="h-5 w-5 text-gray-500" />
          </div>
          <input
            type="file"
            multiple
            onChange={handleFileChange}
            className="hidden"
            accept={FILE_UPLOAD.ALLOWED_EXTENSIONS.join(",")}
            disabled={disabled}
          />
        </label>
      </div>
    );
  }

  // Full version for initial input
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {t("fileUpload.label")}
      </label>

      {/* Upload area */}
      <label className="flex-1 cursor-pointer">
        <div className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 transition-colors text-center">
          <Upload className="mx-auto h-8 w-8 text-gray-400" />
          <p className="mt-1 text-sm text-gray-500">
            {t("fileUpload.clickToUpload")}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {t("fileUpload.formats", { maxSize: FILE_UPLOAD.MAX_SIZE_MB })}
          </p>
        </div>
        <input
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
          accept={FILE_UPLOAD.ALLOWED_EXTENSIONS.join(",")}
          disabled={disabled}
        />
      </label>

      {/* Error message */}
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}

      {/* Uploaded files list */}
      {files.length > 0 && (
        <div className="mt-3 space-y-2">
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <FileIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                <span className="text-sm text-gray-700 truncate">
                  {file.name}
                </span>
                <span className="text-xs text-gray-500 flex-shrink-0">
                  ({formatFileSize(file.size)})
                </span>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="ml-2 p-1 hover:bg-gray-200 rounded transition-colors flex-shrink-0"
                type="button"
                disabled={disabled}
              >
                <X className="h-4 w-4 text-gray-500" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
