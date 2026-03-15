import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { GitCompare, MapPin, Car, LogOut, Users, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";
import { useAuthStore } from "@/store";

const navItems = [
  { to: "/comparison", label: "Algorithm Comparison", icon: GitCompare, roles: ['admin', 'rider', 'driver'] },
  { to: "/rider", label: "Rider Simulation", icon: MapPin, roles: ['admin', 'rider'] },
  { to: "/driver", label: "Driver Simulation", icon: Car, roles: ['admin', 'driver'] },
];

const AppSidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const visibleNavItems = navItems.filter((item) => {
    if (!user?.role) return true;
    return item.roles.includes(user.role);
  });

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border/50">
      <div className="flex items-center gap-3 px-5 py-6 border-b border-sidebar-border/50">
        <div className="w-10 h-10 flex-shrink-0 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
          <GitCompare className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70 tracking-tight leading-tight">
          RideShare <span className="text-cyan-400">Optimizer</span>
        </span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {/* Main Navigation */}
        {navItems.filter(item => item.to !== "/admin").map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors group ${isActive ? "bg-sidebar-accent/50" : "hover:bg-sidebar-accent/30"}`}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-cyan-500 rounded-r-full shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <item.icon className={`w-5 h-5 transition-colors ${isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200"}`} />
              <span className={`transition-colors ${isActive ? "text-white font-semibold" : "text-slate-400 group-hover:text-slate-200"}`}>
                {item.label}
              </span>
            </NavLink>
          );
        })}

        {/* Administration Section */}
        {user?.role === 'admin' && (
          <div className="pt-6 mt-4 border-t border-sidebar-border/30">
            <div className="px-3 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Administration</span>
            </div>
            <NavLink
              to="/admin"
              className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors group ${location.pathname === "/admin" ? "bg-sidebar-accent/50" : "hover:bg-sidebar-accent/30"}`}
            >
              {location.pathname === "/admin" && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-cyan-500 rounded-r-full shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <BarChart3 className={`w-5 h-5 transition-colors ${location.pathname === "/admin" ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200"}`} />
              <span className={`transition-colors ${location.pathname === "/admin" ? "text-white font-semibold" : "text-slate-400 group-hover:text-slate-200"}`}>
                Platform Analytics
              </span>
            </NavLink>

            <NavLink
              to="/admin/users"
              className={`relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors group ${location.pathname === "/admin/users" ? "bg-sidebar-accent/50" : "hover:bg-sidebar-accent/30"}`}
            >
              {location.pathname === "/admin/users" && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-cyan-500 rounded-r-full shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <Users className={`w-5 h-5 transition-colors ${location.pathname === "/admin/users" ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200"}`} />
              <span className={`transition-colors ${location.pathname === "/admin/users" ? "text-white font-semibold" : "text-slate-400 group-hover:text-slate-200"}`}>
                User Role Management
              </span>
            </NavLink>
          </div>
        )}
      </nav>
      <div className="px-5 py-4 border-t border-sidebar-border relative">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-sidebar-accent flex items-center justify-center text-sm font-semibold text-sidebar-accent-foreground flex-shrink-0">
            {user?.name?.charAt(0)?.toUpperCase() || "?"}
          </div>
          <div className="overflow-hidden">
            <div className="text-sm font-medium text-sidebar-accent-foreground truncate">{user?.name || "Guest"}</div>
            <div className="text-xs text-sidebar-foreground capitalize truncate">{user?.role || "unknown"}</div>
          </div>
        </div>
        
        <button 
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default AppSidebar;
