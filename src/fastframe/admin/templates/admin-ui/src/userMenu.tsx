import { useEffect, useState, type MouseEvent } from "react";
import {
  Divider,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Switch,
  Tooltip,
} from "@mui/material";
import DarkModeOutlinedIcon from "@mui/icons-material/DarkModeOutlined";
import LogoutOutlinedIcon from "@mui/icons-material/LogoutOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutlineOutlined";
import { useTheme } from "react-admin";
import { useNavigate } from "react-router-dom";

import { API_URL, type ModelSchema } from "./api";
import { useCurrentUser } from "./currentUser";
import { initials, isUserModel, toneFor } from "./users";

/** Finds the resource + record id for "My profile", if a User model exists. */
function profileTarget(models: ModelSchema[], userId: string | number | null) {
  if (userId === null) return undefined;
  const model = models.find(isUserModel);
  if (!model) return undefined;
  return `/${model.resource}/${userId}`;
}

export function makeUserMenu(models: ModelSchema[]) {
  return function UserMenu() {
    const user = useCurrentUser();
    const [theme, setTheme] = useTheme();
    // `useTheme()` resolves to the mode actually being rendered (explicit
    // choice, or the system preference default) — mirror it onto <html>
    // so plain CSS (index.css) can theme the hand-styled cards that
    // aren't MUI components (profile header, password panel, activity
    // panel, etc.) via `[data-theme="dark"]`.
    useEffect(() => {
      document.documentElement.dataset.theme = theme;
    }, [theme]);
    const navigate = useNavigate();
    const [anchor, setAnchor] = useState<HTMLElement | null>(null);

    const open = (event: MouseEvent<HTMLElement>) => setAnchor(event.currentTarget);
    const close = () => setAnchor(null);

    if (!user) return null;

    const name = user.username || user.email || "Account";
    const tone = toneFor(name);
    const profile = profileTarget(models, user.id);

    const logout = async () => {
      close();
      try {
        await fetch(`${API_URL}/logout`, { method: "POST" });
      } finally {
        window.location.reload();
      }
    };

    return (
      <>
        <Tooltip title={name}>
          <button type="button" className="user-menu-trigger" onClick={open}>
            <span className="avatar sm" style={{ background: tone }} aria-hidden="true">
              {initials(undefined, undefined, name)}
            </span>
          </button>
        </Tooltip>
        <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={close} onClick={close}>
          <div className="user-menu-header">
            <span className="avatar" style={{ background: tone }} aria-hidden="true">
              {initials(undefined, undefined, name)}
            </span>
            <div>
              <div className="user-menu-name">{name}</div>
              {user.email ? <div className="user-menu-email">{user.email}</div> : null}
            </div>
          </div>
          <Divider />
          {profile ? (
            <MenuItem onClick={() => navigate(profile)}>
              <ListItemIcon>
                <PersonOutlineIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>My profile</ListItemText>
            </MenuItem>
          ) : null}
          <MenuItem onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            <ListItemIcon>
              <DarkModeOutlinedIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Dark mode</ListItemText>
            <Switch edge="end" size="small" checked={theme === "dark"} onChange={() => {}} />
          </MenuItem>
          <Divider />
          <MenuItem onClick={logout}>
            <ListItemIcon>
              <LogoutOutlinedIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Log out</ListItemText>
          </MenuItem>
        </Menu>
      </>
    );
  };
}
