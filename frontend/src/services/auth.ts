/**
 * Authentication service for administrator login
 */

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  fullName: string;
  role: string;
  permissions: string[];
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AdminUser | null;
  token: string | null;
  loginTime: number | null;
}

// Administrator database - In a real application, this would be stored securely on the server
const ADMIN_USERS: Array<AdminUser & { password: string }> = [
  {
    id: 'admin-001',
    username: 'admin',
    password: 'ShambaAI2024!',
    email: 'admin@shambaai.com',
    fullName: 'System Administrator',
    role: 'Super Admin',
    permissions: ['read', 'write', 'delete', 'manage_users']
  },
  {
    id: 'admin-002',
    username: 'agriculture_expert',
    password: 'FarmData2024!',
    email: 'expert@shambaai.com',
    fullName: 'Dr. Sarah Kimani',
    role: 'Agriculture Expert',
    permissions: ['read', 'write', 'manage_content']
  },
  {
    id: 'admin-003',
    username: 'data_manager',
    password: 'DataSecure2024!',
    email: 'data@shambaai.com',
    fullName: 'John Mwangi',
    role: 'Data Manager',
    permissions: ['read', 'write', 'manage_data']
  },
  {
    id: 'admin-004',
    username: 'content_moderator',
    password: 'ContentMod2024!',
    email: 'content@shambaai.com',
    fullName: 'Grace Wanjiku',
    role: 'Content Moderator',
    permissions: ['read', 'write']
  },
  {
    id: 'admin-005',
    username: 'technical_admin',
    password: 'TechAdmin2024!',
    email: 'tech@shambaai.com',
    fullName: 'Michael Otieno',
    role: 'Technical Administrator',
    permissions: ['read', 'write', 'delete', 'manage_system']
  }
];

class AuthService {
  private static instance: AuthService;
  private authState: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
    loginTime: null
  };

  private constructor() {
    this.loadAuthState();
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Attempt to authenticate user with credentials
   */
  public async login(credentials: LoginCredentials): Promise<{ success: boolean; message: string; user?: AdminUser }> {
    try {
      // Find user in database
      const user = ADMIN_USERS.find(u => 
        u.username.toLowerCase() === credentials.username.toLowerCase() &&
        u.password === credentials.password
      );

      if (!user) {
        return {
          success: false,
          message: 'Invalid username or password. Please check your credentials and try again.'
        };
      }

      // Generate a simple token (in production, this would be a JWT from the server)
      const token = this.generateToken(user.id);
      
      // Create user object without password
      const { password, ...userWithoutPassword } = user;
      
      // Update auth state
      this.authState = {
        isAuthenticated: true,
        user: userWithoutPassword,
        token,
        loginTime: Date.now()
      };

      // Save to localStorage
      this.saveAuthState();

      return {
        success: true,
        message: 'Login successful! Welcome to the admin panel.',
        user: userWithoutPassword
      };
    } catch (error) {
      return {
        success: false,
        message: 'An error occurred during login. Please try again.'
      };
    }
  }

  /**
   * Logout user and clear session
   */
  public logout(): void {
    this.authState = {
      isAuthenticated: false,
      user: null,
      token: null,
      loginTime: null
    };
    this.saveAuthState();
  }

  /**
   * Check if user is authenticated
   */
  public isAuthenticated(): boolean {
    return this.authState.isAuthenticated && this.isTokenValid();
  }

  /**
   * Get current user
   */
  public getCurrentUser(): AdminUser | null {
    return this.isAuthenticated() ? this.authState.user : null;
  }

  /**
   * Get authentication token
   */
  public getToken(): string | null {
    return this.isAuthenticated() ? this.authState.token : null;
  }

  /**
   * Check if user has specific permission
   */
  public hasPermission(permission: string): boolean {
    if (!this.isAuthenticated() || !this.authState.user) {
      return false;
    }
    return this.authState.user.permissions.includes(permission);
  }

  /**
   * Get user role
   */
  public getUserRole(): string | null {
    return this.isAuthenticated() ? this.authState.user?.role || null : null;
  }

  /**
   * Generate a simple token (in production, this would be handled by the server)
   */
  private generateToken(userId: string): string {
    const timestamp = Date.now();
    const randomString = Math.random().toString(36).substring(2);
    return btoa(`${userId}:${timestamp}:${randomString}`);
  }

  /**
   * Check if token is still valid (24 hours)
   */
  private isTokenValid(): boolean {
    if (!this.authState.token || !this.authState.loginTime) {
      return false;
    }

    const now = Date.now();
    const twentyFourHours = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
    
    return (now - this.authState.loginTime) < twentyFourHours;
  }

  /**
   * Save authentication state to localStorage
   */
  private saveAuthState(): void {
    try {
      localStorage.setItem('shambaai_admin_auth', JSON.stringify(this.authState));
    } catch (error) {
      console.error('Failed to save auth state:', error);
    }
  }

  /**
   * Load authentication state from localStorage
   */
  private loadAuthState(): void {
    try {
      const saved = localStorage.getItem('shambaai_admin_auth');
      if (saved) {
        this.authState = JSON.parse(saved);
        
        // Check if token is still valid
        if (!this.isTokenValid()) {
          this.logout();
        }
      }
    } catch (error) {
      console.error('Failed to load auth state:', error);
      this.logout();
    }
  }

  /**
   * Get login statistics
   */
  public getLoginStats(): { totalUsers: number; activeUsers: number } {
    return {
      totalUsers: ADMIN_USERS.length,
      activeUsers: this.isAuthenticated() ? 1 : 0
    };
  }

  /**
   * Get all admin users (for admin management - in production, this would be server-side)
   */
  public getAllAdminUsers(): Omit<AdminUser, 'id'>[] {
    return ADMIN_USERS.map(({ id, password, ...user }) => user);
  }
}

// Export singleton instance
export const authService = AuthService.getInstance();

// Export types and service
export default authService;

