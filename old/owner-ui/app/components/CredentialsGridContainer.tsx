import { ReactNode } from "react";
import { Box, SxProps } from "@mui/material";

/**
 * Padding, margin and width properties that match Material Design's responsive grid guidelines
 */
const responsiveSx: SxProps = {
  px: { xs: 2, sm: 4, md: 0, lg: 25 },
  mx: { xs: 0, md: "auto", lg: 0 },
  width: { xs: "100%", md: 840, lg: "100%" },
};

export function CredentialsGridContainer({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <Box component="section" sx={{ ...responsiveSx, mt: { xs: 1, md: 1.5 } }}>
      {children}
    </Box>
  );
}
