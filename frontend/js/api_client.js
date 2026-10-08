function getApiBase() {
  if (typeof window !== "undefined") {
    if (window.__API_BASE__) return window.__API_BASE__.replace(/\/$/, "");
    const stored = localStorage.getItem("FOOTBALL_LIFE_API_BASE");
    if (stored) return stored.replace(/\/$/, "");
    if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      return (window.__API_BASE__ || "").replace(/\/$/, "");
    }
  }
  return "http://localhost:8000";
}

const API_BASE = getApiBase();

export const ApiClient = {
  async healthCheck() {
    try {
      const res = await fetch(`${API_BASE}/healthz`);
      return await res.json();
    } catch (e) {
      return null;
    }
  },

  async createNewWorld(name, country, position) {
    const res = await fetch(`${API_BASE}/api/world/new`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, country, position, seed: Math.floor(Math.random() * 100000) })
    });
    if (!res.ok) throw new Error("Failed to create world");
    return await res.json();
  },

  async getWorldState() {
    const res = await fetch(`${API_BASE}/api/world/state`);
    if (!res.ok) return null;
    return await res.json();
  },

  async getCurrentScreen() {
    const res = await fetch(`${API_BASE}/api/game/current-screen`);
    if (!res.ok) throw new Error("Failed to fetch screen");
    return await res.json();
  },

  async advanceNextStep() {
    const res = await fetch(`${API_BASE}/api/game/next-step`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to advance step");
    return await res.json();
  },

  async submitChoice(choiceType, selectedOfferId) {
    const res = await fetch(`${API_BASE}/api/game/choice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ choice_type: choiceType, selected_offer_id: selectedOfferId })
    });
    if (!res.ok) throw new Error("Failed to submit choice");
    return await res.json();
  },

  async getTimeline() {
    const res = await fetch(`${API_BASE}/api/game/timeline`);
    if (!res.ok) throw new Error("Failed to fetch timeline");
    return await res.json();
  },

  async getComparisons() {
    const res = await fetch(`${API_BASE}/api/game/comparisons`);
    if (!res.ok) throw new Error("Failed to fetch comparisons");
    return await res.json();
  },

  async getPlayerDetails(playerId) {
    const res = await fetch(`${API_BASE}/api/player/${playerId}`);
    if (!res.ok) throw new Error("Failed to fetch player details");
    return await res.json();
  },

  async getMyClub() {
    const res = await fetch(`${API_BASE}/api/game/my-club`);
    if (!res.ok) throw new Error("Failed to fetch club");
    return await res.json();
  },

  async getClubDetails(clubId) {
    const res = await fetch(`${API_BASE}/api/club/${clubId}`);
    if (!res.ok) throw new Error("Failed to fetch club details");
    return await res.json();
  },

  async getAllClubs() {
    const res = await fetch(`${API_BASE}/api/world/clubs`);
    if (!res.ok) throw new Error("Failed to fetch clubs directory");
    return await res.json();
  },

  async makeManualSave(saveName) {
    const res = await fetch(`${API_BASE}/api/saves/manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ save_name: saveName })
    });
    return await res.json();
  },

  async listSaves() {
    const res = await fetch(`${API_BASE}/api/saves`);
    return await res.json();
  },

  async loadSave(saveId) {
    const res = await fetch(`${API_BASE}/api/saves/${saveId}/load`, { method: "POST" });
    return await res.json();
  },

  async retirePlayer() {
    const res = await fetch(`${API_BASE}/api/game/action/retire`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to submit retirement");
    return await res.json();
  },

  async getRetirementSummary() {
    const res = await fetch(`${API_BASE}/api/game/retirement-summary`);
    if (!res.ok) throw new Error("Failed to fetch retirement summary");
    return await res.json();
  },

  async performLifestyleAction(actionType, itemId, subAction, customName, backstoryId) {
    const res = await fetch(`${API_BASE}/api/game/lifestyle-action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_type: actionType,
        item_id: itemId,
        sub_action: subAction,
        custom_name: customName,
        backstory_id: backstoryId
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to perform lifestyle action");
    }
    return await res.json();
  },

  async getNationalTeam() {
    const res = await fetch(`${API_BASE}/api/player/national-team`);
    if (!res.ok) throw new Error("Failed to fetch national team");
    return await res.json();
  },

  async getInternationalTournament() {
    const res = await fetch(`${API_BASE}/api/world/international/tournament`);
    if (!res.ok) throw new Error("Failed to fetch international tournament");
    return await res.json();
  }
};

