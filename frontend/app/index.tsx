import { useEffect } from 'react';
import { useRouter, useSegments } from 'expo-router';

export default function Index() {
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    // Use setTimeout to avoid navigation during render
    const timeout = setTimeout(() => {
      if (segments[0] !== '(tabs)') {
        router.replace('/(tabs)/dashboard');
      }
    }, 0);

    return () => clearTimeout(timeout);
  }, []);

  return null;
}
