import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Shield, UserCheck, UserPlus, Users, UserMinus } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import { promoteToDriver, demoteToRider, getUsers } from "@/api/client";
import { Button } from "@/components/ui/button";

const UserManagementPage = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [actionUserId, setActionUserId] = useState<number | null>(null);
  const [loadingUsers, setLoadingUsers] = useState(true);

  const fetchUsers = async () => {
    try {
      const res = await getUsers();
      setUsers(res.data.users);
    } catch (err) {
      console.error("Failed to fetch users", err);
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId: number, action: 'promote' | 'demote') => {
    setActionUserId(userId);
    try {
      if (action === 'promote') {
        await promoteToDriver(userId.toString());
      } else {
        await demoteToRider(userId.toString());
      }
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.message || `Failed to ${action} user`);
    } finally {
      setActionUserId(null);
    }
  };

  return (
    <div className="pb-8">
      <PageHeader
        breadcrumb="Administration"
        title="User Role Management"
        description="Monitor user accounts and manage platform permissions"
      />
      
      <div className="px-8 mt-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card rounded-xl p-6 card-shadow border border-border/60"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Registered Users</h3>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-full">
              <Users className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                {users.length} Total
              </span>
            </div>
          </div>
          
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-600 dark:text-slate-400 font-medium uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-6 py-4 border-b border-border">User Identity</th>
                  <th className="px-6 py-4 text-center border-b border-border">Role Status</th>
                  <th className="px-6 py-4 text-center border-b border-border">Driver Status</th>
                  <th className="px-6 py-4 text-right border-b border-border">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loadingUsers ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-slate-400 italic">
                      Retrieving platform users...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-10 text-center text-slate-400 italic">
                        No users found in the system.
                      </td>
                    </tr>
                ) : users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xs font-bold text-white uppercase shadow-sm">
                          {u.name.charAt(0)}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white leading-tight">{u.name}</div>
                          <div className="text-[11px] text-slate-500 dark:text-slate-400">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide ${
                        u.role === 'admin' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30' :
                        u.role === 'driver' ? 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30' :
                        'bg-slate-100 text-slate-600 dark:bg-slate-800'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {u.driver_profile ? (
                        <div className="flex items-center justify-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                          <UserCheck className="w-4 h-4" />
                          <span className="text-[11px] font-bold">Active Driver Profile</span>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-400 font-medium tracking-wide">Standard Rider</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {u.role === 'rider' ? (
                        <Button 
                          onClick={() => handleRoleChange(u.id, 'promote')} 
                          variant="cyan" 
                          size="sm"
                          className="h-8 gap-2 text-[11px] font-semibold"
                          disabled={actionUserId === u.id}
                        >
                          <UserPlus className="w-3.5 h-3.5" />
                          {actionUserId === u.id ? "Processing..." : "Promote"}
                        </Button>
                      ) : u.role === 'driver' ? (
                        <Button 
                          onClick={() => handleRoleChange(u.id, 'demote')} 
                          variant="outline" 
                          size="sm"
                          className="h-8 gap-2 text-[11px] font-semibold text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700 dark:text-red-400 dark:border-red-900/30 dark:hover:bg-red-900/20"
                          disabled={actionUserId === u.id}
                        >
                          <UserMinus className="w-3.5 h-3.5" />
                          {actionUserId === u.id ? "Processing..." : "Demote"}
                        </Button>
                      ) : (
                        <span className="text-[11px] text-slate-400 italic font-medium px-4">System Restricted</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default UserManagementPage;
