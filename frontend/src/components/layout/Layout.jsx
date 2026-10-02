import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { MobileNav } from "./MobileNav";

export function Layout({ currentRoute, onNavigate, title, children }) {
  return (
    <div className="app-container">
      <Sidebar currentRoute={currentRoute} onNavigate={onNavigate} />
      <div className="main-wrapper">
        <Navbar title={title} onNavigate={onNavigate} />
        <main className="page-content">{children}</main>
        <MobileNav currentRoute={currentRoute} onNavigate={onNavigate} />
      </div>
    </div>
  );
}
