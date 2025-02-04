import { createTheme } from "@mui/material";

export const walletTheme = createTheme({
  components: {
    MuiCssBaseline: {
      styleOverrides: `
            html {
                min-height: 100%;
            }
            html, body {
                display: flex;
                flex-direction: column;
            }
            body {
                flex: 1;
            }
            main {
                min-height: 100%;
            }
            `,
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 905,
      lg: 1240,
      xl: 1440,
    },
  },
});
