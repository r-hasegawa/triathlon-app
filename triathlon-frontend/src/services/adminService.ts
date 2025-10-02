import { authService } from './authService';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Competition {
  name: string;
  date: string | null;
  location: string | null;
  description: string | null;
}

class AdminService {
  private async getHeaders() {
    const token = authService.getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async getCompetitions(includeInactive: boolean = false) {
    const headers = await this.getHeaders();
    const url = `${API_BASE}/admin/competitions?include_inactive=${includeInactive}`;
    
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch competitions: ${response.status}`);
    }
    
    return response.json();
  }

  async createCompetition(competition: Competition) {
    const headers = await this.getHeaders();
    
    const response = await fetch(`${API_BASE}/admin/competitions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(competition)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create competition: ${response.status}`);
    }
    
    return response.json();
  }

  async deleteCompetition(competitionId: string) {
    const headers = await this.getHeaders();
    
    const response = await fetch(`${API_BASE}/admin/competitions/${competitionId}`, {
      method: 'DELETE',
      headers
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete competition: ${response.status}`);
    }
    
    return response.json();
  }

  async getUsers() {
    const headers = await this.getHeaders();
    
    const response = await fetch(`${API_BASE}/admin/users`, { headers });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch users: ${response.status}`);
    }
    
    return response.json();
  }
}

export const adminService = new AdminService();