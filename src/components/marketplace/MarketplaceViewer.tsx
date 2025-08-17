import React, { useEffect, useState } from 'react';
import { ThemeManager, Theme } from '../../theme/ThemeManager';

interface MarketplaceViewerProps {
  manager: ThemeManager;
  onApply?: (theme: Theme) => void;
}

/**
 * MarketplaceViewer lists community themes and allows preview/apply.
 */
export const MarketplaceViewer: React.FC<MarketplaceViewerProps> = ({ manager, onApply }) => {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [preview, setPreview] = useState<Theme | null>(null);

  useEffect(() => {
    setThemes(manager.listMarketplaceThemes());
  }, [manager]);

  const handleHover = (t: Theme) => {
    setPreview(t);
    manager.applyTheme(t);
  };

  return (
    <div className="marketplace-viewer">
      {themes.map((t) => (
        <div
          key={t.name}
          className="marketplace-item"
          onMouseEnter={() => handleHover(t)}
          onClick={() => onApply?.(t)}
        >
          <strong>{t.name}</strong> <span>by {t.author}</span>
        </div>
      ))}
      {preview && (
        <div className="theme-preview">
          Previewing: {preview.name}
        </div>
      )}
    </div>
  );
};
