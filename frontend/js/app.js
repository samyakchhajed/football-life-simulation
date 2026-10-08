import { ApiClient } from "./api_client.js";

// Application State
let appState = {
  worldState: null,
  currentScreenData: null,
  activeLeagueTab: null
};

// DOM Elements
const contentEl = document.getElementById("main-content");
const seasonNumEl = document.getElementById("header-season-num");
const userChipEl = document.getElementById("header-user-chip");
const nextBtn = document.getElementById("next-step-btn");
const myClubBtn = document.getElementById("my-club-btn");
const allClubsBtn = document.getElementById("all-clubs-btn");
const timelineBtn = document.getElementById("timeline-btn");
const compareBtn = document.getElementById("compare-btn");
const savesBtn = document.getElementById("saves-btn");
const restartBtn = document.getElementById("restart-btn");
const modalContainerEl = document.getElementById("modal-container");

// Initialize App
async function init() {
  setupGlobalListeners();
  
  const state = await ApiClient.getWorldState();
  if (state && state.world_id) {
    appState.worldState = state;
    await loadCurrentScreen();
  } else {
    showCreationModal();
  }
}

function getNextButtonLabel(stage, seasonYear) {
  switch (stage) {
    case 1: return "View Continental Qualifiers 🏆";
    case 2: return "Simulate Continental Cup Knockouts ⚔️";
    case 3: return "Proceed to Awards Ceremony 🏅";
    case 4: return "View Season Summary 📜";
    case 5: return "Go to Offseason Decisions 💼";
    case 6: return "Proceed to Transfer Window 🔄";
    case 7: return "Enter New Season Launchpad 🚀";
    case 8: return `Kick Off Season ${seasonYear || ''} Domestic Matches ⚽`;
    default: return "Continue ▶";
  }
}

function setupGlobalListeners() {
  nextBtn.addEventListener("click", async () => {
    nextBtn.disabled = true;
    nextBtn.innerText = "Simulating Calculations...";
    try {
      const res = await ApiClient.advanceNextStep();
      appState.worldState = await ApiClient.getWorldState();
      if (res && res.screen) {
        appState.currentScreenData = res.screen;
        renderScreen(res.screen);
        updateHeader();
      } else {
        await loadCurrentScreen();
      }
    } catch (e) {
      alert("Error advancing stage: " + e.message);
    } finally {
      nextBtn.disabled = false;
      const curStage = appState.currentScreenData?.stage || 1;
      const curYear = appState.currentScreenData?.season_year || appState.worldState?.current_season;
      nextBtn.innerText = getNextButtonLabel(curStage, curYear);
    }
  });

  if (myClubBtn) myClubBtn.addEventListener("click", showMyClubModal);
  if (allClubsBtn) allClubsBtn.addEventListener("click", showAllClubsModal);
  timelineBtn.addEventListener("click", showTimelineModal);
  compareBtn.addEventListener("click", showComparisonModal);
  savesBtn.addEventListener("click", showSavesModal);
  if (restartBtn) restartBtn.addEventListener("click", window.restartCareer);
  userChipEl.addEventListener("click", () => {
    if (appState.worldState?.user_player) {
      showPlayerCardModal(appState.worldState.user_player);
    }
  });
}

window.restartCareer = function() {
  if (confirm("Are you sure you want to restart and create a new career? Any unsaved progress will be reset.")) {
    modalContainerEl.innerHTML = "";
    showCreationModal();
  }
};

async function loadCurrentScreen() {
  const screen = await ApiClient.getCurrentScreen();
  appState.currentScreenData = screen;
  updateHeader();
  renderScreen(screen);
}

function updateHeader() {
  if (!appState.worldState) return;
  const user = appState.worldState.user_player;
  const club = appState.worldState.user_club;
  const leagueName = appState.worldState.league_name || "";
  const season = appState.currentScreenData?.season_year || appState.worldState.current_season;
  const stage = appState.currentScreenData?.stage || appState.worldState.current_stage;

  seasonNumEl.innerText = `Season ${season}`;
  if (user) {
    const isInjured = user.injury && user.injury.weeks_remaining > 0;
    userChipEl.innerHTML = `
      <span style="color:var(--accent-gold); font-weight:800;">${user.overall_rating}</span>
      <span>${user.name}</span>
      <span style="color:var(--accent-blue); font-size:0.8rem;">(${club ? club.name : 'Free Agent'} • ${leagueName})</span>
      ${isInjured ? `<span style="background:rgba(239,68,68,0.25); color:#ef4444; border:1px solid rgba(239,68,68,0.4); padding:2px 6px; border-radius:4px; font-size:0.75rem; font-weight:700;">🚑 Injured (${user.injury.weeks_remaining}w)</span>` : ''}
    `;
    userChipEl.style.display = "flex";
  }

  // Update Stepper
  for (let i = 1; i <= 8; i++) {
    const stepEl = document.getElementById(`step-indicator-${i}`);
    if (stepEl) {
      stepEl.className = "step-item";
      if (i === stage) stepEl.classList.add("active");
      else if (i < stage) stepEl.classList.add("completed");
    }
  }
}

window.declareRetirement = async function() {
  const user = appState.worldState?.user_player;
  const age = user ? user.age : 35;
  if (!confirm(`Are you sure you want to announce your retirement at age ${age}? Your playing career will officially conclude, your legacy stats will be finalized, and your status across all clubs will be inducted into the Hall of Fame.`)) {
    return;
  }
  try {
    const res = await ApiClient.retirePlayer();
    appState.worldState = await ApiClient.getWorldState();
    modalContainerEl.innerHTML = "";
    await showRetirementSummaryModal(res?.summary);
  } catch (e) {
    alert("Error retiring: " + e.message);
  }
};

// ==============================================================================
// SCREEN RENDERERS (8 STOPS)
// ==============================================================================
function renderScreen(screen) {
  contentEl.innerHTML = "";
  const stage = screen.stage;

  switch (stage) {
    case 1:
      renderStage1(screen);
      break;
    case 2:
      renderStage2(screen);
      break;
    case 3:
      renderStage3(screen);
      break;
    case 4:
      renderStage4(screen);
      break;
    case 5:
      renderStage5(screen);
      break;
    case 6:
      renderStage6(screen);
      break;
    case 7:
      renderStage7(screen);
      break;
    case 8:
      renderStage8(screen);
      break;
    default:
      contentEl.innerHTML = `<h2>Stage ${stage}</h2>`;
  }
  if (nextBtn) {
    nextBtn.innerText = getNextButtonLabel(stage, screen.season_year);
  }
}

// STAGE 1: LEAGUE SEASON
function renderStage1(data) {
  const leagues = Object.values(data.leagues);
  if (!appState.activeLeagueTab && leagues.length > 0) {
    appState.activeLeagueTab = leagues[0].id;
  }

  let tabsHtml = leagues.map(l => `
    <button class="tab-btn ${l.id === appState.activeLeagueTab ? 'active' : ''}" onclick="window.setLeagueTab('${l.id}')">
      ${l.name} (${l.country})
    </button>
  `).join("");

  const activeLeague = leagues.find(l => l.id === appState.activeLeagueTab) || leagues[0];
  const userClubId = data.user_club ? data.user_club.id : "";

  let rowsHtml = activeLeague.standings.map((s, idx) => `
    <tr class="${s.club_id === userClubId ? 'user-club-row' : ''}">
      <td><strong>${idx + 1}</strong></td>
      <td>
        <strong style="cursor:pointer; color:var(--accent-blue);" onclick="window.showClubDetails('${s.club_id}')">
          ${s.club_name}
        </strong>
      </td>
      <td>${s.played}</td>
      <td>${s.won}</td>
      <td>${s.drawn}</td>
      <td>${s.lost}</td>
      <td>${s.goals_for}</td>
      <td>${s.goals_against}</td>
      <td>${s.goal_difference > 0 ? '+' + s.goal_difference : s.goal_difference}</td>
      <td><strong style="color:var(--accent-gold);">${s.points}</strong></td>
    </tr>
  `).join("");

  contentEl.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <div>
        <h1 style="font-size:1.8rem; font-weight:800;">${data.title}</h1>
        <p style="color:var(--text-secondary);">38 match weeks simulated across 10 global top divisions.</p>
        <div style="margin-top:8px; font-size:0.875rem;">
          <span style="color:var(--text-muted);">Your Team:</span> 
          <strong style="cursor:pointer; color:var(--accent-blue);" onclick="window.showMyClubModal()">
            ${data.user_club ? data.user_club.name : 'Free Agent'}
          </strong> 
          <span style="color:var(--accent-gold);">(${data.league_name || activeLeague.name} • ${data.league_country || activeLeague.country})</span>
        </div>
      </div>
      <div>
        ${createPlayerCardHtml(data.user_player, 'compact')}
      </div>
    </div>

    <div class="tabs-header">${tabsHtml}</div>

    <div class="standings-table-container">
      <table class="standings-table">
        <thead>
          <tr>
            <th>Pos</th>
            <th>Club</th>
            <th>P</th>
            <th>W</th>
            <th>D</th>
            <th>L</th>
            <th>GF</th>
            <th>GA</th>
            <th>GD</th>
            <th>Pts</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>

    ${activeLeague.past_champions && activeLeague.past_champions.length > 0 ? `
      <div style="margin-top:24px; background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
          <h4 style="font-size:1.05rem; font-weight:800; color:var(--accent-gold); margin:0;">📜 ${activeLeague.name} — Roll of Champions (Past 10 Seasons)</h4>
          <span style="font-size:0.8rem; color:var(--text-secondary);">${activeLeague.record_scorer || ''}</span>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:10px;">
          ${activeLeague.past_champions.slice(0, 10).map(pc => `
            <div style="background:rgba(0,0,0,0.25); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:8px 12px;">
              <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700;">${pc.season_label} Champion</div>
              <div style="font-weight:800; font-size:0.95rem; color:#fff;">${pc.club_name}</div>
              <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">${pc.points} Pts • ${pc.top_scorer}</div>
            </div>
          `).join("")}
        </div>
      </div>
    ` : ''}
  `;
}

window.setLeagueTab = function(leagueId) {
  appState.activeLeagueTab = leagueId;
  renderScreen(appState.currentScreenData);
};

// STAGE 2: TOURNAMENT QUALIFICATION (32 Clubs)
function renderStage2(data) {
  let clubsHtml = data.qualified_clubs.map(c => `
    <div class="club-card" style="cursor:pointer;" onclick="window.showClubDetails('${c.id}')">
      <div class="club-crest" style="background:${c.primary_color}; border:2px solid ${c.secondary_color};">
        ${c.short_name}
      </div>
      <div>
        <div style="font-weight:700; font-size:1rem; color:#fff;">${c.name}</div>
        <div style="font-size:0.8rem; color:var(--text-secondary);">${c.country} • Titles: ${c.league_titles + c.tournament_titles} 🏆 • Budget: €${c.budget}M</div>
      </div>
    </div>
  `).join("");

  contentEl.innerHTML = `
    <div style="margin-bottom:24px;">
      <h1 style="font-size:1.8rem; font-weight:800;">${data.title}</h1>
      <p style="color:var(--text-secondary);">The premier 32 clubs across 10 global domestic leagues competing for continental and world supremacy (Top 3 per league + Best 2 4th-placed wildcards).</p>
      <div style="margin-top:12px; padding:12px 16px; background:var(--bg-glass); border-radius:var(--radius-sm); display:inline-block;">
        ${data.user_club_qualified ? 
          `<span style="color:var(--accent-green); font-weight:700;">✅ Your club (${data.user_club_name}) has qualified for the 32-team tournament!</span>` : 
          `<span style="color:var(--text-muted); font-weight:600;">❌ Your club (${data.user_club_name}) did not qualify this season.</span>`}
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:16px;">
      ${clubsHtml}
    </div>
  `;
}

// STAGE 3: TOURNAMENT RESULTS (32-Team Bracket)
function renderStage3(data) {
  const winner = data.winner_club;
  const runnerUp = data.runner_up_club;
  const rounds = data.tournament_rounds || {};

  const roundNames = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"];
  let roundsHtml = roundNames.filter(r => rounds[r] && rounds[r].length > 0).map(rName => {
    const matches = rounds[rName];
    return `
      <div style="margin-bottom:20px;">
        <h4 style="font-size:1.05rem; font-weight:800; color:var(--accent-blue); margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px;">
          ⚔️ ${rName} (${matches.length} ${matches.length === 1 ? 'Match' : 'Matches'})
        </h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:10px;">
          ${matches.map(m => `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
              <div style="flex:1;">
                <div style="font-weight:${m.winner_club_id === m.home_club_id ? '800' : '500'}; color:${m.winner_club_id === m.home_club_id ? 'var(--accent-gold)' : '#fff'}; font-size:0.85rem; cursor:pointer;" onclick="window.showClubDetails('${m.home_club_id}')">
                  ${m.home_club_name}
                </div>
                <div style="font-weight:${m.winner_club_id === m.away_club_id ? '800' : '500'}; color:${m.winner_club_id === m.away_club_id ? 'var(--accent-gold)' : '#fff'}; font-size:0.85rem; cursor:pointer; margin-top:2px;" onclick="window.showClubDetails('${m.away_club_id}')">
                  ${m.away_club_name}
                </div>
              </div>
              <div style="text-align:right; font-weight:900; font-size:1.1rem; color:var(--accent-blue); padding-left:12px;">
                ${m.home_goals} - ${m.away_goals}
                ${m.penalty_winner_id ? '<span style="font-size:0.65rem; color:var(--accent-gold); display:block;">(PK)</span>' : ''}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }).join("");

  contentEl.innerHTML = `
    <div style="text-align:center; margin-bottom:32px;">
      <span style="font-size:3rem;">🏆</span>
      <h1 style="font-size:2.2rem; font-weight:900; margin-top:8px; cursor:pointer; color:#fff;" onclick="window.showClubDetails('${winner.id}')">
        ${winner.name} Crowned Champions!
      </h1>
      <p style="color:var(--accent-gold); font-weight:700;">Winners of the Continental Champions Trophy (32-Club Tournament)</p>
      <p style="color:var(--text-secondary); margin-top:4px;">Runner-Up: <span style="cursor:pointer; color:var(--accent-blue);" onclick="window.showClubDetails('${runnerUp.id}')">${runnerUp.name}</span></p>
    </div>

    <!-- Knockout Bracket Summary -->
    <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:24px; margin-bottom:24px;">
      <h3 style="font-size:1.25rem; font-weight:800; margin-bottom:16px; color:var(--accent-gold);">🏆 Knockout Tournament Bracket</h3>
      ${roundsHtml}
    </div>

    ${data.international_tournament ? `
      <!-- Summer International Football Championship -->
      <div style="background:linear-gradient(135deg, rgba(30, 58, 138, 0.25) 0%, rgba(17, 24, 39, 0.8) 100%); border:2px solid var(--accent-blue); border-radius:var(--radius-lg); padding:24px; margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
          <div>
            <div style="font-size:0.8rem; font-weight:800; color:var(--accent-gold); text-transform:uppercase; letter-spacing:0.05em;">🌍 Quadrennial Summer Championship Cycle</div>
            <h2 style="font-size:1.6rem; font-weight:900; color:#fff; margin-top:4px;">${data.international_tournament.name}</h2>
          </div>
          <div style="text-align:right;">
            <span style="font-size:0.85rem; background:rgba(59,130,246,0.2); border:1px solid var(--accent-blue); color:var(--accent-blue); padding:4px 10px; border-radius:999px; font-weight:700;">
              ${ ({1:'QUALIFIERS & SUMMER SERIES', 2:'CONTINENTAL NATIONS CUP', 3:'NATIONS LEAGUE FINALS', 4:'WORLD CHAMPIONSHIP'})[data.international_tournament.cycle_year] || `CYCLE YEAR ${data.international_tournament.cycle_year}` }
            </span>
          </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:16px; margin-bottom:16px;">
          <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; text-align:center;">
            <div style="font-size:2rem;">👑</div>
            <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:800; text-transform:uppercase;">Champions</div>
            <div style="font-size:1.4rem; font-weight:900; color:#fff; margin-top:4px;">${data.international_tournament.winner_country}</div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:2px;">Defeated ${data.international_tournament.runner_up_country}</div>
          </div>

          ${data.international_tournament.top_scorer_name ? `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; text-align:center;">
              <div style="font-size:2rem;">👟</div>
              <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:800; text-transform:uppercase;">Golden Boot Top Scorer</div>
              <div style="font-size:1.2rem; font-weight:900; color:#fff; margin-top:4px;">${data.international_tournament.top_scorer_name}</div>
              <div style="font-size:0.85rem; color:var(--accent-green); font-weight:700; margin-top:2px;">${data.international_tournament.top_scorer_goals} Goals</div>
            </div>
          ` : ''}

          ${data.user_national_team ? `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; text-align:center;">
              <div style="font-size:2rem;">🏴</div>
              <div style="font-size:0.75rem; color:var(--accent-blue); font-weight:800; text-transform:uppercase;">Your National Team</div>
              <div style="font-size:1.2rem; font-weight:900; color:#fff; margin-top:4px;">${data.user_national_team.country}</div>
              <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:2px;">
                ${data.user_national_team.fifa_ranking ? `FIFA World Rank #${data.user_national_team.fifa_ranking}` : 'Senior National Squad'}
              </div>
              ${data.user_player ? `
                <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700; margin-top:4px;">
                  Status: ${data.user_player.national_team_status || 'Squad Member'} (${data.user_player.international_caps || 0} Caps • ${data.user_player.international_goals || 0}G)
                </div>
              ` : ''}
            </div>
          ` : ''}
        </div>

        ${(() => {
          const matches = data.international_tournament.matches || [];
          if (!matches.length) return '';
          const userCountry = data.user_national_team?.country;
          const userPlayerName = data.user_player?.name || appState.worldState?.user_player?.name;
          
          // Group by round
          const rounds = {};
          matches.forEach(m => { (rounds[m.round_name] = rounds[m.round_name] || []).push(m); });
          const roundOrder = ['Round of 16', 'Quarter-Finals', 'Semi-Finals', 'Final'];
          const sortedRounds = Object.keys(rounds).sort((a,b) => {
            const ai = roundOrder.indexOf(a), bi = roundOrder.indexOf(b);
            return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
          });
          return `
            <div style="margin-top:16px;">
              <h3 style="font-size:1.1rem; font-weight:800; color:var(--accent-blue); margin-bottom:12px;">🌍 Tournament Match Bracket & Fixtures</h3>
              ${sortedRounds.map(rName => `
                <div style="margin-bottom:16px;">
                  <div style="font-size:0.75rem; font-weight:800; color:var(--accent-gold); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">${rName}</div>
                  <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:10px;">
                    ${rounds[rName].map(m => {
                      const isUserCountry = userCountry && (m.home_country === userCountry || m.away_country === userCountry);
                      const wentToPens = Boolean(m.penalty_winner_country);
                      return `
                        <div style="background:rgba(0,0,0,0.35); border:1.5px solid ${isUserCountry ? 'var(--accent-blue)' : 'var(--border-color)'}; border-radius:var(--radius-sm); padding:12px 14px; position:relative;">
                          ${isUserCountry ? `<div style="position:absolute; top:4px; right:8px; font-size:0.65rem; color:var(--accent-blue); font-weight:800;">⭐ YOUR NATION</div>` : ''}
                          <div style="display:flex; justify-content:space-between; align-items:center; font-weight:800; font-size:1rem; color:#fff; margin-top:${isUserCountry ? '6px' : '0'};">
                            <span style="${m.home_country === userCountry ? 'color:var(--accent-blue); font-weight:900;' : ''}">${m.home_country}</span>
                            <span style="color:var(--accent-gold); font-size:1.15rem; padding:0 8px;">${m.home_goals} – ${m.away_goals}${wentToPens ? ' (P)' : ''}</span>
                            <span style="${m.away_country === userCountry ? 'color:var(--accent-blue); font-weight:900;' : ''}">${m.away_country}</span>
                          </div>
                          <div style="font-size:0.75rem; color:var(--accent-green); margin-top:4px; font-weight:700;">
                            🏆 ${m.winner_country} advanced${wentToPens ? ` (Won on penalties)` : ''}
                          </div>
                          ${m.scorers && m.scorers.length > 0 ? `
                            <div style="font-size:0.72rem; color:var(--text-secondary); margin-top:6px; line-height:1.3;">
                              ⚽ Scorers: ${m.scorers.map(s => {
                                const isUserScorer = userPlayerName && s.player_name && s.player_name.includes(userPlayerName);
                                return isUserScorer ? `<strong style="color:var(--accent-gold);">★ ${s.player_name} (YOU)</strong>` : (s.player_name || s.player_id);
                              }).join(', ')}
                            </div>
                          ` : ''}
                        </div>
                      `;
                    }).join('')}
                  </div>
                </div>
              `).join('')}
            </div>
          `;
        })()}
      </div>
    ` : ''}

    ${data.tournament_history && data.tournament_history.length > 0 ? `
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:20px;">
        <h3 style="font-size:1.15rem; font-weight:800; color:var(--accent-gold); margin-bottom:14px;">📜 Continental Champions Trophy — Roll of Honor</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr)); gap:12px;">
          ${data.tournament_history.map(th => `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:10px 14px;">
              <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700;">${th.season_label}</div>
              <div style="font-weight:800; color:#fff; font-size:1rem; margin:2px 0;">🏆 ${th.winner_name}</div>
              <div style="font-size:0.8rem; color:var(--text-secondary);">Runner-Up: ${th.runner_up_name} (${th.score})</div>
            </div>
          `).join("")}
        </div>
      </div>
    ` : ''}
  `;
}

// STAGE 4: AWARDS CEREMONY
function renderStage4(data) {
  const awards = data.awards;
  const ballonDor = awards.ballon_dor_winner;
  const leagueIds = Object.keys(awards.league_awards || {});
  
  if (!appState.activeAwardsLeagueTab && leagueIds.length > 0) {
    appState.activeAwardsLeagueTab = leagueIds[0];
  }

  const activeLeagueId = appState.activeAwardsLeagueTab || leagueIds[0];
  const activeLeagueAwards = (awards.league_awards && awards.league_awards[activeLeagueId]) || [];
  const activeLeagueTots = (awards.league_tots && awards.league_tots[activeLeagueId]) || [];
  const activeLeagueName = activeLeagueAwards[0] ? activeLeagueAwards[0].award_name.split(" ")[0] : "Domestic League";

  // League tabs
  const leagueTabsHtml = leagueIds.map(lid => {
    const lAwards = awards.league_awards[lid] || [];
    const name = lAwards[0] ? lAwards[0].award_name.split(" ")[0] : `League ${lid}`;
    return `
      <button class="tab-btn ${lid === activeLeagueId ? 'active' : ''}" onclick="window.setAwardsLeagueTab('${lid}')">
        ${name} Awards
      </button>
    `;
  }).join("");

  contentEl.innerHTML = `
    <div style="text-align:center; margin-bottom:28px;">
      <h1 style="font-size:2.2rem; font-weight:900; color:var(--accent-gold);">✨ World Football Awards Gala ✨</h1>
      <p style="color:var(--text-secondary);">Honoring the world's standout footballers across all 10 leagues for Season ${data.season_year}</p>
    </div>

    <!-- 1. WORLD GOLDEN BALL -->
    ${ballonDor ? `
      <div style="display:flex; justify-content:center; margin-bottom:32px;">
        <div style="background:linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(120,53,15,0.4) 50%, rgba(17,24,39,0.9) 100%); border:2px solid var(--accent-gold); border-radius:var(--radius-lg); padding:24px; text-align:center; max-width:480px; width:100%; box-shadow: 0 0 25px rgba(245,158,11,0.3);">
          <div style="font-size:2.2rem; margin-bottom:4px;">🌟</div>
          <div style="font-size:0.85rem; font-weight:800; color:var(--accent-gold); letter-spacing:0.08em; text-transform:uppercase;">World Golden Ball • World Player of the Year</div>
          <h2 style="font-size:1.9rem; font-weight:900; margin:10px 0 4px 0; color:#fff; cursor:pointer;" onclick="window.showCardDetails('${ballonDor.player_id}')">${ballonDor.player_name}</h2>
          <p style="color:var(--accent-blue); font-weight:700; margin-bottom:8px; cursor:pointer;" onclick="window.showClubDetails('${ballonDor.club_id}')">${ballonDor.club_name} (${ballonDor.position})</p>
          <div style="font-size:0.85rem; color:var(--text-secondary); background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:var(--radius-sm); display:inline-block;">${ballonDor.stat_summary}</div>
        </div>
      </div>
    ` : ''}

    <!-- 2. GLOBAL POSITIONAL TROPHIES -->
    <div style="margin-bottom:32px;">
      <h3 style="font-size:1.25rem; font-weight:800; color:#fff; margin-bottom:14px;">🏆 World Positional Honors & Accolades</h3>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:14px;">
        ${(awards.cross_league_awards || []).map(aw => `
          <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; border-left:3px solid var(--accent-gold);">
            <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:800; text-transform:uppercase; letter-spacing:0.04em;">${aw.award_name}</div>
            <div style="font-size:1.15rem; font-weight:800; margin-top:4px; cursor:pointer; color:#fff;" onclick="window.showCardDetails('${aw.player_id}')">${aw.player_name}</div>
            <div style="font-size:0.8rem; color:var(--accent-blue); cursor:pointer; margin-top:2px;" onclick="window.showClubDetails('${aw.club_id}')">${aw.club_name} (${aw.position || 'Star'})</div>
            <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:8px; background:rgba(0,0,0,0.2); padding:4px 8px; border-radius:var(--radius-sm);">${aw.stat_summary}</div>
          </div>
        `).join("")}
      </div>
    </div>

    <!-- 3. WORLD DREAM XI -->
    ${awards.world_xi && awards.world_xi.length > 0 ? `
      <div style="margin-bottom:32px; background:linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(0,0,0,0.35) 100%); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:20px;">
        <h3 style="font-size:1.25rem; font-weight:800; color:var(--accent-gold); margin-bottom:12px;">👑 World Dream XI — The Elite 11 of Football</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
          ${awards.world_xi.map(w => `
            <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(251,191,36,0.3); border-radius:var(--radius-sm); padding:10px; cursor:pointer;" onclick="window.showCardDetails('${w.player_id}')">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:#fff; font-size:0.9rem;">${w.player_name}</span>
                <span style="font-size:0.75rem; font-weight:800; color:${w.position === 'FWD' ? '#f87171' : w.position === 'MID' ? '#38bdf8' : w.position === 'DEF' ? '#34d399' : '#fbbf24'};">${w.position}</span>
              </div>
              <div style="font-size:0.75rem; color:var(--accent-blue);">${w.club_name}</div>
              <div style="font-size:0.7rem; color:var(--text-muted); margin-top:4px;">${w.stat_summary}</div>
            </div>
          `).join("")}
        </div>
      </div>
    ` : ''}

    <!-- 4. CONTINENTAL TOURNAMENT AWARDS -->
    ${awards.tournament_awards && awards.tournament_awards.length > 0 ? `
      <div style="margin-bottom:32px;">
        <h3 style="font-size:1.25rem; font-weight:800; color:#fff; margin-bottom:14px;">⚔️ Continental Tournament Silverware & Accolades</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px;">
          ${awards.tournament_awards.map(aw => `
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:14px;">
              <div style="font-size:0.75rem; color:var(--accent-green); font-weight:800; text-transform:uppercase;">${aw.award_name}</div>
              <div style="font-size:1.05rem; font-weight:800; margin-top:4px; cursor:pointer; color:#fff;" onclick="window.showCardDetails('${aw.player_id}')">${aw.player_name}</div>
              <div style="font-size:0.8rem; color:var(--accent-blue); cursor:pointer;" onclick="window.showClubDetails('${aw.club_id}')">${aw.club_name}</div>
              <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:6px;">${aw.stat_summary}</div>
            </div>
          `).join("")}
        </div>
      </div>
    ` : ''}

    <!-- 5. DOMESTIC LEAGUE AWARDS & TEAM OF THE SEASON -->
    <div>
      <h3 style="font-size:1.25rem; font-weight:800; color:var(--accent-blue); margin-bottom:12px;">🛡️ Domestic League Trophies & Official Honors</h3>
      <div class="table-tabs" style="margin-bottom:16px;">
        ${leagueTabsHtml}
      </div>

      <h4 style="font-size:1rem; font-weight:800; color:var(--accent-gold); margin-bottom:10px;">🌟 Official Individual Accolades</h4>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin-bottom:24px;">
        ${activeLeagueAwards.map(aw => `
          <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:14px; border-left:3px solid var(--accent-blue);">
            <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:800; text-transform:uppercase;">${aw.award_name}</div>
            <div style="font-size:1.1rem; font-weight:800; margin-top:4px; cursor:pointer; color:#fff;" onclick="window.showCardDetails('${aw.player_id}')">${aw.player_name}</div>
            <div style="font-size:0.8rem; color:var(--accent-blue); cursor:pointer;" onclick="window.showClubDetails('${aw.club_id}')">${aw.club_name} (${aw.position || 'Player'})</div>
            <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:6px; background:rgba(0,0,0,0.2); padding:4px 8px; border-radius:var(--radius-sm);">${aw.stat_summary}</div>
          </div>
        `).join("")}
      </div>

      ${activeLeagueTots.length > 0 ? `
        <h4 style="font-size:1rem; font-weight:800; color:var(--accent-gold); margin-bottom:10px;">⭐ Official Team of the Season (Best 11)</h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
          ${activeLeagueTots.map(t => `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:10px; cursor:pointer;" onclick="window.showCardDetails('${t.player_id}')">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:#fff; font-size:0.85rem;">${t.player_name}</span>
                <span style="font-size:0.75rem; font-weight:800; color:${t.position === 'FWD' ? '#f87171' : t.position === 'MID' ? '#38bdf8' : t.position === 'DEF' ? '#34d399' : '#fbbf24'};">${t.position}</span>
              </div>
              <div style="font-size:0.75rem; color:var(--accent-blue);">${t.club_name}</div>
              <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">${t.stat_summary}</div>
            </div>
          `).join("")}
        </div>
      ` : ''}
    </div>
  `;
}

window.setAwardsLeagueTab = function(leagueId) {
  appState.activeAwardsLeagueTab = leagueId;
  if (appState.currentScreenData) {
    renderStage4(appState.currentScreenData);
  }
};

// STAGE 5: SEASON SUMMARY & CAREER REPORT
function renderStage5(data) {
  const user = data.user_player;
  const club = data.user_club;

  contentEl.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px;">
      <div>
        <h1 style="font-size:1.8rem; font-weight:800;">${data.title}</h1>
        <p style="color:var(--text-secondary);">End of Season ${data.season_year} Performance & Narrative Recap</p>
      </div>
      <div>
        <div style="background:var(--bg-glass); border:1px solid var(--border-color); padding:10px 16px; border-radius:var(--radius-md); text-align:right;">
          <div style="font-size:0.8rem; color:var(--text-secondary);">World Position Rank</div>
          <div style="font-size:1.4rem; font-weight:900; color:var(--accent-blue);">#${data.position_rank}</div>
          <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:600;">Market Value: ${data.market_value_m}M</div>
        </div>
      </div>
    </div>

    <div style="display:grid; grid-template-columns:260px 1fr; gap:24px; margin-bottom:24px;">
      <div>${createPlayerCardHtml(user, 'full')}</div>

      <div>
        <h3 style="font-size:1.2rem; font-weight:800; margin-bottom:12px;">📰 Living World News & Storylines</h3>
        <div class="news-feed">
          ${data.storylines.map(s => `<div class="news-card">${s}</div>`).join("")}
        </div>
      </div>
    </div>
  `;
}

// Helper: Contract Status Banner
function renderContractStatusBanner(user, club, leagueName) {
  if (!user) return "";
  const contract = user.contract;
  const clubName = club?.name || contract?.club_name || "Free Agent";
  const yearsLeft = contract ? contract.years_remaining : 0;
  const isExpiring = !contract || yearsLeft <= 1;
  const statusColor = !contract ? '#ef4444' : (isExpiring ? '#f59e0b' : '#34d399');
  const statusText = !contract ? 'Free Agent (Unsigned)' : 
                     (yearsLeft <= 0 ? 'Expired' : 
                     (yearsLeft === 1 ? '1 Year Remaining (Final Year / Renewal Window)' : 
                     `${yearsLeft} Years Remaining (Secured)`));
  
  const marketVal = (Math.pow(user.overall_rating / 10, 2.8) * 0.12).toFixed(1);

  return `
    <div style="background:linear-gradient(135deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.95) 100%); border:1px solid ${isExpiring ? 'var(--accent-gold)' : 'var(--border-color)'}; border-radius:var(--radius-lg); padding:18px 22px; margin-bottom:24px; box-shadow:0 4px 20px rgba(0,0,0,0.3);">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
        <div style="display:flex; align-items:center; gap:14px;">
          <div style="font-size:2rem;">📋</div>
          <div>
            <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Current Contract & Squad Status</div>
            <div style="font-size:1.25rem; font-weight:900; color:#fff; margin-top:2px;">
              ${clubName} 
              <span style="font-size:0.85rem; color:var(--accent-blue); font-weight:600;">(${leagueName || appState.worldState?.league_name || 'Top Division'})</span>
            </div>
          </div>
        </div>
        
        <div style="display:flex; gap:20px; align-items:center;">
          <div style="text-align:right;">
            <div style="font-size:0.75rem; color:var(--text-secondary);">Contract Term</div>
            <div style="font-size:0.95rem; font-weight:800; color:${statusColor};">${statusText}</div>
          </div>
          <div style="text-align:right; border-left:1px solid var(--border-color); padding-left:20px;">
            <div style="font-size:0.75rem; color:var(--text-secondary);">Market Value</div>
            <div style="font-size:1.1rem; font-weight:900; color:var(--accent-gold);">${marketVal}M</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// STAGE 6: OFFSEASON & CONTRACT CHOICES
function renderStage6(data) {
  const user = data.user_player || appState.worldState?.user_player;
  const club = data.user_club || appState.worldState?.user_club;
  const leagueName = data.league_name || appState.worldState?.league_name;
  const lifestyle = data.lifestyle || {};

  if (!appState.activeStage6Tab) {
    appState.activeStage6Tab = "contracts";
  }

  const tabsHeaderHtml = `
    <div style="display:flex; gap:12px; margin-bottom:20px;">
      <button class="btn ${appState.activeStage6Tab === 'contracts' ? 'btn-primary' : ''}" onclick="window.setStage6Tab('contracts')">
        💼 Transfer Bids & Contracts ${data.needs_user_decision && data.user_offers?.length > 0 ? `(${data.user_offers.length})` : ''}
      </button>
      <button class="btn ${appState.activeStage6Tab === 'lifestyle' ? 'btn-primary' : ''}" onclick="window.setStage6Tab('lifestyle')">
        🌟 Lifestyle, Wealth & Personal Life (€${(lifestyle.net_worth || user?.net_worth || 0).toFixed(1)}M)
      </button>
    </div>
  `;

  let tabBodyHtml = "";

  if (appState.activeStage6Tab === "contracts") {
    let offersHtml = "";
    if (data.needs_user_decision && data.user_offers && data.user_offers.length > 0) {
      const isExpiring = user?.contract && user.contract.years_remaining <= 1;
      const descText = isExpiring 
        ? "Your contract is in its final year. Select your next destination or extend your contract:" 
        : `Transfer market is open! Clubs have submitted transfer fee bids for your signature. You may accept a transfer to a new club, extend your stay, or click 'Proceed to Transfer Window' below to honor your contract with ${club?.name || 'your club'}.`;

      offersHtml = `
        <div style="background:var(--bg-card); border:1px solid var(--accent-gold); border-radius:var(--radius-lg); padding:24px; margin-top:20px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
            <div>
              <h3 style="font-size:1.3rem; font-weight:800; color:var(--accent-gold); margin:0;">💼 Transfer Bids & Contract Decisions</h3>
              <p style="color:var(--text-secondary); margin-top:4px; max-width:700px;">${descText}</p>
            </div>
            <div style="background:rgba(251,191,36,0.1); border:1px solid var(--accent-gold); border-radius:var(--radius-sm); padding:6px 12px; font-size:0.8rem; color:var(--accent-gold);">
              💡 Note: Signing as Sub / Extra allows you to move to a powerhouse giant early and earn starting status through development.
            </div>
          </div>

          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:8px; margin:14px 0 18px 0; background:rgba(0,0,0,0.3); padding:10px 14px; border-radius:var(--radius-sm); border:1px solid var(--border-color); font-size:0.75rem;">
            <div><strong style="color:var(--accent-gold);">👑 Tier 1 (★★★★★):</strong> Elite Continental Giant</div>
            <div><strong style="color:var(--accent-blue);">💎 Tier 2 (★★★★):</strong> European Challenger</div>
            <div><strong style="color:var(--accent-green);">⚡ Tier 3 (★★★):</strong> Mid-Table Established</div>
            <div><strong style="color:var(--text-secondary);">🛡️ Tier 4 (★★):</strong> Top-Flight Underdog</div>
          </div>
          
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:18px; margin-top:16px;">
            ${data.user_offers.map(o => {
              const roleBadge = o.expected_role === 'Guaranteed Starter' 
                ? `<span style="background:rgba(52,211,153,0.15); color:#34d399; border:1px solid rgba(52,211,153,0.4); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:800;">★ Guaranteed Starter</span>`
                : (o.expected_role && o.expected_role.includes('Sub') 
                  ? `<span style="background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.4); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:800;">🔄 Impact Sub / Rotation</span>`
                  : `<span style="background:rgba(251,191,36,0.15); color:#fbbf24; border:1px solid rgba(251,191,36,0.4); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:800;">📋 Squad Depth / Backup</span>`);

              return `
                <div style="background:rgba(0,0,0,0.35); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:18px; display:flex; flex-direction:column; justify-content:space-between;">
                  <div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                      <div>
                        <div style="font-weight:900; font-size:1.15rem; color:#fff; cursor:pointer;" onclick="window.showClubDetails('${o.club_id}')">${o.club_name}</div>
                        <div style="font-size:0.8rem; color:var(--accent-blue); font-weight:600;">${o.league_name} • ${o.contract_years} Years Duration</div>
                        <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700; margin-top:3px;">
                          ${o.club_tier || 'Club'} <span style="color:#fbbf24;">(${o.club_stars || '★★★'})</span>
                        </div>
                        <div style="margin-top:6px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                          <span style="background:rgba(255,255,255,0.06); border:1px solid var(--border-color); padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700; color:#fff;">
                            ${o.trajectory_status || '⚖️ Stable Mid-Table'}
                          </span>
                          ${o.recent_form_display ? `
                            <span style="font-size:0.75rem; color:var(--text-muted);">
                              3-Yr Trajectory: <strong style="color:var(--accent-blue);">${o.recent_form_display}</strong>
                            </span>
                          ` : ''}
                        </div>
                      </div>
                      <div>${roleBadge}</div>
                    </div>
                    
                    <div style="background:rgba(255,255,255,0.03); border-left:3px solid var(--accent-gold); padding:8px 12px; margin:12px 0; font-size:0.85rem; color:var(--text-secondary); line-height:1.4;">
                      "${o.contextual_reason}"
                    </div>

                    <!-- Contract Package Breakdown -->
                    <div style="background:rgba(0,0,0,0.3); border-radius:var(--radius-sm); padding:10px 12px; margin-bottom:12px; font-size:0.8rem; display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                      <div>
                        <span style="color:var(--text-muted);">Annual Wage:</span><br>
                        <strong style="color:var(--accent-green); font-size:0.95rem;">€${(o.annual_wage || 1.0).toFixed(1)}M / yr</strong>
                      </div>
                      <div>
                        <span style="color:var(--text-muted);">Silverware Bonus:</span><br>
                        <strong style="color:var(--accent-gold); font-size:0.95rem;">+€${(o.silverware_bonus || 0.5).toFixed(1)}M</strong>
                      </div>
                      <div>
                        <span style="color:var(--text-muted);">Release Clause:</span><br>
                        <strong style="color:#fff;">${o.release_clause > 0 ? '€' + o.release_clause + 'M' : 'None'}</strong>
                      </div>
                      <div>
                        <span style="color:var(--text-muted);">Transfer Fee:</span><br>
                        <strong style="color:var(--accent-blue);">${o.compensation_fee > 0 ? '€' + o.compensation_fee + 'M' : 'Free / Renewal'}</strong>
                      </div>
                    </div>
                  </div>

                  <button class="btn btn-primary" style="margin-top:8px; width:100%; justify-content:center; padding:10px;" onclick="window.acceptOffer('${o.offer_id}')">
                    ${o.is_renewal ? 'Extend Contract ✍️' : `Sign with ${o.club_name} ✍️`}
                  </button>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      `;
    } else {
      offersHtml = `
        <div style="background:var(--bg-glass); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:20px; margin-top:20px; display:flex; align-items:center; gap:12px;">
          <span style="font-size:1.5rem;">✅</span>
          <div>
            <div style="font-weight:800; color:var(--accent-green);">Contract Secured for Upcoming Season</div>
            <p style="color:var(--text-secondary); font-size:0.875rem; margin-top:2px;">You have active years remaining with ${club?.name || 'your club'}. No transfer decisions are needed at this time.</p>
          </div>
        </div>
      `;
    }
    tabBodyHtml = `
      ${renderContractStatusBanner(user, club, leagueName)}
      ${offersHtml}
    `;
  } else {
    // LIFESTYLE & WEALTH TAB
    const netWorth = lifestyle.net_worth || user?.net_worth || 0.0;
    const wage = lifestyle.annual_wage || user?.annual_wage || 0.5;
    const relStatus = lifestyle.relationship_status || user?.relationship_status || 'Single';
    const partner = lifestyle.partner_name || user?.partner_name || null;
    const children = lifestyle.children || user?.children || [];
    const props = lifestyle.properties || user?.properties || [];
    const spons = lifestyle.sponsorship_deals || user?.sponsorship_deals || [];
    const availSpons = lifestyle.available_sponsorships || [];
    const availProps = lifestyle.available_properties || [];
    const lifeActions = lifestyle.available_life_actions || [];

    const partnerBackstory = lifestyle.partner_backstory || user?.partner_backstory || null;
    const partnerOrigin = lifestyle.partner_origin_story || user?.partner_origin_story || null;
    const meetingYear = lifestyle.partner_meeting_year || user?.partner_meeting_year || null;

    tabBodyHtml = `
      <!-- Wealth & Status Overview Bar -->
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:14px; margin-bottom:24px;">
        <div style="background:var(--bg-card); border:1px solid var(--accent-gold); border-radius:var(--radius-md); padding:16px;">
          <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:800; text-transform:uppercase;">Bank Net Worth</div>
          <div style="font-size:1.6rem; font-weight:900; color:#fff; margin-top:4px;">€${netWorth.toFixed(1)}M</div>
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">Club Salary: €${wage.toFixed(1)}M / yr</div>
        </div>

        <div style="background:var(--bg-card); border:1px solid var(--accent-pink, #ec4899); border-radius:var(--radius-md); padding:16px;">
          <div style="font-size:0.75rem; color:var(--accent-pink, #f472b6); font-weight:800; text-transform:uppercase;">Personal & Family Life</div>
          <div style="font-size:1.15rem; font-weight:800; color:#fff; margin-top:4px;">
            ${relStatus === 'Married' ? '💍 Married' : (relStatus === 'In a Relationship' ? '💘 Dating' : '👤 Single')}
          </div>
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">
            ${partner ? `Partner: <strong style="color:#fff;">${partner}</strong>` : 'No active partner'} • ${children.length > 0 ? `${children.length} Child (${children.join(', ')})` : 'No children'}
          </div>
          ${partnerBackstory ? `
            <div style="margin-top:6px;">
              <span style="display:inline-block; font-size:0.72rem; background:rgba(236,72,153,0.15); border:1px solid rgba(236,72,153,0.4); padding:2px 8px; border-radius:4px; color:#f472b6; font-weight:700;">
                ${partnerBackstory} ${meetingYear ? `(S${meetingYear})` : ''}
              </span>
              ${partnerOrigin ? `<div style="font-size:0.72rem; color:var(--text-secondary); margin-top:3px; font-style:italic; line-height:1.3;">"${partnerOrigin}"</div>` : ''}
            </div>
          ` : ''}
        </div>

        <div style="background:var(--bg-card); border:1px solid var(--accent-green); border-radius:var(--radius-md); padding:16px;">
          <div style="font-size:0.75rem; color:var(--accent-green); font-weight:800; text-transform:uppercase;">Endorsements & Assets</div>
          <div style="font-size:1.15rem; font-weight:800; color:#fff; margin-top:4px;">
            ${spons.length} Active Deals • ${props.length} Properties
          </div>
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:4px;">
            ${lifestyle.has_private_lab || user?.has_private_lab ? '🧬 Cryo-Recovery Lab Active' : 'Standard Club Medical Facilities'}
          </div>
        </div>
      </div>

      <!-- 1. Real Estate & Facilities -->
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:20px; margin-bottom:24px;">
        <h3 style="font-size:1.2rem; font-weight:800; color:var(--accent-gold); margin-bottom:12px;">🏡 Real Estate & High-Tech Facilities</h3>
        ${props.length > 0 ? `
          <div style="margin-bottom:14px; display:flex; flex-wrap:wrap; gap:8px;">
            ${props.map(p => `
              <span style="background:rgba(251,191,36,0.15); border:1px solid var(--accent-gold); padding:6px 12px; border-radius:6px; font-size:0.85rem; font-weight:700; color:#fff;">
                ✓ ${p}
              </span>
            `).join("")}
          </div>
        ` : '<p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:14px;">No properties acquired yet. Living in standard club accommodations.</p>'}

        <h4 style="font-size:0.95rem; font-weight:700; color:#fff; margin-bottom:10px;">Available for Acquisition:</h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
          ${availProps.map(p => `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:14px; display:flex; flex-direction:column; justify-content:space-between;">
              <div>
                <div style="font-weight:800; font-size:1.05rem; color:#fff;">${p.name}</div>
                <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:700; margin:3px 0 6px 0;">Cost: €${p.cost.toFixed(1)}M</div>
                <p style="font-size:0.8rem; color:var(--text-secondary); line-height:1.4;">${p.description}</p>
              </div>
              <button class="btn btn-primary" style="margin-top:12px; width:100%; justify-content:center; padding:8px;" 
                ${netWorth < p.cost ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}
                onclick="window.executeLifestyleAction('buy_property', '${p.id}')">
                ${netWorth >= p.cost ? 'Acquire Property ✍️' : `Requires €${p.cost.toFixed(1)}M`}
              </button>
            </div>
          `).join("")}
          ${availProps.length === 0 ? '<p style="font-size:0.85rem; color:var(--accent-green);">All premier real estate & facilities already acquired! 👑</p>' : ''}
        </div>
      </div>

      <!-- 2. Brand Sponsorship Deals -->
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:20px; margin-bottom:24px;">
        <h3 style="font-size:1.2rem; font-weight:800; color:var(--accent-blue); margin-bottom:12px;">👟 Commercial Sponsorships & Global Endorsements</h3>
        ${spons.length > 0 ? `
          <div style="margin-bottom:14px; display:flex; flex-wrap:wrap; gap:8px;">
            ${spons.map(s => `
              <span style="background:rgba(56,189,248,0.15); border:1px solid var(--accent-blue); padding:6px 12px; border-radius:6px; font-size:0.85rem; font-weight:700; color:#fff;">
                ✓ ${s.name} (+€${s.annual_payout}M/yr)
              </span>
            `).join("")}
          </div>
        ` : '<p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:14px;">No active commercial sponsorships signed.</p>'}

        <h4 style="font-size:0.95rem; font-weight:700; color:#fff; margin-bottom:10px;">Available Sponsorship Offers:</h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
          ${availSpons.map(s => `
            <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:14px; display:flex; flex-direction:column; justify-content:space-between;">
              <div>
                <div style="font-weight:800; font-size:1.05rem; color:#fff;">${s.name}</div>
                <div style="font-size:0.8rem; color:var(--accent-green); font-weight:700; margin:3px 0 6px 0;">Annual Payout: +€${s.annual_payout.toFixed(1)}M / year</div>
                <p style="font-size:0.8rem; color:var(--text-secondary); line-height:1.4;">${s.description}</p>
              </div>
              <button class="btn btn-primary" style="margin-top:12px; width:100%; justify-content:center; padding:8px;" onclick="window.executeLifestyleAction('sign_sponsorship', '${s.id}')">
                Sign Endorsement ✍️
              </button>
            </div>
          `).join("")}
          ${availSpons.length === 0 ? '<p style="font-size:0.85rem; color:var(--text-muted);">Reach higher overall ratings and win major silverware to attract prestigious brand sponsors.</p>' : ''}
        </div>
      </div>

      <!-- 3. Family & Personal Milestones -->
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:20px;">
        <h3 style="font-size:1.2rem; font-weight:800; color:var(--accent-green); margin-bottom:12px;">💖 Family & Life Journey</h3>
        ${lifeActions.length > 0 ? `
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
            ${lifeActions.map(a => `
              <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:14px; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                  <div style="font-weight:800; font-size:1.05rem; color:#fff;">${a.title}</div>
                  <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px; line-height:1.4;">${a.description}</p>
                </div>
                <button class="btn btn-primary" style="margin-top:12px; width:100%; justify-content:center; padding:8px;" onclick="window.executeFamilyAction('${a.action}')">
                  ${a.title}
                </button>
              </div>
            `).join("")}
          </div>
        ` : '<p style="font-size:0.85rem; color:var(--text-secondary);">Family journey is grounded and settled. Focus remains on pitch glory.</p>'}
      </div>
    `;
  }

  contentEl.innerHTML = `
    <div>
      <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:4px;">${data.title}</h1>
      <p style="color:var(--text-secondary); margin-bottom:20px;">Budgets distributed, youth intakes promoted, and retirements processed (${data.retired_players_count} retired).</p>
      
      ${tabsHeaderHtml}
      ${tabBodyHtml}
    </div>
  `;
}

window.setStage6Tab = function(tabName) {
  appState.activeStage6Tab = tabName;
  if (appState.currentScreenData) {
    renderStage6(appState.currentScreenData);
  }
};

window.executeLifestyleAction = async function(actionType, itemId) {
  try {
    const res = await ApiClient.performLifestyleAction(actionType, itemId);
    alert(res.message || "Action successful!");
    appState.worldState = await ApiClient.getWorldState();
    const screen = await ApiClient.getCurrentScreen();
    appState.currentScreenData = screen;
    renderStage6(screen);
    updateHeader();
  } catch (e) {
    alert("Error: " + e.message);
  }
};

window.executeFamilyAction = async function(subAction) {
  if (subAction === "meet_partner") {
    showMeetPartnerModal();
    return;
  }
  
  let customName = null;
  if (subAction === "have_child") {
    customName = prompt("Enter child's name (or leave empty for default):", "Leo");
  }
  try {
    const res = await ApiClient.performLifestyleAction("family_action", null, subAction, customName);
    alert(res.message || "Family milestone celebrated!");
    appState.worldState = await ApiClient.getWorldState();
    const screen = await ApiClient.getCurrentScreen();
    appState.currentScreenData = screen;
    renderStage6(screen);
    updateHeader();
  } catch (e) {
    alert("Error: " + e.message);
  }
};

function showMeetPartnerModal() {
  const lifestyle = appState.currentScreenData?.lifestyle || {};
  const backstories = lifestyle.meeting_backstories || [
    { id: "childhood_sweetheart", title: "🏡 Childhood Sweetheart", icon: "🏡", tagline: "Hometown Roots & Academy Days", description: "You grew up together in your hometown before your academy breakthrough." },
    { id: "college_friend", title: "🎓 University & Studies Friend", icon: "🎓", tagline: "Youth Academy & Campus Studies", description: "Met during your youth days while balancing training with campus studies." },
    { id: "charity_gala", title: "✨ Grassroots Charity & Community Gala", icon: "✨", tagline: "Philanthropy & Shared Purpose", description: "Crossed paths at a grassroots youth charity foundation event." },
    { id: "neighborhood_cafe", title: "☕ Serendipitous City Encounter", icon: "☕", tagline: "Quiet Sanctuary & Grounded Life", description: "A chance, peaceful meeting at a neighborhood coffee shop away from the noise." },
    { id: "creative_professional", title: "📸 Creative & Media Professional", icon: "📸", tagline: "Modern Passion & Shared Ambition", description: "Met through an editorial photoshoot, connecting over modern design and travel." }
  ];
  const defaultName = lifestyle.suggested_partner_name || "Elena Rossi";

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" style="max-width:680px;" onclick="event.stopPropagation()">
        <div class="modal-header">
          <div>
            <h3 style="margin:0;">💘 Begin New Relationship & Love Life</h3>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:3px;">
              Choose how you met your partner to shape your personal life narrative and family legacy.
            </div>
          </div>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <!-- Partner Name Input -->
          <div style="margin-bottom:20px; background:rgba(0,0,0,0.3); padding:14px; border-radius:var(--radius-md); border:1px solid var(--border-color);">
            <label style="display:block; font-size:0.85rem; font-weight:700; color:var(--accent-pink, #f472b6); margin-bottom:8px;">
              Partner's Name:
            </label>
            <div style="display:flex; gap:8px;">
              <input type="text" id="partner-name-input" value="${defaultName}" 
                style="flex:1; background:var(--bg-card); border:1px solid var(--border-color); color:#fff; padding:10px 14px; border-radius:var(--radius-sm); font-size:0.95rem; font-weight:600;" />
            </div>
            <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:6px;">
              Culturally authentic name suggested based on your home nation. Feel free to customize!
            </div>
          </div>

          <!-- Meeting Backstory Archetype Selection -->
          <label style="display:block; font-size:0.85rem; font-weight:700; color:#fff; margin-bottom:10px;">
            Select Meeting Backstory:
          </label>
          <div id="backstory-list" style="display:flex; flex-direction:column; gap:10px; margin-bottom:20px; max-height:300px; overflow-y:auto; padding-right:4px;">
            ${backstories.map((bs, idx) => `
              <div class="backstory-option" data-id="${bs.id}" onclick="window.selectBackstory('${bs.id}')"
                style="background: ${idx === 0 ? 'rgba(236,72,153,0.12)' : 'rgba(0,0,0,0.25)'}; 
                       border: 1.5px solid ${idx === 0 ? 'var(--accent-pink, #ec4899)' : 'var(--border-color)'}; 
                       border-radius: var(--radius-sm); padding: 12px; cursor: pointer; transition: all 0.2s ease;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div style="font-weight:800; font-size:0.95rem; color:#fff;">
                    ${bs.title}
                  </div>
                  <span style="font-size:0.75rem; color:var(--accent-pink, #f472b6); font-weight:700;">${bs.tagline}</span>
                </div>
                <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px; line-height:1.4;">
                  ${bs.description}
                </div>
              </div>
            `).join("")}
          </div>

          <input type="hidden" id="selected-backstory-id" value="${backstories[0].id}" />

          <button class="btn btn-primary" style="width:100%; justify-content:center; padding:12px; font-weight:800; font-size:1rem; background:linear-gradient(135deg, #ec4899 0%, #db2777 100%); border:none;" 
            onclick="window.confirmMeetPartner()">
            Confirm Relationship 💘
          </button>
        </div>
      </div>
    </div>
  `;
}

window.selectBackstory = function(bsId) {
  document.getElementById("selected-backstory-id").value = bsId;
  const cards = document.querySelectorAll(".backstory-option");
  cards.forEach(c => {
    if (c.getAttribute("data-id") === bsId) {
      c.style.background = "rgba(236,72,153,0.12)";
      c.style.borderColor = "var(--accent-pink, #ec4899)";
    } else {
      c.style.background = "rgba(0,0,0,0.25)";
      c.style.borderColor = "var(--border-color)";
    }
  });
};

window.confirmMeetPartner = async function() {
  const partnerName = document.getElementById("partner-name-input").value.trim() || "Elena Rossi";
  const backstoryId = document.getElementById("selected-backstory-id").value;
  try {
    const res = await ApiClient.performLifestyleAction("family_action", null, "meet_partner", partnerName, backstoryId);
    window.closeModal();
    alert(res.message || "Relationship started!");
    appState.worldState = await ApiClient.getWorldState();
    const screen = await ApiClient.getCurrentScreen();
    appState.currentScreenData = screen;
    renderStage6(screen);
    updateHeader();
  } catch (e) {
    alert("Error: " + e.message);
  }
};

window.acceptOffer = async function(offerId) {
  try {
    await ApiClient.submitChoice("transfer", offerId);
    alert("Contract successfully signed!");
    const nextStepRes = await ApiClient.advanceNextStep();
    appState.worldState = await ApiClient.getWorldState();
    if (nextStepRes && nextStepRes.screen) {
      appState.currentScreenData = nextStepRes.screen;
      renderScreen(nextStepRes.screen);
      updateHeader();
    } else {
      await loadCurrentScreen();
    }
  } catch (e) {
    alert("Error accepting offer: " + e.message);
  }
};

// STAGE 7: TRANSFER WINDOW
function renderStage7(data) {
  const user = data.user_player || appState.worldState?.user_player;
  const club = data.user_club || appState.worldState?.user_club;
  const leagueName = data.league_name || appState.worldState?.league_name;

  contentEl.innerHTML = `
    <div>
      <h1 style="font-size:1.8rem; font-weight:800; margin-bottom:4px;">${data.title}</h1>
      <p style="color:var(--text-secondary); margin-bottom:20px;">World transfer window concluded under the 5-signings squad limit.</p>
      
      ${renderContractStatusBanner(user, club, leagueName)}

      <div style="margin-top:20px; background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:20px;">
        <h3 style="font-size:1.1rem; font-weight:800; margin-bottom:6px;">Squads Stabilized & Ready</h3>
        <p style="color:var(--accent-blue); font-weight:600;">Rosters updated and squads stabilized across all 10 leagues for the upcoming campaign.</p>
        <button class="btn" style="margin-top:16px;" onclick="window.showAllClubsModal()">Browse All Club Rosters 🌐</button>
      </div>
    </div>
  `;
}

// STAGE 8: NEW SEASON PREVIEW
function renderStage8(data) {
  if (data.is_career_ended) {
    showRetirementSummaryModal();
    return;
  }

  const dev = data.development_report;
  let devHtml = "";
  if (dev) {
    const deltaText = dev.rating_delta > 0 ? `+${dev.rating_delta}` : `${dev.rating_delta}`;
    const deltaColor = dev.rating_delta > 0 ? 'var(--accent-green)' : (dev.rating_delta < 0 ? '#ef4444' : 'var(--text-muted)');
    const tierBadge = dev.review_summary || (dev.rating_delta > 0 ? `📈 Progressed (+${dev.rating_delta} OVR)` : (dev.rating_delta < 0 ? `⏳ Declined (${dev.rating_delta} OVR)` : '⚖️ Subdued Campaign (+0 OVR)'));

    devHtml = `
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:20px; max-width:650px; margin:20px auto; text-align:left;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:12px; margin-bottom:14px;">
          <div>
            <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Performance Review</div>
            <div style="font-size:1.1rem; font-weight:800; color:var(--accent-gold);">${tierBadge}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.8rem; color:var(--text-muted);">Rating Progression</div>
            <div style="font-size:1.3rem; font-weight:900; color:${deltaColor};">
              ${dev.prev_rating} ➔ ${dev.new_rating} (${deltaText})
            </div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; text-align:center;">
          <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:var(--radius-sm);">
            <div style="font-size:0.75rem; color:var(--text-secondary);">Matches</div>
            <div style="font-size:1.2rem; font-weight:800; color:#fff;">${dev.season_matches}</div>
          </div>
          <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:var(--radius-sm);">
            <div style="font-size:0.75rem; color:var(--text-secondary);">Goals</div>
            <div style="font-size:1.2rem; font-weight:800; color:var(--accent-green);">${dev.season_goals}</div>
          </div>
          <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:var(--radius-sm);">
            <div style="font-size:0.75rem; color:var(--text-secondary);">Assists</div>
            <div style="font-size:1.2rem; font-weight:800; color:var(--accent-blue);">${dev.season_assists}</div>
          </div>
          <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:var(--radius-sm);">
            <div style="font-size:0.75rem; color:var(--text-secondary);">Total G+A</div>
            <div style="font-size:1.2rem; font-weight:800; color:var(--accent-gold);">${dev.ga_total}</div>
          </div>
        </div>
      </div>
    `;
  }

  contentEl.innerHTML = `
    <div style="text-align:center; padding:20px 10px;">
      <h1 style="font-size:2.2rem; font-weight:900; color:var(--accent-blue);">${data.title}</h1>
      <p style="color:var(--text-secondary); margin-top:6px;">Offseason concluded. Rosters reset, fitness restored, and 38 match fixtures prepared for the new campaign.</p>
      
      ${devHtml}

      <div style="display:flex; justify-content:center; margin-top:20px;">
        ${createPlayerCardHtml(data.user_player, 'full')}
      </div>

      <div style="margin-top:24px; padding:16px; background:var(--bg-glass); border-radius:var(--radius-md); max-width:650px; margin-left:auto; margin-right:auto;">
        <span style="font-weight:700; color:var(--accent-gold);">⚡ Next Step:</span>
        <span style="color:var(--text-secondary); font-size:0.9rem;"> Click the bottom button to kick off and simulate the 38 domestic league match weeks of Season ${data.season_year}.</span>
      </div>
    </div>
  `;
}

// ==============================================================================
// FIFA / EFOOTBALL CARD GENERATOR
// ==============================================================================
function createPlayerCardHtml(player, mode = 'full') {
  if (!player) return "";
  const tierInfo = player.overall_rating >= 93 ? { class: 'card-god-level', label: '👑 GOD-LEVEL (93-100)', color: '#fef08a', bg: 'rgba(69, 26, 3, 0.9)' } :
                   player.overall_rating >= 85 ? { class: 'card-best', label: '⭐ WORLD-CLASS (85-92)', color: '#34d399', bg: 'rgba(2, 44, 34, 0.9)' } :
                   player.overall_rating >= 75 ? { class: 'card-elite', label: '⚡ ELITE (75-84)', color: '#818cf8', bg: 'rgba(30, 27, 75, 0.9)' } :
                   player.overall_rating >= 65 ? { class: 'card-gold', label: '🥇 GOLD (65-74)', color: '#fbbf24', bg: 'rgba(69, 39, 16, 0.9)' } :
                   player.overall_rating >= 55 ? { class: 'card-silver', label: '🥈 SILVER (55-64)', color: '#cbd5e1', bg: 'rgba(30, 41, 59, 0.9)' } :
                   { class: 'card-bronze', label: '🥉 BRONZE (<55)', color: '#fdba74', bg: 'rgba(67, 20, 7, 0.9)' };

  const clubName = player.club_name || (player.contract ? player.contract.club_name : "Free Agent");
  const leagueName = player.league_name ? ` • ${player.league_name}` : (appState.worldState?.league_name ? ` • ${appState.worldState.league_name}` : "");

  return `
    <div class="player-card ${tierInfo.class}" onclick="window.showCardDetails('${player.id}')">
      <div class="card-header-badge">
        <div class="card-rating-stack">
          <div class="card-rating-num">${player.overall_rating}</div>
          <div class="card-pos-tag">${player.position}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px;">
          <div class="card-country-tag">${player.country}</div>
          <span class="card-tier-pill" style="color:${tierInfo.color}; background:${tierInfo.bg}; border:1px solid ${tierInfo.color};">
            ${tierInfo.label}
          </span>
        </div>
      </div>

      <div class="card-avatar-area">
        <span class="card-avatar-icon">${player.overall_rating >= 93 ? '👑' : '⚽'}</span>
      </div>

      <div class="card-nameplate">
        <div class="card-player-name">${player.name}</div>
        <div class="card-club-name">${clubName}${leagueName}</div>
      </div>

      <div class="card-stats-grid">
        <div class="stat-item"><span class="stat-label">ATT</span><span class="stat-value">${player.attacking}</span></div>
        <div class="stat-item"><span class="stat-label">PLY</span><span class="stat-value">${player.playmaking}</span></div>
        <div class="stat-item"><span class="stat-label">DEF</span><span class="stat-value">${player.defending}</span></div>
        <div class="stat-item"><span class="stat-label">PHY</span><span class="stat-value">${player.physical}</span></div>
      </div>

      ${player.traits && player.traits.length > 0 ? `
        <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; justify-content:center;">
          ${player.traits.map(t => `
            <span style="font-size:0.65rem; background:rgba(0,0,0,0.6); border:1px solid rgba(255,255,255,0.25); padding:2px 6px; border-radius:4px; color:#fff; font-weight:700;">
              ${t}
            </span>
          `).join("")}
        </div>
      ` : ''}
    </div>
  `;
}

window.showCardDetails = async function(playerId) {
  try {
    const p = await ApiClient.getPlayerDetails(playerId);
    if (p) showPlayerCardModal(p);
  } catch (e) {
    console.error("Failed to load player card:", e);
  }
};

// ==============================================================================
// MODALS & PLAYER CREATION
// ==============================================================================
const COUNTRY_NAMES_FRONTEND = {
  "England": { first: ["Oliver", "Harry", "George", "Noah", "Arthur", "Jack", "Charlie", "Marcus", "Mason", "Declan", "Jude", "Cole"], last: ["Smith", "Jones", "Williams", "Taylor", "Brown", "Wilson", "Johnson", "Davies", "Kane", "Bellingham", "Saka", "Foden", "Palmer"] },
  "Spain": { first: ["Alejandro", "Mateo", "Lucas", "Leo", "Daniel", "Hugo", "Manuel", "Pablo", "Alvaro", "Gavi", "Pedri", "Lamine", "Rodri"], last: ["Garcia", "Rodriguez", "Gonzalez", "Fernandez", "Lopez", "Martinez", "Sanchez", "Perez", "Ramos", "Yamal", "Ruiz", "Morata", "Olmo"] },
  "France": { first: ["Gabriel", "Leo", "Raphael", "Louis", "Lucas", "Jules", "Antoine", "Kylian", "Aurelien", "Eduardo", "Theo", "Ousmane"], last: ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Mbappe", "Griezmann", "Camavinga", "Tchouameni", "Hernandez", "Dembele"] },
  "Germany": { first: ["Noah", "Matteo", "Elias", "Finn", "Leon", "Theo", "Paul", "Jamal", "Florian", "Kai", "Joshua", "Leroy"], last: ["Muller", "Schmidt", "Schneider", "Fischer", "Weber", "Musiala", "Wirtz", "Havertz", "Kimmich", "Sane", "Gundogan", "Kroos"] },
  "Italy": { first: ["Leonardo", "Francesco", "Alessandro", "Lorenzo", "Mattia", "Tommaso", "Nicolo", "Federico", "Gianluigi", "Sandro", "Giacomo"], last: ["Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Barella", "Chiesa", "Donnarumma", "Tonali", "Bastoni", "Dimarco"] },
  "Portugal": { first: ["Afonso", "Rodrigo", "Martim", "Santiago", "Duarte", "Tomas", "Bruno", "Bernardo", "Ruben", "Rafael", "Diogo"], last: ["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Fernandes", "Dias", "Leao", "Jota", "Cancelo", "Neves"] },
  "Netherlands": { first: ["Noah", "Sem", "Liam", "Lucas", "Daan", "Finn", "Frenkie", "Virgil", "Cody", "Xavi", "Jeremie"], last: ["De Jong", "Van Dijk", "De Vries", "Bakker", "Visser", "Gakpo", "Simons", "Frimpong", "Depay", "Ake", "Dumfries", "Koopmeiners"] },
  "Belgium": { first: ["Arthur", "Noah", "Jules", "Louis", "Lucas", "Liam", "Kevin", "Romelu", "Jeremy", "Amadou", "Leandro"], last: ["Peeters", "Janssens", "Maes", "Jacobs", "Willems", "De Bruyne", "Lukaku", "Doku", "Onana", "Trossard", "Tielemans"] },
  "Norway": { first: ["Jakob", "Emil", "Filip", "Noah", "Oliver", "Erling", "Martin", "Alexander", "Sander", "Antonio"], last: ["Hansen", "Johansen", "Olsen", "Larsen", "Haaland", "Odegaard", "Sorloth", "Berge", "Nusa", "Ryerson"] },
  "Sweden": { first: ["William", "Liam", "Noah", "Hugo", "Lucas", "Viktor", "Alexander", "Dejan", "Emil", "Lucas"], last: ["Andersson", "Johansson", "Karlsson", "Nilsson", "Gyokeres", "Isak", "Kulusevski", "Forsberg", "Bergvall"] },
  "Croatia": { first: ["Luka", "Ivan", "Marko", "David", "Mateo", "Dominik", "Josko", "Andrej", "Mario", "Borna"], last: ["Horvat", "Kovacevic", "Babic", "Maric", "Modric", "Kovacic", "Gvardiol", "Livakovic", "Kramaric", "Pasalic"] },
  "Denmark": { first: ["William", "Alfred", "Oscar", "Noah", "Karl", "Rasmus", "Christian", "Pierre", "Mikkel", "Joachim"], last: ["Nielsen", "Jensen", "Hansen", "Pedersen", "Hojlund", "Eriksen", "Hojbjerg", "Damsgaard", "Maehle"] },
  "Russia": { first: ["Aleksandr", "Mikhail", "Maksim", "Artyom", "Ivan", "Dmitry", "Daniil", "Matvey", "Ilya", "Kirill", "Aleksei"], last: ["Ivanov", "Smirnov", "Kuznetsov", "Popov", "Petrov", "Golovin", "Miranchuk", "Chalov", "Safonov", "Barinov", "Akinfeev"] },
  "Brazil": { first: ["Gabriel", "Lucas", "Matheus", "Arthur", "Davi", "Vinicius", "Rodrygo", "Endrick", "Neymar", "Casemiro"], last: ["Silva", "Santos", "Oliveira", "Souza", "Junior", "Goes", "Guimaraes", "Paqueta", "Alisson", "Ederson"] },
  "Argentina": { first: ["Mateo", "Bautista", "Juan", "Felipe", "Bruno", "Lautaro", "Lionel", "Julian", "Enzo", "Alexis", "Rodrigo"], last: ["Gonzalez", "Rodriguez", "Fernandez", "Martinez", "Messi", "Alvarez", "Romero", "Mac Allister", "De Paul", "Dybala"] },
  "Uruguay": { first: ["Santiago", "Mateo", "Agustin", "Lucas", "Federico", "Darwin", "Ronald", "Manuel", "Facundo"], last: ["Rodriguez", "Hernandez", "Valverde", "Nunez", "Araujo", "Ugarte", "Bentancur", "Pellistri", "Suarez", "Cavani"] },
  "Colombia": { first: ["Samuel", "Santiago", "Matias", "Emiliano", "Luis", "James", "Jhon", "Davinson", "Richard"], last: ["Rodriguez", "Gomez", "Gonzalez", "Diaz", "Duran", "Arias", "Rios", "Sinisterra", "Lucumi"] },
  "India": { first: ["Aarav", "Vihaan", "Vivaan", "Arjun", "Sai", "Sunil", "Manvir", "Sahal", "Anirudh", "Lallianzuala"], last: ["Sharma", "Patel", "Verma", "Singh", "Kumar", "Chhetri", "Thapa", "Samad", "Chhangte", "Bose"] },
  "Australia": { first: ["Oliver", "Noah", "Jack", "Henry", "William", "Nestory", "Garang", "Harry", "Jordan"], last: ["Smith", "Jones", "Williams", "Brown", "Irankunda", "Kuol", "Souttar", "Bos", "Baccus"] },
  "Japan": { first: ["Ren", "Haruto", "Minato", "Yuto", "Riku", "Kaoru", "Takefusa", "Wataru", "Daizen", "Ritsu"], last: ["Sato", "Suzuki", "Takahashi", "Tanaka", "Mitoma", "Kubo", "Endo", "Maeda", "Doan"] },
  "South Korea": { first: ["Min-jun", "Seo-jun", "Ha-jun", "Do-yun", "Heung-min", "Kang-in", "Min-jae", "Hee-chan"], last: ["Kim", "Lee", "Park", "Jeong", "Son", "Hwang", "Hong", "Song", "Oh"] },
  "USA": { first: ["Liam", "Noah", "Oliver", "James", "Christian", "Weston", "Folarin", "Tyler", "Timothy"], last: ["Smith", "Johnson", "Williams", "Pulisic", "McKennie", "Balogun", "Adams", "Weah"] }
};

function getRandomDefaultName(country) {
  const pool = COUNTRY_NAMES_FRONTEND[country] || COUNTRY_NAMES_FRONTEND["England"];
  const first = pool.first[Math.floor(Math.random() * pool.first.length)];
  const last = pool.last[Math.floor(Math.random() * pool.last.length)];
  return `${first} ${last}`;
}

function showCreationModal() {
  const initialCountry = "England";
  const initialName = getRandomDefaultName(initialCountry);

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop">
      <div class="creation-card">
        <h2>Create Your Footballer</h2>
        <p style="color:var(--text-secondary); margin-bottom:20px;">Begin your career journey from age 17 in the youth academy.</p>
        
        <form id="creation-form">
          <div class="form-group">
            <label>Nationality</label>
            <select id="create-country" class="form-select" onchange="window.onCreationCountryChange(this.value)">
              <optgroup label="Western Europe">
                <option value="England" selected>England 🏴󠁧󠁢󠁥󠁮󠁧󠁿</option>
                <option value="Spain">Spain 🇪🇸</option>
                <option value="France">France 🇫🇷</option>
                <option value="Germany">Germany 🇩🇪</option>
                <option value="Italy">Italy 🇮🇹</option>
                <option value="Portugal">Portugal 🇵🇹</option>
                <option value="Netherlands">Netherlands 🇳🇱</option>
                <option value="Belgium">Belgium 🇧🇪</option>
              </optgroup>
              <optgroup label="Northern & Eastern Europe">
                <option value="Norway">Norway 🇳🇴</option>
                <option value="Sweden">Sweden 🇸🇪</option>
                <option value="Croatia">Croatia 🇭🇷</option>
                <option value="Denmark">Denmark 🇩🇰</option>
                <option value="Russia">Russia 🇷🇺</option>
              </optgroup>
              <optgroup label="South America">
                <option value="Brazil">Brazil 🇧🇷</option>
                <option value="Argentina">Argentina 🇦🇷</option>
                <option value="Uruguay">Uruguay 🇺🇾</option>
                <option value="Colombia">Colombia 🇨🇴</option>
              </optgroup>
              <optgroup label="Asia, Oceania & North America">
                <option value="India">India 🇮🇳</option>
                <option value="Australia">Australia 🇦🇺</option>
                <option value="Japan">Japan 🇯🇵</option>
                <option value="South Korea">South Korea 🇰🇷</option>
                <option value="USA">USA 🇺🇸</option>
              </optgroup>
            </select>
          </div>
          <div class="form-group">
            <label>Player Name (Auto-Generated or Custom)</label>
            <div style="display:flex; gap:8px;">
              <input type="text" id="create-name" class="form-input" required value="${initialName}" style="flex:1;" />
              <button type="button" class="btn btn-secondary" onclick="window.randomizeCurrentName()" title="Randomize name for selected country">🎲</button>
            </div>
          </div>
          <div class="form-group">
            <label>Position</label>
            <select id="create-position" class="form-select">
              <option value="FWD">Forward (Striker / Winger)</option>
              <option value="MID">Midfielder (Playmaker / Box-to-Box)</option>
              <option value="DEF">Defender (Centre-Back / Full-Back)</option>
              <option value="GK">Goalkeeper (Shot-Stopper)</option>
            </select>
          </div>
          <button type="submit" class="btn btn-primary" style="width:100%; justify-content:center; padding:12px;">
            Start Career 🚀
          </button>
        </form>
      </div>
    </div>
  `;

  document.getElementById("creation-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("create-name").value;
    const country = document.getElementById("create-country").value;
    const position = document.getElementById("create-position").value;
    
    modalContainerEl.innerHTML = "";
    const res = await ApiClient.createNewWorld(name, country, position);
    appState.worldState = await ApiClient.getWorldState();
    
    if (res.origin_story) {
      showOriginStoryModal(res.origin_story);
    } else {
      await loadCurrentScreen();
    }
  });
}

window.onCreationCountryChange = function(country) {
  const nameInput = document.getElementById("create-name");
  if (nameInput) {
    nameInput.value = getRandomDefaultName(country);
  }
};

window.randomizeCurrentName = function() {
  const countrySelect = document.getElementById("create-country");
  const country = countrySelect ? countrySelect.value : "England";
  const nameInput = document.getElementById("create-name");
  if (nameInput) {
    nameInput.value = getRandomDefaultName(country);
  }
};

function showOriginStoryModal(story) {
  modalContainerEl.innerHTML = `
    <div class="modal-backdrop">
      <div class="modal-dialog" style="max-width:650px;">
        <div class="modal-header">
          <h3 style="color:var(--accent-gold);">🌟 ${story.title}</h3>
        </div>
        <div class="modal-body" style="line-height:1.6;">
          <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; margin-bottom:20px;">
            <div style="font-size:0.9rem; color:var(--accent-blue); font-weight:700;">Club & League Assignment</div>
            <div style="font-size:1.3rem; font-weight:800; color:#fff; margin:4px 0;">${story.club_name}</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">${story.league_name} (${story.club_country}) • Youth Infrastructure Tier ${story.infrastructure_level}</div>
          </div>

          <p style="font-size:1rem; color:var(--text-primary); margin-bottom:16px;">${story.narrative}</p>
          <p style="font-size:0.875rem; color:var(--text-secondary);">Ahead of you lie 5 domestic leagues, 100 historic clubs, continental tournaments, and the ultimate dream of claiming the World Golden Ball.</p>

          <button class="btn btn-primary" style="width:100%; justify-content:center; margin-top:24px; padding:12px;" onclick="window.closeModalAndLoad()">
            Step Onto the Pitch ⚽
          </button>
        </div>
      </div>
    </div>
  `;
}

window.closeModalAndLoad = async function() {
  modalContainerEl.innerHTML = "";
  await loadCurrentScreen();
};

function showPlayerCardModal(player) {
  const clubName = player.club_name || (player.contract ? player.contract.club_name : "Free Agent");
  const clubId = player.club_id || (player.contract ? player.contract.club_id : null);
  const leagueName = player.league_name || appState.worldState?.league_name || "Top Flight";
  const leagueCountry = player.league_country || appState.worldState?.league_country || player.country;
  const isInjured = player.injury && player.injury.weeks_remaining > 0;
  const history = player.history || [];

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" style="max-width:760px;" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>Player Profile & Career Record</h3>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body" style="max-height:80vh; overflow-y:auto; display:flex; flex-direction:column; align-items:center; gap:16px;">
          ${createPlayerCardHtml(player, 'full')}
          
          ${player.traits && player.traits.length > 0 ? `
            <div style="width:100%; background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:10px 14px;">
              <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:800; text-transform:uppercase; margin-bottom:6px;">⚡ Signature Playstyles & Traits</div>
              <div style="display:flex; flex-wrap:wrap; gap:8px;">
                ${player.traits.map(t => `
                  <span style="background:rgba(255,255,255,0.08); border:1px solid var(--accent-blue); padding:4px 10px; border-radius:6px; font-size:0.8rem; font-weight:800; color:#fff;">
                    ${t}
                  </span>
                `).join("")}
              </div>
            </div>
          ` : ''}

          ${isInjured ? `
            <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.4); border-radius:var(--radius-sm); padding:10px 14px; width:100%; display:flex; align-items:center; gap:10px;">
              <span style="font-size:1.4rem;">🚑</span>
              <div>
                <div style="font-weight:800; color:#ef4444; font-size:0.9rem;">Active Injury: ${player.injury.description}</div>
                <div style="font-size:0.75rem; color:var(--text-secondary);">${player.injury.weeks_remaining} match weeks remaining until full clearance.</div>
              </div>
            </div>
          ` : ''}

          <div style="width:100%; display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px; background:rgba(0,0,0,0.25); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-color); font-size:0.85rem;">
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Current Club:</span> <strong style="color:var(--accent-blue); display:block; cursor:pointer;" onclick="${clubId ? `window.showClubDetails('${clubId}')` : `window.showMyClubModal()`}">${clubName}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">League:</span> <strong style="color:var(--accent-gold); display:block;">${leagueName}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Age:</span> <strong style="display:block;">${player.age} Years</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Career Apps:</span> <strong style="display:block;">${player.career_matches}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Goals / Assists:</span> <strong style="color:var(--accent-green); display:block;">${player.career_goals}G / ${player.career_assists}A</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Clean Sheets / Saves:</span> <strong style="display:block;">${player.career_clean_sheets} CS / ${player.career_saves} Sv</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Trophies Won:</span> <strong style="color:var(--accent-gold); display:block;">${player.career_trophies} 🏆</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Golden Balls:</span> <strong style="color:var(--accent-gold); display:block;">${player.career_ballon_dors || 0} 🌟</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">National Team:</span> <strong style="color:var(--accent-blue); display:block;">${player.country} (${player.national_team_status || 'Eligible'}${player.is_national_team_captain ? ' ©' : ''})</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Int'l Caps / Goals:</span> <strong style="color:var(--accent-gold); display:block;">${player.international_caps || 0} Caps / ${player.international_goals || 0}G</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Int'l Silverware:</span> <strong style="color:var(--accent-gold); display:block;">${player.international_trophies || 0} Int'l 🏆</strong></div>
          </div>

          ${player.is_user || player.relationship_status !== 'Single' || (player.properties && player.properties.length > 0) ? `
            <div style="width:100%; background:rgba(0,0,0,0.25); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:12px 14px;">
              <div style="font-size:0.8rem; color:var(--accent-pink, #f472b6); font-weight:800; text-transform:uppercase; margin-bottom:6px;">💖 Personal Life, Love & Family Legacy</div>
              <div style="font-size:0.85rem; color:#fff; display:flex; flex-direction:column; gap:4px;">
                <div>
                  <strong>Status:</strong> ${player.relationship_status === 'Married' ? '💍 Married' : (player.relationship_status === 'In a Relationship' ? '💘 Dating' : '👤 Single')}
                  ${player.partner_name ? ` • Partner: <strong style="color:var(--accent-gold);">${player.partner_name}</strong>` : ''}
                  ${player.partner_backstory ? `<span style="font-size:0.75rem; background:rgba(236,72,153,0.15); border:1px solid rgba(236,72,153,0.4); padding:1px 6px; border-radius:4px; margin-left:6px; color:#f472b6;">${player.partner_backstory}</span>` : ''}
                </div>
                ${player.partner_origin_story ? `
                  <div style="font-size:0.75rem; color:var(--text-secondary); font-style:italic; line-height:1.3; margin-top:2px;">"${player.partner_origin_story}"</div>
                ` : ''}
                ${player.children && player.children.length > 0 ? `
                  <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:2px;">
                    👶 <strong>Children (${player.children.length}):</strong> ${player.children.join(', ')}
                  </div>
                ` : ''}
                ${player.properties && player.properties.length > 0 ? `
                  <div style="font-size:0.8rem; color:var(--accent-gold); margin-top:4px;">
                    🏡 <strong>Estates & Assets:</strong> ${player.properties.join(' • ')}
                  </div>
                ` : ''}
              </div>
            </div>
          ` : ''}

          ${history.length > 0 ? `
            <div style="width:100%; margin-top:8px;">
              <h4 style="font-size:0.95rem; font-weight:800; color:var(--accent-gold); margin-bottom:8px;">📜 Season-by-Season Career History</h4>
              <div style="max-height:220px; overflow-y:auto; border:1px solid var(--border-color); border-radius:var(--radius-sm);">
                <table style="width:100%; font-size:0.78rem; border-collapse:collapse; text-align:center;">
                  <thead>
                    <tr style="background:rgba(0,0,0,0.4); color:var(--text-secondary); font-size:0.72rem;">
                      <th style="padding:6px;">Season</th>
                      <th style="padding:6px; text-align:left;">Club</th>
                      <th style="padding:6px;">Apps</th>
                      <th style="padding:6px;">G</th>
                      <th style="padding:6px;">A</th>
                      <th style="padding:6px;">CS</th>
                      <th style="padding:6px;">OVR</th>
                      <th style="padding:6px; text-align:left;">Honors & Accolades</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${history.map(h => `
                      <tr style="border-bottom:1px solid var(--border-color);">
                        <td style="padding:6px; font-weight:700;">Season ${h.season_year}</td>
                        <td style="padding:6px; text-align:left; color:var(--accent-blue);">${h.club_name}</td>
                        <td style="padding:6px;">${h.matches_played}</td>
                        <td style="padding:6px; color:var(--accent-green); font-weight:700;">${h.goals}</td>
                        <td style="padding:6px; color:var(--accent-blue); font-weight:700;">${h.assists}</td>
                        <td style="padding:6px;">${h.clean_sheets}</td>
                        <td style="padding:6px; font-weight:800; color:var(--accent-gold);">${h.ending_rating}</td>
                        <td style="padding:6px; text-align:left; font-size:0.72rem;">
                          ${[...(h.trophies_won || []), ...(h.awards_won || [])].join(" • ") || '<span style="color:var(--text-muted);">-</span>'}
                        </td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
            </div>
          ` : '<div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">No completed seasons recorded yet. Play through the campaign to record your year-by-year history!</div>'}

          ${player.is_user && !appState.worldState?.is_career_ended ? `
            <button class="btn btn-secondary" style="border:1px solid #ef4444; color:#ef4444; width:100%; justify-content:center; margin-top:8px; padding:10px;" onclick="window.declareRetirement()">
              Announce Career Retirement 🎖️
            </button>
          ` : ''}
        </div>
      </div>
    </div>
  `;
}

// CLUB DETAILS & SQUAD INSPECTION MODAL
window.showMyClubModal = async function() {
  const clubData = await ApiClient.getMyClub();
  if (clubData) renderClubModal(clubData);
};

window.showClubDetails = async function(clubId) {
  const clubData = await ApiClient.getClubDetails(clubId);
  if (clubData) renderClubModal(clubData);
};

function renderClubModal(clubData) {
  const c = clubData.club;
  const squad = clubData.squad || [];
  const legends = c.legends || [];
  const titleYears = c.title_years || [];

  let squadRows = squad.map(p => `
    <tr style="cursor:pointer;" onclick="window.showCardDetails('${p.id}')">
      <td>
        <span style="font-weight:700; color:${p.position === 'FWD' ? '#f87171' : p.position === 'MID' ? '#38bdf8' : p.position === 'DEF' ? '#34d399' : '#fbbf24'};">${p.position}</span>
      </td>
      <td>
        <strong style="color:var(--accent-blue);" onclick="window.showCardDetails('${p.id}')">${p.name}</strong> 
        ${p.is_user ? '<span style="color:var(--accent-gold); font-size:0.75rem; background:rgba(251,191,36,0.2); padding:2px 6px; border-radius:4px; margin-left:4px;">YOU</span>' : ''}
        ${p.is_starter ? '<span style="color:var(--accent-green); font-size:0.75rem; margin-left:4px;">★ Starter</span>' : '<span style="color:var(--text-muted); font-size:0.75rem; margin-left:4px;">Bench</span>'}
      </td>
      <td><strong>${p.overall_rating}</strong></td>
      <td>${p.age}</td>
      <td>${p.country}</td>
      <td>${p.season_goals}</td>
      <td>${p.season_assists}</td>
      <td>${p.season_matches}</td>
    </tr>
  `).join("");

  let legendsHtml = legends.length > 0 ? `
    <div style="margin-top:20px; background:rgba(0,0,0,0.25); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px;">
      <h4 style="font-size:1.05rem; font-weight:800; color:var(--accent-gold); margin-bottom:10px;">🌟 Hall of Fame & Club Legends</h4>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px;">
        ${legends.map(leg => `
          <div style="background:rgba(255,255,255,0.03); border-left:3px solid var(--accent-gold); padding:10px 14px; border-radius:var(--radius-sm);">
            <div style="font-weight:800; color:#fff; font-size:0.95rem;">${leg.name} <span style="font-size:0.75rem; color:var(--accent-gold); font-weight:600;">(${leg.position})</span></div>
            <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">Era: ${leg.years_active} • ${leg.country}</div>
            <div style="font-size:0.8rem; color:var(--accent-blue); margin-top:4px;">
              ${leg.matches} Apps • ${leg.goals} Goals • ${leg.assists} Assists • ${leg.trophies} 🏆
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  ` : '';

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" style="max-width:920px;" onclick="event.stopPropagation()">
        <div class="modal-header">
          <div style="display:flex; align-items:center; gap:12px;">
            <div class="club-crest" style="background:${c.primary_color}; border:2px solid ${c.secondary_color}; width:48px; height:48px; font-size:1.1rem;">
              ${c.short_name}
            </div>
            <div>
              <h3 style="margin:0;">${c.name}</h3>
              <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:700;">
                ${c.tier_name ? `${c.tier_name} (${c.tier_stars})` :
                  (c.last_season_rank <= 4 ? '👑 Tier 1 • Elite Continental Giant (★★★★★)' :
                   c.last_season_rank <= 8 ? '💎 Tier 2 • Continental Challenger (★★★★)' :
                   c.last_season_rank <= 14 ? '⚡ Tier 3 • Mid-Table Established (★★★)' : '🛡️ Tier 4 • Top-Flight Underdog (★★)')}
                ${c.form_trajectory ? ` • <span style="color:#fff; background:rgba(255,255,255,0.08); padding:2px 6px; border-radius:4px;">${c.form_trajectory.badge}</span> <span style="color:var(--accent-blue); font-size:0.75rem;">(${c.form_trajectory.form_display})</span>` : ''}
              </div>
              <div style="font-size:0.8rem; color:var(--text-secondary);">${clubData.league_name} (${clubData.league_country}) • Est. ${c.founded_year || 1900} • Budget: ${c.budget}M</div>
            </div>
          </div>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body" style="max-height:75vh; overflow-y:auto;">
          <!-- Club Info Bar -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:12px; background:rgba(0,0,0,0.3); padding:12px 16px; border-radius:var(--radius-md); margin-bottom:16px;">
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Stadium:</span> <strong style="display:block; font-size:0.85rem;">${c.stadium_name || 'City Arena'}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Capacity:</span> <strong style="display:block;">${c.stadium_capacity ? c.stadium_capacity.toLocaleString() : '50,000'}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Budget:</span> <strong style="display:block; color:var(--accent-gold);">${c.budget}M</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Infrastructure:</span> <strong style="display:block;">Tier ${c.infrastructure_level} / 5</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">League Titles:</span> <strong style="display:block; color:var(--accent-blue);">${c.league_titles} 🏆</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.75rem;">Continental Cups:</span> <strong style="display:block; color:var(--accent-green);">${c.tournament_titles} 🏆</strong></div>
          </div>

          <!-- Trophy Heritage Note -->
          ${titleYears.length > 0 ? `
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:16px; background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.25); border-radius:var(--radius-sm); padding:8px 12px;">
              🏆 <strong>Championship Seasons:</strong> ${titleYears.join(", ")} ${c.historical_rival ? `• <span style="color:var(--accent-blue);">Historic Rival: ${c.historical_rival}</span>` : ''}
            </div>
          ` : ''}

          <!-- Squad Roster Table -->
          <h4 style="font-size:1.1rem; font-weight:800; margin-bottom:12px;">Full Squad Roster (${squad.length} Players • Click player for Card)</h4>
          <div class="standings-table-container" style="max-height:280px; overflow-y:auto; margin-top:0;">
            <table class="standings-table">
              <thead>
                <tr>
                  <th>Pos</th>
                  <th>Player Name</th>
                  <th>OVR</th>
                  <th>Age</th>
                  <th>Country</th>
                  <th>Goals</th>
                  <th>Assists</th>
                  <th>Apps</th>
                </tr>
              </thead>
              <tbody>${squadRows}</tbody>
            </table>
          </div>

          ${legendsHtml}
        </div>
      </div>
    </div>
  `;
}

// ALL CLUBS DIRECTORY MODAL
async function showAllClubsModal() {
  const directory = await ApiClient.getAllClubs();
  
  let leaguesHtml = directory.map(l => `
    <div style="margin-bottom:24px;">
      <h4 style="color:var(--accent-gold); font-size:1.1rem; margin-bottom:12px;">${l.league_name} (${l.league_country})</h4>
      <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:12px;">
        ${l.clubs.map(c => {
          const tierBadge = c.tier_stars ? `Tier ${c.tier_number || (c.last_season_rank <= 4 ? 1 : c.last_season_rank <= 8 ? 2 : c.last_season_rank <= 14 ? 3 : 4)} ${c.tier_stars}` :
                            (c.last_season_rank <= 4 ? '👑 Tier 1 ★★★★★' :
                             c.last_season_rank <= 8 ? '💎 Tier 2 ★★★★' :
                             c.last_season_rank <= 14 ? '⚡ Tier 3 ★★★' : '🛡️ Tier 4 ★★');
          return `
            <div class="club-card" style="padding:10px; cursor:pointer;" onclick="window.showClubDetails('${c.id}')">
              <div class="club-crest" style="background:${c.primary_color}; border:2px solid ${c.secondary_color}; width:38px; height:38px; font-size:0.85rem;">
                ${c.short_name}
              </div>
              <div>
                <div style="font-weight:700; font-size:0.9rem; color:#fff;">${c.name}</div>
                <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700;">${tierBadge}</div>
                ${c.form_trajectory ? `
                  <div style="font-size:0.72rem; color:#38bdf8; margin-top:1px;">
                    ${c.form_trajectory.badge} <span style="color:var(--text-muted);">(${c.form_trajectory.form_display})</span>
                  </div>
                ` : ''}
                <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">Titles: ${c.league_titles + c.tournament_titles} 🏆 • Est. ${c.founded_year || 1900} • Budget: ${c.budget}M</div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `).join("");

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" style="max-width:950px;" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>🌐 World Clubs Directory (100 Clubs)</h3>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body" style="max-height:75vh; overflow-y:auto;">
          <p style="color:var(--text-secondary); margin-bottom:20px;">Explore all 100 clubs across the 5 top divisions. Click any club to inspect its squad, budget, legends, and history:</p>
          ${leaguesHtml}
        </div>
      </div>
    </div>
  `;
}

async function showTimelineModal() {
  const timeline = await ApiClient.getTimeline();
  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>📜 Career Timeline & Achievements</h3>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; margin-bottom:24px; background:rgba(0,0,0,0.3); padding:16px; border-radius:var(--radius-md);">
            <div><span style="color:var(--text-secondary); font-size:0.8rem;">Matches:</span> <strong>${timeline.career_matches}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.8rem;">Goals:</span> <strong>${timeline.career_goals}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.8rem;">Assists:</span> <strong>${timeline.career_assists}</strong></div>
            <div><span style="color:var(--text-secondary); font-size:0.8rem;">Trophies:</span> <strong style="color:var(--accent-gold);">${timeline.career_trophies} 🏆</strong></div>
          </div>

          <h4 style="font-size:1.1rem; margin-bottom:12px;">Milestone Moments</h4>
          ${timeline.milestones.length > 0 ? `
            <div style="border-left:2px solid var(--accent-blue); padding-left:16px; display:flex; flex-direction:column; gap:16px;">
              ${timeline.milestones.map(m => `
                <div>
                  <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:700;">Season ${m.season_year} (Age ${m.age}) • ${m.club_name}</div>
                  <div style="font-weight:800; font-size:1rem; margin-top:2px;">${m.title}</div>
                  <div style="font-size:0.85rem; color:var(--text-secondary);">${m.description}</div>
                </div>
              `).join("")}
            </div>
          ` : '<p style="color:var(--text-secondary);">No milestones recorded yet. Play more seasons to forge your legacy!</p>'}
        </div>
      </div>
    </div>
  `;
}

async function showComparisonModal() {
  const comp = await ApiClient.getComparisons();
  const user = comp.user_player;
  const peers = comp.top_peers;

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" style="max-width:960px;" onclick="event.stopPropagation()">
        <div class="modal-header">
          <div>
            <h3 style="margin:0;">⚔️ Positional Comparison & Benchmarks (${user.position})</h3>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">
              At Age ${user.age} (${user.overall_rating} OVR), world stars represent developmental targets to surpass. Direct title rivalries ignite in the 80+ elite tier!
            </div>
          </div>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <div style="display:flex; gap:16px; overflow-x:auto; padding-bottom:12px;">
            <div>
              <div style="text-align:center; font-weight:800; color:var(--accent-gold); margin-bottom:8px; font-size:0.85rem; letter-spacing:0.05em;">★ YOU (AGE ${user.age})</div>
              ${createPlayerCardHtml(user, 'full')}
            </div>
            ${peers.map(p => {
              let tag = "⭐ WORLD BENCHMARK";
              let tagColor = "var(--text-secondary)";
              if (user.overall_rating >= 78 && Math.abs(p.overall_rating - user.overall_rating) <= 5) {
                tag = "🔥 DIRECT RIVAL";
                tagColor = "#f87171";
              } else if (p.overall_rating >= 88) {
                tag = "⭐ WORLD CLASS";
                tagColor = "var(--accent-gold)";
              } else {
                tag = "⚡ DIVISION PEER";
                tagColor = "var(--accent-blue)";
              }

              return `
                <div>
                  <div style="text-align:center; font-weight:800; color:${tagColor}; margin-bottom:8px; font-size:0.85rem; letter-spacing:0.05em;">${tag}</div>
                  ${createPlayerCardHtml(p, 'full')}
                </div>
              `;
            }).join("")}
          </div>
        </div>
      </div>
    </div>
  `;
}

async function showSavesModal() {
  const saves = await ApiClient.listSaves();
  modalContainerEl.innerHTML = `
    <div class="modal-backdrop" onclick="window.closeModal(event)">
      <div class="modal-dialog" style="max-width:600px;" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3>💾 Manual Save Manager</h3>
          <button class="modal-close" onclick="window.closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <div style="display:flex; gap:12px; margin-bottom:20px;">
            <input type="text" id="save-name-input" class="form-input" placeholder="Save point name..." value="Career Milestone" />
            <button class="btn btn-primary" onclick="window.executeSave()">Save Now</button>
          </div>

          <h4 style="font-size:1rem; margin-bottom:12px;">Saved Snapshots</h4>
          ${saves.length > 0 ? `
            <div style="display:flex; flex-direction:column; gap:8px;">
              ${saves.map(s => `
                <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:12px; display:flex; justify-content:space-between; align-items:center;">
                  <div>
                    <div style="font-weight:700;">${s.save_name}</div>
                    <div style="font-size:0.8rem; color:var(--text-secondary);">${s.player_name} • Season ${s.season} (${s.club_name}) • Rating ${s.overall_rating}</div>
                  </div>
                  <button class="btn" onclick="window.executeLoad('${s.save_id}')">Load</button>
                </div>
              `).join("")}
            </div>
          ` : '<p style="color:var(--text-secondary);">No saves found.</p>'}

          <div style="margin-top:24px; padding-top:16px; border-top:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.85rem; color:var(--text-secondary);">Want to begin a brand new journey?</span>
            <button class="btn" style="border-color:rgba(239,68,68,0.4); color:#fca5a5;" onclick="window.restartCareer()">Start New Career 🔄</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

window.executeSave = async function() {
  const name = document.getElementById("save-name-input").value;
  await ApiClient.makeManualSave(name);
  alert("World state saved successfully!");
  showSavesModal();
};

window.executeLoad = async function(saveId) {
  await ApiClient.loadSave(saveId);
  window.closeModal();
  appState.worldState = await ApiClient.getWorldState();
  await loadCurrentScreen();
};

window.closeModal = function(e) {
  modalContainerEl.innerHTML = "";
};

// ==============================================================================
// GRAND RETIREMENT & LEGACY SUMMARY MODAL
// ==============================================================================
async function showRetirementSummaryModal(summaryData) {
  let summary = summaryData;
  if (!summary || !summary.player_name) {
    try {
      summary = await ApiClient.getRetirementSummary();
    } catch (e) {
      console.error("Failed to load retirement summary:", e);
      return;
    }
  }

  const clubsHtml = summary.clubs_played_for && summary.clubs_played_for.length > 0 ? summary.clubs_played_for.map(c => {
    const seasonsStr = c.seasons && c.seasons.length > 0 
      ? `Season ${c.seasons.join(", ")} (${c.seasons.length} Season${c.seasons.length > 1 ? 's' : ''})` 
      : 'Career Era';
    const legendBadge = c.is_legend ? `
      <div style="margin-top:10px; background:linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(217,119,6,0.1) 100%); border:1px solid rgba(251,191,36,0.5); border-radius:var(--radius-sm); padding:8px 12px; display:flex; align-items:center; gap:8px;">
        <span style="font-size:1.2rem;">🏛️</span>
        <div>
          <div style="font-weight:900; font-size:0.85rem; color:var(--accent-gold); text-transform:uppercase; letter-spacing:0.04em;">Inducted into Club Hall of Fame Legends</div>
          <div style="font-size:0.78rem; color:var(--text-secondary);">${c.legend_title || 'Club Icon'}</div>
        </div>
      </div>
    ` : `
      <div style="margin-top:8px; font-size:0.73rem; color:var(--text-muted); background:rgba(0,0,0,0.2); padding:6px 10px; border-radius:var(--radius-sm);">
        <strong style="color:var(--text-secondary);">Threshold:</strong> ${c.threshold_desc || 'High milestone criteria required.'}
      </div>
    `;

    return `
      <div style="background:rgba(0,0,0,0.35); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.15rem; font-weight:800; color:#fff;">${c.club_name}</span>
              ${c.club_tier ? `<span style="font-size:0.75rem; color:var(--accent-gold); font-weight:700; background:rgba(251,191,36,0.1); padding:2px 6px; border-radius:4px;">${c.club_tier}</span>` : ''}
            </div>
            <div style="font-size:0.8rem; color:var(--accent-blue); font-weight:600; margin-top:2px;">${seasonsStr}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.85rem; color:var(--accent-gold); font-weight:800;">${(c.trophies || []).length} Trophies 🏆</div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-top:12px; text-align:center; background:rgba(255,255,255,0.02); padding:10px; border-radius:var(--radius-sm);">
          <div>
            <div style="font-size:0.7rem; color:var(--text-secondary);">Appearances</div>
            <div style="font-size:1.1rem; font-weight:800;">${c.matches}</div>
          </div>
          <div>
            <div style="font-size:0.7rem; color:var(--text-secondary);">Goals</div>
            <div style="font-size:1.1rem; font-weight:800; color:var(--accent-green);">${c.goals}</div>
          </div>
          <div>
            <div style="font-size:0.7rem; color:var(--text-secondary);">Assists</div>
            <div style="font-size:1.1rem; font-weight:800; color:var(--accent-blue);">${c.assists}</div>
          </div>
          <div>
            <div style="font-size:0.7rem; color:var(--text-secondary);">Clean Sheets</div>
            <div style="font-size:1.1rem; font-weight:800; color:#cbd5e1;">${c.clean_sheets}</div>
          </div>
        </div>

        ${legendBadge}
      </div>
    `;
  }).join("") : '<p style="color:var(--text-secondary);">No club history recorded.</p>';

  modalContainerEl.innerHTML = `
    <div class="modal-backdrop">
      <div class="modal-dialog" style="max-width:850px; max-height:90vh; overflow-y:auto;" onclick="event.stopPropagation()">
        <div class="modal-header" style="text-align:center; border-bottom:1px solid var(--border-color); padding-bottom:16px;">
          <div style="width:100%;">
            <div style="font-size:2rem; margin-bottom:4px;">🎖️</div>
            <h2 style="font-size:1.8rem; font-weight:900; color:var(--accent-gold); margin:0;">Career Legacy & Hall of Fame</h2>
            <p style="color:var(--text-secondary); font-size:0.9rem; margin-top:4px;">
              ${summary.player_name} (${summary.position} • ${summary.country}) — Retired at Age ${summary.age} • Final OVR ${summary.final_rating} (Peak ${summary.peak_rating})
            </p>
          </div>
        </div>

        <div class="modal-body" style="padding-top:16px;">
          <!-- Career Grand Totals -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(110px, 1fr)); gap:10px; margin-bottom:24px; text-align:center;">
            <div style="background:rgba(0,0,0,0.4); padding:12px 6px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
              <div style="font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase;">Seasons</div>
              <div style="font-size:1.3rem; font-weight:900; color:#fff;">${summary.total_seasons}</div>
            </div>
            <div style="background:rgba(0,0,0,0.4); padding:12px 6px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
              <div style="font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase;">Matches</div>
              <div style="font-size:1.3rem; font-weight:900; color:#fff;">${summary.career_matches}</div>
            </div>
            <div style="background:rgba(0,0,0,0.4); padding:12px 6px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
              <div style="font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase;">Goals</div>
              <div style="font-size:1.3rem; font-weight:900; color:var(--accent-green);">${summary.career_goals}</div>
            </div>
            <div style="background:rgba(0,0,0,0.4); padding:12px 6px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
              <div style="font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase;">Assists</div>
              <div style="font-size:1.3rem; font-weight:900; color:var(--accent-blue);">${summary.career_assists}</div>
            </div>
            <div style="background:rgba(0,0,0,0.4); padding:12px 6px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
              <div style="font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase;">Trophies</div>
              <div style="font-size:1.3rem; font-weight:900; color:var(--accent-gold);">${summary.career_trophies} 🏆</div>
            </div>
            <div style="background:rgba(0,0,0,0.4); padding:12px 6px; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
              <div style="font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase;">Golden Ball</div>
              <div style="font-size:1.3rem; font-weight:900; color:var(--accent-gold);">${summary.career_ballon_dors} 🌟</div>
            </div>
          </div>

          <!-- World Immortal Banner -->
          ${summary.world_hall_of_fame ? `
            <div style="background:linear-gradient(135deg, rgba(245,158,11,0.25) 0%, rgba(217,119,6,0.15) 50%, rgba(17,24,39,0.9) 100%); border:2px solid var(--accent-gold); border-radius:var(--radius-md); padding:16px; margin-bottom:20px; text-align:center; box-shadow: 0 0 20px rgba(245,158,11,0.25);">
              <div style="font-size:1.6rem; margin-bottom:2px;">👑</div>
              <div style="font-size:1.2rem; font-weight:900; color:var(--accent-gold); text-transform:uppercase; letter-spacing:0.06em;">${summary.world_hall_of_fame.title}</div>
              <div style="font-size:0.85rem; color:#fff; font-weight:700; margin-top:4px;">${summary.world_hall_of_fame.reason}</div>
            </div>
          ` : ''}

          <!-- Domestic League Hall of Fame -->
          ${summary.inducted_leagues && summary.inducted_leagues.length > 0 ? `
            <div style="margin-bottom:20px;">
              <h4 style="font-size:1.1rem; font-weight:800; color:var(--accent-blue); margin-bottom:10px;">
                🛡️ Domestic League Hall of Fame Inductions (${summary.inducted_leagues.length} Leagues)
              </h4>
              <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:10px;">
                ${summary.inducted_leagues.map(l => `
                  <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(56,189,248,0.4); border-radius:var(--radius-sm); padding:12px;">
                    <div style="font-size:1rem; font-weight:800; color:#fff;">${l.league_name} (${l.country})</div>
                    <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:700; margin-top:2px;">⭐ ${l.reason}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:6px;">${l.matches} Apps • ${l.goals}G / ${l.assists}A • ${l.titles} League Titles</div>
                  </div>
                `).join("")}
              </div>
            </div>
          ` : ''}

          <!-- Continental Tournament Hall of Fame -->
          ${summary.inducted_tournaments && summary.inducted_tournaments.length > 0 ? `
            <div style="margin-bottom:20px;">
              <h4 style="font-size:1.1rem; font-weight:800; color:var(--accent-green); margin-bottom:10px;">
                ⚔️ Continental Cup Hall of Fame
              </h4>
              <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:10px;">
                ${summary.inducted_tournaments.map(t => `
                  <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(52,211,153,0.4); border-radius:var(--radius-sm); padding:12px;">
                    <div style="font-size:1rem; font-weight:800; color:#fff;">${t.competition}</div>
                    <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:700; margin-top:2px;">🏆 ${t.reason}</div>
                  </div>
                `).join("")}
              </div>
            </div>
          ` : ''}

          <!-- International / National Team Hall of Fame -->
          ${summary.inducted_international && summary.inducted_international.length > 0 ? `
            <div style="margin-bottom:20px;">
              <h4 style="font-size:1.1rem; font-weight:800; color:var(--accent-gold); margin-bottom:10px;">
                🌍 International National Team Hall of Fame
              </h4>
              <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:10px;">
                ${summary.inducted_international.map(it => `
                  <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(245,158,11,0.4); border-radius:var(--radius-sm); padding:12px;">
                    <div style="font-size:1rem; font-weight:800; color:#fff;">🏴 ${it.country} National Team</div>
                    <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:700; margin-top:2px;">🎖️ ${it.reason}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:6px;">${it.caps} Caps • ${it.goals} Goals • ${it.assists} Assists • ${it.trophies} International Trophies</div>
                  </div>
                `).join("")}
              </div>
            </div>
          ` : ''}

          <!-- Clubs Played For & Legend Status -->
          <h4 style="font-size:1.1rem; font-weight:800; color:var(--accent-gold); margin-bottom:12px;">
            🏛️ Club Legacy & Hall of Fame Inductions (${summary.inducted_clubs ? summary.inducted_clubs.length : 0} Legend Titles)
          </h4>
          ${clubsHtml}

          <!-- Milestone Moments -->
          <div style="margin-top:20px;">
            <h4 style="font-size:1rem; font-weight:800; margin-bottom:8px; color:var(--text-secondary);">📜 Career Milestones</h4>
            <div style="max-height:160px; overflow-y:auto; border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:12px; background:rgba(0,0,0,0.2);">
              ${summary.milestones && summary.milestones.length > 0 ? summary.milestones.map(m => `
                <div style="font-size:0.8rem; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                  <span style="color:var(--accent-gold); font-weight:700;">Season ${m.season_year} (Age ${m.age}):</span> <strong>${m.title}</strong> — <span style="color:var(--text-secondary);">${m.description}</span>
                </div>
              `).join("") : '<p style="font-size:0.8rem; color:var(--text-secondary);">No milestones recorded.</p>'}
            </div>
          </div>

          <!-- Exit Actions -->
          <div style="margin-top:24px; padding-top:16px; border-top:1px solid var(--border-color); display:flex; gap:12px; justify-content:flex-end;">
            <button class="btn" onclick="window.showAllClubsModal()">Browse All Clubs 🌐</button>
            <button class="btn btn-primary" style="padding:10px 24px;" onclick="window.restartCareer()">Start New Career 🔄</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

window.showRetirementSummaryModal = showRetirementSummaryModal;

// Start App
init();
