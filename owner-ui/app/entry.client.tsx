import * as React from "react";
import * as ReactDOM from "react-dom/client";
import { RemixBrowser } from "@remix-run/react";
import { CacheProvider } from "@emotion/react";
import ClientStyleContext from "./src/ClientStyleContext";
import createEmotionCache from "./src/createEmotionCache";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { walletTheme } from "~/styles/theme";

interface ClientCacheProviderProps {
  children: React.ReactNode;
}
function ClientCacheProvider({ children }: Readonly<ClientCacheProviderProps>) {
  const [cache, setCache] = React.useState(createEmotionCache());

  const clientStyleContextValue = React.useMemo(
    () => ({
      reset() {
        setCache(createEmotionCache());
      },
    }),
    [],
  );

  return (
    <ClientStyleContext.Provider value={clientStyleContextValue}>
      <CacheProvider value={cache}>{children}</CacheProvider>
    </ClientStyleContext.Provider>
  );
}

const hydrate = () => {
  React.startTransition(() => {
    ReactDOM.hydrateRoot(
      document,
      <React.StrictMode>
        <ClientCacheProvider>
          <ThemeProvider theme={walletTheme}>
            <CssBaseline />
            <RemixBrowser />
          </ThemeProvider>
        </ClientCacheProvider>
      </React.StrictMode>,
    );
  });
};

if (window.requestIdleCallback) {
  window.requestIdleCallback(hydrate);
} else {
  // Safari doesn't support requestIdleCallback
  // https://caniuse.com/requestidlecallback
  setTimeout(hydrate, 1);
}
