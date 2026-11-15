import DOMPurify from 'dompurify';

const ALLOWED_TAGS = [
  'a', 'b', 'blockquote', 'br', 'em', 'h2', 'h3', 'h4', 'hr',
  'i', 'li', 'ol', 'p', 'strong', 'u', 'ul',
];

const ALLOWED_ATTR = ['href', 'title'];

export function sanitizeMiniSiteContent(content) {
  if (typeof content !== 'string') return '';

  return DOMPurify.sanitize(content, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    ALLOW_ARIA_ATTR: false,
  });
}
