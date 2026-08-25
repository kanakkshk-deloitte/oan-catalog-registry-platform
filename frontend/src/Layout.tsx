interface NavItem {
  key: string;
  label: string;
}

interface LayoutProps {
  title: string;
  description: string;
  navItems: NavItem[];
  activeNav: string;
  onNavChange: (key: string) => void;
  children: React.ReactNode;
}

export function Layout({
  title,
  description,
  navItems,
  activeNav,
  onNavChange,
  children,
}: LayoutProps) {
  return (
    <section className="shell card">
      <aside className="sidenav">
        <h2>{title}</h2>
        <p className="side-note">{description}</p>
        <nav className="nav-list" aria-label="Navigation">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${activeNav === item.key ? 'active' : ''}`}
              onClick={() => onNavChange(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </section>
  );
}
