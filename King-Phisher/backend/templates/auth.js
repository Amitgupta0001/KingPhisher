class KingPhisherAuth {
    static async login(credentials) {
      try {
        const response = await KingPhisherAPI.post('/auth/login', credentials);
        await this._storeAuthData(response);
        
        // Notify all components about auth change
        chrome.runtime.sendMessage({ action: 'authStateChanged', loggedIn: true });
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  
    static async register(userData) {
      try {
        const response = await KingPhisherAPI.post('/auth/register', userData);
        await this._storeAuthData(response);
        
        // Notify all components about auth change
        chrome.runtime.sendMessage({ action: 'authStateChanged', loggedIn: true });
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  
    static async _storeAuthData(data) {
      await chrome.storage.local.set({
        kpAuthToken: data.token,
        kpUser: data.user,
        isAuthenticated: true
      });
    }
  
    static async isAuthenticated() {
      const { kpAuthToken } = await chrome.storage.local.get('kpAuthToken');
      return !!kpAuthToken;
    }
  
    static async logout() {
      await chrome.storage.local.remove(['kpAuthToken', 'kpUser', 'isAuthenticated']);
      // Notify all components about auth change
      chrome.runtime.sendMessage({ action: 'authStateChanged', loggedIn: false });
    }
  }