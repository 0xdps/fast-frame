import { defaultTheme } from "react-admin";
import { createTheme } from "@mui/material/styles";

const ink = "#172033";
const paper = "#F4F7FB";
const accent = "#3157E8";

export const theme = createTheme({
  ...defaultTheme,
  palette: {
    ...defaultTheme.palette,
    mode: "light",
    primary: { main: accent, contrastText: "#FFFFFF" },
    secondary: { main: "#0F9F6E", contrastText: "#FFFFFF" },
    background: { default: paper, paper: "#FFFFFF" },
    text: { primary: ink, secondary: "#5C6B7A" },
    divider: "#E3E8EE",
    error: { main: "#C2414A" },
  },
  shape: { borderRadius: 12 },
  typography: {
    ...defaultTheme.typography,
    fontFamily: '"Figtree", "Segoe UI", sans-serif',
    h4: { fontFamily: '"Outfit", sans-serif', fontWeight: 600, letterSpacing: "-0.03em" },
    h5: { fontFamily: '"Outfit", sans-serif', fontWeight: 600, letterSpacing: "-0.03em" },
    h6: { fontFamily: '"Outfit", sans-serif', fontWeight: 600, letterSpacing: "-0.02em" },
    button: { fontFamily: '"Outfit", sans-serif', fontWeight: 600, textTransform: "none" },
  },
  components: {
    ...defaultTheme.components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#FFFFFF",
          color: ink,
          boxShadow: "none",
          borderBottom: "1px solid #E3E8EE",
        },
        colorInherit: {
          backgroundColor: "#FFFFFF",
          color: ink,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 10, textTransform: "none", fontWeight: 600, boxShadow: "none" },
        contained: { boxShadow: "none" },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: "none" },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontFamily: '"Outfit", sans-serif',
          fontWeight: 600,
          fontSize: "0.8rem",
          color: "#5C6B7A",
          backgroundColor: "#F7F9FB",
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: "outlined", size: "small" },
    },
    MuiFormControl: {
      defaultProps: { variant: "outlined", size: "small" },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { borderRadius: 10, backgroundColor: "#FFFFFF" },
      },
    },
  },
});

Object.assign(theme, { sidebar: { width: 248, closedWidth: 64 } });
