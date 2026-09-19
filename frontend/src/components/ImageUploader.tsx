import React, { useRef } from 'react';
import { GradingStatus } from '../types';

interface ImageUploaderProps {
  status: GradingStatus;
  onUpload: (file: File | Blob, filename: string, problemId?: string) => void;
  onSelectProblemById: (problemId: string) => void;
  onError?: (error: any) => void;
}

const MAX_SIZE_BYTES = 5 * 1024 * 1024;
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp', 'image/jpg']);

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  status,
  onUpload,
  onSelectProblemById,
  onError,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  const isTranscribing = status === 'transcribing';

  const validateAndUpload = (file: File) => {
    if (!ALLOWED_TYPES.has(file.type.toLowerCase())) {
      onError?.({
        code: 'UNSUPPORTED_FILE',
        message: `Unsupported file type: ${file.type || 'unknown'}.`,
        action: 'Please upload a JPEG, PNG, or WebP image.',
      });
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      onError?.({
        code: 'TOO_LARGE',
        message: `File size (${Math.round(file.size / 1024)} KB) exceeds 5 MB limit.`,
        action: 'Please compress or select a smaller photo.',
      });
      return;
    }

    onUpload(file, file.name);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = async (sampleKey: string, problemId: string, ext: 'jpg' | 'webp' | 'png' = 'jpg') => {
    onSelectProblemById(problemId);
    // Fetch local sample image from samples/images/
    try {
      const res = await fetch(`/samples/images/${sampleKey}.${ext}`);
      if (res.ok) {
        const blob = await res.blob();
        onUpload(blob, `${sampleKey}.${ext}`, problemId);
        return;
      }
    } catch {
      // Fallback below
    }

    // Fallback synthetic blob if fetch fails
    const canvas = document.createElement('canvas');
    canvas.width = 100;
    canvas.height = 100;
    canvas.toBlob((blob) => {
      if (blob) onUpload(blob, `${sampleKey}.${ext}`, problemId);
    }, ext === 'webp' ? 'image/webp' : 'image/jpeg');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <div
        className="uploader-box"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload handwritten solution photo"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            fileInputRef.current?.click();
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        <div style={{ color: 'var(--ink-muted)' }}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
        </div>

        <div>
          <p style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--ink-primary)' }}>
            {isTranscribing ? 'Transcribing handwriting into steps...' : 'Drop photo of solution here, or browse'}
          </p>
          <p style={{ fontSize: '0.8125rem', color: 'var(--ink-muted)', marginTop: 'var(--space-1)' }}>
            Supports JPG, PNG, WebP (auto-scaled to 1600px)
          </p>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-2)' }} onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            className="primary-btn"
            disabled={isTranscribing}
            onClick={() => fileInputRef.current?.click()}
            style={{ fontSize: '0.8125rem' }}
          >
            Choose File
          </button>
          <button
            type="button"
            disabled={isTranscribing}
            onClick={() => cameraInputRef.current?.click()}
            style={{ fontSize: '0.8125rem' }}
          >
            &#128247; Take Photo
          </button>
        </div>
      </div>

      <div className="sample-row">
        <span style={{ fontSize: '0.8125rem', color: 'var(--ink-muted)', fontWeight: 500 }}>
          Try a sample:
        </span>
        <button
          type="button"
          className="sample-chip"
          onClick={() => handleLoadSample('ohm_correct', 'phy-ohm-01', 'jpg')}
          title="Load Ohm's Law full marks demo (JPG)"
        >
          Ohm's Law (JPG)
        </button>
        <button
          type="button"
          className="sample-chip"
          onClick={() => handleLoadSample('ohm_wrong_sub', 'phy-ohm-01', 'webp')}
          title="Load Ohm's Law substitution error demo (WebP)"
        >
          Ohm's Law Error (WebP)
        </button>
        <button
          type="button"
          className="sample-chip"
          onClick={() => handleLoadSample('optics_wrong_sign', 'phy-trap-07', 'jpg')}
          title="Load Pressure unit trap demo (JPG)"
        >
          Pressure Trap (JPG)
        </button>
        <button
          type="button"
          className="sample-chip"
          onClick={() => handleLoadSample('quad_slip', 'math-quad-01', 'webp')}
          title="Load Quadratic roots demo (WebP)"
        >
          Quadratic Roots (WebP)
        </button>
      </div>
    </div>
  );
};
