const FLAG_TRUE = new Set(['true', '1', 'yes', 'on']);
const FLAG_FALSE = new Set(['false', '0', 'no', 'off']);

function readEnv(keys: string[]): string | undefined {
  for (const key of keys) {
    const value = process.env[key];
    if (typeof value !== 'undefined') {
      return value;
    }
  }
  return undefined;
}

function toBooleanFlag(value: string | undefined, defaultValue: boolean): boolean {
  if (typeof value !== 'string') {
    return defaultValue;
  }

  const normalized = value.trim().toLowerCase();
  if (FLAG_TRUE.has(normalized)) {
    return true;
  }
  if (FLAG_FALSE.has(normalized)) {
    return false;
  }
  return defaultValue;
}

export function isProductionEnvironment(): boolean {
  return process.env.NODE_ENV === 'production';
}



export function isSimpleAuthEnabled(): boolean {
  const explicit = readEnv([
    'NEXT_PUBLIC_ENABLE_SIMPLE_AUTH',
    'ENABLE_SIMPLE_AUTH',
    'KAREN_ENABLE_SIMPLE_AUTH',
  ]);

  return toBooleanFlag(explicit, !isProductionEnvironment());
}
