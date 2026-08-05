import 'react';

declare module 'react' {
  /** Compatibilité pour les références optionnelles initialisées au premier chargement API. */
  function useRef<T = undefined>(): React.MutableRefObject<T | undefined>;
}
