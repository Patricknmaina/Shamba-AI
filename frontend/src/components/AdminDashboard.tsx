import React from 'react';
import { Button } from './ui';
import { cn } from '../lib/utils';
import { 
  User, 
  LogOut, 
  Shield, 
  Clock, 
  Key, 
  Settings, 
  Users, 
  Database,
  Activity,
  Lock
} from 'lucide-react';
import type { AdminUser } from '../services/auth';

interface AdminDashboardProps {
  user: AdminUser;
  onLogout: () => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ user, onLogout }) => {
  const formatLoginTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'super admin':
        return 'from-red-500 to-red-600';
      case 'agriculture expert':
        return 'from-green-500 to-green-600';
      case 'data manager':
        return 'from-blue-500 to-blue-600';
      case 'content moderator':
        return 'from-purple-500 to-purple-600';
      case 'technical administrator':
        return 'from-orange-500 to-orange-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case 'super admin':
        return <Shield className="w-5 h-5" />;
      case 'agriculture expert':
        return <Users className="w-5 h-5" />;
      case 'data manager':
        return <Database className="w-5 h-5" />;
      case 'content moderator':
        return <Activity className="w-5 h-5" />;
      case 'technical administrator':
        return <Settings className="w-5 h-5" />;
      default:
        return <User className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-600 shadow-lg">
        {/* Decorative Elements */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-blue-100 to-transparent dark:from-blue-900/20 dark:to-transparent rounded-full -translate-y-16 translate-x-16 opacity-60"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-slate-100 to-transparent dark:from-slate-700/30 dark:to-transparent rounded-full translate-y-12 -translate-x-12 opacity-40"></div>
        
        <div className="relative z-10 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={cn(
                'w-16 h-16 bg-gradient-to-br rounded-full flex items-center justify-center shadow-lg',
                getRoleColor(user.role)
              )}>
                {getRoleIcon(user.role)}
                <span className="sr-only">{user.role}</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  Welcome back, {user.fullName}
                </h2>
                <p className="text-blue-600 dark:text-blue-400 font-medium">
                  {user.role} • {user.email}
                </p>
              </div>
            </div>
            
            <Button
              onClick={onLogout}
              variant="outline"
              className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-red-200 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-300 dark:hover:border-red-600 transition-all duration-200"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Admin Information Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* User Profile Card */}
        <div className="relative overflow-hidden bg-gradient-to-br from-green-50 via-white to-emerald-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-green-200 dark:border-green-800 shadow-lg">
          {/* Decorative Elements */}
          <div className="absolute top-0 left-0 w-24 h-24 bg-gradient-to-br from-green-100 to-transparent dark:from-green-900/20 dark:to-transparent rounded-full -translate-y-12 -translate-x-12 opacity-50"></div>
          
          <div className="relative z-10 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                User Profile
              </h3>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                <span className="text-slate-600 dark:text-slate-400 font-medium">Username:</span>
                <span className="font-semibold text-slate-900 dark:text-slate-100">{user.username}</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                <span className="text-slate-600 dark:text-slate-400 font-medium">Full Name:</span>
                <span className="font-semibold text-slate-900 dark:text-slate-100">{user.fullName}</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-green-200 dark:border-green-700">
                <span className="text-slate-600 dark:text-slate-400 font-medium">User ID:</span>
                <span className="font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">{user.id}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Role & Permissions Card */}
        <div className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-white to-pink-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-purple-200 dark:border-purple-800 shadow-lg">
          {/* Decorative Elements */}
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-purple-100 to-transparent dark:from-purple-900/20 dark:to-transparent rounded-full -translate-y-12 translate-x-12 opacity-50"></div>
          
          <div className="relative z-10 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Role & Permissions
              </h3>
            </div>
            
            <div className="space-y-3">
              <div className="p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-purple-200 dark:border-purple-700">
                <div className="flex items-center space-x-2 mb-2">
                  <div className={cn(
                    'w-6 h-6 bg-gradient-to-br rounded-full flex items-center justify-center',
                    getRoleColor(user.role)
                  )}>
                    {getRoleIcon(user.role)}
                  </div>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">{user.role}</span>
                </div>
              </div>
              
              <div className="p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-purple-200 dark:border-purple-700">
                <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">Permissions:</p>
                <div className="flex flex-wrap gap-1">
                  {user.permissions.map((permission, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-full font-medium"
                    >
                      {permission}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Session Information Card */}
        <div className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-blue-200 dark:border-blue-800 shadow-lg">
          {/* Decorative Elements */}
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-blue-100 to-transparent dark:from-blue-900/20 dark:to-transparent rounded-full translate-y-16 -translate-x-16 opacity-40"></div>
          
          <div className="relative z-10 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                <Clock className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Session Info
              </h3>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-blue-200 dark:border-blue-700">
                <span className="text-slate-600 dark:text-slate-400 font-medium">Status:</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-green-600 dark:text-green-400 font-semibold text-sm">Active</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-blue-200 dark:border-blue-700">
                <span className="text-slate-600 dark:text-slate-400 font-medium">Login Time:</span>
                <span className="font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {formatLoginTime(Date.now())}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-lg border border-blue-200 dark:border-blue-700">
                <span className="text-slate-600 dark:text-slate-400 font-medium">Security:</span>
                <div className="flex items-center space-x-1">
                  <Lock className="w-3 h-3 text-green-500" />
                  <span className="text-green-600 dark:text-green-400 font-semibold text-sm">Secured</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Security Notice */}
      <div className="relative overflow-hidden bg-gradient-to-br from-orange-50 via-white to-red-50 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl border-2 border-orange-200 dark:border-orange-800 shadow-lg">
        {/* Decorative Elements */}
        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-orange-100 to-transparent dark:from-orange-900/20 dark:to-transparent rounded-full -translate-y-12 translate-x-12 opacity-50"></div>
        
        <div className="relative z-10 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-full flex items-center justify-center">
              <Key className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Security Notice
            </h3>
          </div>
          
          <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl p-4 border border-orange-200 dark:border-orange-700">
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              <strong>Important:</strong> You are accessing the ShambaAI administrative panel. 
              All activities are logged and monitored. Please ensure you log out when finished 
              and never share your credentials with unauthorized personnel.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

