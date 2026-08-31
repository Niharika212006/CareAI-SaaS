/**
 * Formatting helpers for dates, currency, and clinical severity.
 */

export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date);
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateTimeString) {
  if (!dateTimeString) return 'N/A';
  try {
    const date = new Date(dateTimeString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch {
    return dateTimeString;
  }
}

export function formatCurrency(amount) {
  const num = Number(amount) || 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(num);
}

export function formatAllergiesDisplay(allergies) {
  if (!allergies) return 'None recorded';
  if (Array.isArray(allergies)) {
    if (allergies.length === 0) return 'None recorded';
    return allergies
      .map((item) => (typeof item === 'object' && item !== null ? item.name : String(item)))
      .filter(Boolean)
      .join(', ');
  }
  if (typeof allergies === 'string') return allergies;
  return 'None recorded';
}

export function formatConditionsDisplay(conditions) {
  if (!conditions) return 'None recorded';
  if (Array.isArray(conditions)) {
    if (conditions.length === 0) return 'None recorded';
    return conditions
      .map((item) => (typeof item === 'object' && item !== null ? item.name || item.condition : String(item)))
      .filter(Boolean)
      .join(', ');
  }
  if (typeof conditions === 'string') return conditions;
  return 'None recorded';
}
