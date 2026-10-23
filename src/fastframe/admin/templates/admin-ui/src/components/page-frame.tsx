import { useEffect, useState, type ReactNode } from "react";
import { useOutletContext } from "react-router-dom";

import { PageHeader } from "./page-header";

export interface ShellOutlet {
  openMenu: () => void;
  openPalette: () => void;
}

export function PageFrame({
  title,
  meta,
  actions,
  breadcrumb,
  messages,
  children,
}: {
  title: string;
  meta?: ReactNode;
  actions?: ReactNode;
  breadcrumb?: ReactNode;
  messages?: ReactNode;
  children: ReactNode;
}) {
  const { openMenu, openPalette } = useOutletContext<ShellOutlet>();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    setScrolled(false);
  }, [title]);

  return (
    <div className="group/page flex min-h-0 flex-1 flex-col" data-scrolled={scrolled ? "true" : "false"}>
      <PageHeader
        title={title}
        meta={meta}
        actions={actions}
        breadcrumb={breadcrumb}
        messages={messages}
        onOpenMenu={openMenu}
        onOpenPalette={openPalette}
      />
      <div
        className="relative flex min-h-0 flex-1 flex-col overflow-auto"
        onScroll={(event) => setScrolled(event.currentTarget.scrollTop > 0)}
      >
        {children}
      </div>
    </div>
  );
}
