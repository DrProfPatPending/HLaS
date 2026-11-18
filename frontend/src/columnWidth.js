// Column widths from Field Order (`widths` and `minimum_widths`) as CSS values.
// Club Settings stores whatever is typed, so a bare number such as "90" means 90px;
// passing it straight to CSS would be invalid and the browser would ignore it.

const CSS_LENGTH = /^\d+(?:\.\d+)?(?:px|%|em|rem|ch|vw)$/;

function toCssLength(raw) {
  if (typeof raw === 'number') {
    return Number.isFinite(raw) && raw > 0 ? `${raw}px` : '';
  }
  if (typeof raw !== 'string') return '';
  const value = raw.trim().toLowerCase();
  if (!value) return '';
  if (CSS_LENGTH.test(value)) return value;
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? `${numeric}px` : '';
}

// "flex", "auto", blank or anything unrecognised gives '' (let the table size the column).
export function columnWidthValue(raw) {
  return toCssLength(raw);
}

export function columnMinWidthValue(raw) {
  return toCssLength(raw);
}

// A configured width wins; otherwise the minimum width, if any.
export function columnWidthStyle(width, minWidth) {
  const widthValue = columnWidthValue(width);
  if (widthValue) return { width: widthValue };
  const minWidthValue = columnMinWidthValue(minWidth);
  return minWidthValue ? { minWidth: minWidthValue } : {};
}
