import { useCallback } from 'react';

export function useRequestHandlers(
  submitInFlightRef: React.MutableRefObject<boolean>,
  activeRequestControllerRef: React.MutableRefObject<AbortController | null>,
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setProcessingStatus: React.Dispatch<React.SetStateAction<string>>
) {
  const stopActiveRequest = useCallback(() => {
    submitInFlightRef.current = false;
    activeRequestControllerRef.current?.abort();
    activeRequestControllerRef.current = null;
    setIsLoading(false);
    setProcessingStatus('Request cancelled by user.');
    setTimeout(() => {
      setProcessingStatus('');
    }, 2000);
  }, [submitInFlightRef, activeRequestControllerRef, setIsLoading, setProcessingStatus]);

  return { stopActiveRequest };
}