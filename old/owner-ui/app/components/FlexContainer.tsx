import { Container, styled } from "@mui/material";

export const FlexContainer = styled(Container)({
  flexGrow: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}) as typeof Container;
