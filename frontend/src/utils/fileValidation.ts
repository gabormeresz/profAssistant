import { FILE_UPLOAD } from "./constants";

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validate a single file for upload
 */
export function validateFile(file: File): FileValidationResult {
  // Check file size
  if (file.size > FILE_UPLOAD.MAX_SIZE) {
    return {
      valid: false,
      error: FILE_UPLOAD.ERROR_MESSAGES.TOO_LARGE(
        file.name,
        FILE_UPLOAD.MAX_SIZE_MB
      )
    };
  }

  // Check file type
  const isValidType =
    (FILE_UPLOAD.ALLOWED_TYPES as readonly string[]).includes(file.type) ||
    FILE_UPLOAD.ALLOWED_EXTENSIONS.some((ext) => file.name.endsWith(ext));

  if (!isValidType) {
    return {
      valid: false,
      error: FILE_UPLOAD.ERROR_MESSAGES.UNSUPPORTED_TYPE(file.name)
    };
  }

  return { valid: true };
}

/**
 * Validate multiple files and return valid ones with any error message
 */
export function validateFiles(files: FileList | File[]): {
  validFiles: File[];
  error?: string;
} {
  const validFiles: File[] = [];
  let lastError: string | undefined;

  const fileArray = Array.from(files);

  for (const file of fileArray) {
    const result = validateFile(file);
    if (result.valid) {
      validFiles.push(file);
    } else {
      lastError = result.error;
    }
  }

  return { validFiles, error: lastError };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KB`;
}
