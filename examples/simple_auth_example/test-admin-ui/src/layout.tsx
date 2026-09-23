import { AppBar, Layout, Menu, type LayoutProps } from "react-admin";

const FrameAppBar = () => <AppBar color="inherit" elevation={0} userMenu={false} />;

const FrameMenu = () => (
  <div className="frame-menu">
    <div className="frame-brand">
      <span className="frame-mark" aria-hidden="true">
        Ff
      </span>
      <div>
        <div className="frame-name">FastFrame</div>
        <div className="frame-sub">Blog admin</div>
      </div>
    </div>
    <Menu />
  </div>
);

export const FrameLayout = (props: LayoutProps) => (
  <Layout {...props} appBar={FrameAppBar} menu={FrameMenu} />
);
