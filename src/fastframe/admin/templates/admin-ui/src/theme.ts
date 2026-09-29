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
    // react-admin's own `defaultTheme` (spread above) is actually its
    // *light* theme and hardcodes this to `grey[300]` regardless of mode
    // (see ra-ui-materialui's `defaultTheme.js`). Override explicitly so
    // the edit/create Save-Delete toolbar matches our surface color.
    RaToolbar: {
      styleOverrides: {
        root: { backgroundColor: "#FFFFFF" },
      },
    },
  },
});

Object.assign(theme, { sidebar: { width: 248, closedWidth: 64 } });

const darkInk = "#EEF1F6";
const darkPaper = "#0F1522";

export const darkTheme = createTheme({
  ...defaultTheme,
  palette: {
    ...defaultTheme.palette,
    mode: "dark",
    primary: { main: "#6E8CFF", contrastText: "#0F1522" },
    secondary: { main: "#3ECF95", contrastText: "#0F1522" },
    background: { default: darkPaper, paper: "#161D2E" },
    text: { primary: darkInk, secondary: "#93A0B3" },
    divider: "#28324A",
    error: { main: "#EF6A72" },
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
          backgroundColor: "#161D2E",
          color: darkInk,
          boxShadow: "none",
          borderBottom: "1px solid #28324A",
        },
        colorInherit: {
          backgroundColor: "#161D2E",
          color: darkInk,
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
          color: "#93A0B3",
          backgroundColor: "#161D2E",
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
        root: { borderRadius: 10, backgroundColor: "#161D2E" },
      },
    },
    // Same fix as `theme` above: `defaultTheme` is react-admin's *light*
    // theme, so its `RaToolbar` override (`grey[300]`) leaks into dark
    // mode unless we override it here too.
    RaToolbar: {
      styleOverrides: {
        root: { backgroundColor: "#161D2E" },
      },
    },
  },
});

Object.assign(darkTheme, { sidebar: { width: 248, closedWidth: 64 } });
