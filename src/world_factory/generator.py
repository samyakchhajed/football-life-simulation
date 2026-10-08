import uuid
import random
from typing import Dict, List, Tuple
from src.engine.models import (
    WorldState, Player, Club, League, Position, Contract
)
from src.engine.names_database import get_random_name_for_country, ALL_SUPPORTED_COUNTRIES
from src.engine.traits import assign_initial_traits

LEAGUE_CONFIGS = [
    {"name": "Premier Division", "country": "England", "prefix": "ENG"},
    {"name": "Liga Primera", "country": "Spain", "prefix": "ESP"},
    {"name": "Serie Campionato", "country": "Italy", "prefix": "ITA"},
    {"name": "Meister Liga", "country": "Germany", "prefix": "GER"},
    {"name": "Ligue Championnat", "country": "France", "prefix": "FRA"},
    {"name": "Brasileirão Super Série", "country": "Brazil", "prefix": "BRA"},
    {"name": "Liga Argentina Primera", "country": "Argentina", "prefix": "ARG"},
    {"name": "Major Soccer Championship", "country": "USA", "prefix": "USA"},
    {"name": "Japan Super League", "country": "Japan", "prefix": "JPN"},
    {"name": "Indian Super Championship", "country": "India", "prefix": "IND"}
]

FICTIONAL_CLUBS_BY_COUNTRY = {
    "England": [
        ("Royal London FC", "LON", "Emperor Stadium", "#1e3a8a", "#fbbf24"),
        ("London Monarchs", "LNM", "Crown Park", "#0f172a", "#38bdf8"),
        ("Manchester Vulcan", "MNV", "Vulcan Arena", "#b91c1c", "#f3f4f6"),
        ("Manchester Sky", "MNS", "Starlight Ground", "#0284c7", "#ffffff"),
        ("Merseyside Iron", "MSI", "Harbor Coliseum", "#be123c", "#fecdd3"),
        ("Merseyside Harriers", "MSH", "Maritime Park", "#15803d", "#ffffff"),
        ("Midland Strikers", "MDS", "Forge Arena", "#7c3aed", "#e0e7ff"),
        ("Thames Apex", "THM", "Citadel Ground", "#c2410c", "#fed7aa"),
        ("Northumbria United", "NMB", "Castlegate Stadium", "#047857", "#facc15"),
        ("Yorkshire Titans", "YRK", "Titan Coliseum", "#4338ca", "#a5f3fc"),
        ("South Coast Mariners", "SCM", "Solent Park", "#0369a1", "#f0f9ff"),
        ("Avon Valley FC", "AVN", "Avon Meadow", "#854d0e", "#fef08a"),
        ("Trentside Dynamo", "TRN", "Trentview Stadium", "#991b1b", "#fee2e2"),
        ("East Anglian Harriers", "EAH", "Fens Arena", "#a16207", "#fef9c3"),
        ("Sussex Coast FC", "SXC", "Coastline Park", "#0e7490", "#cffafe"),
        ("Black Country Forge", "BCF", "Ironworks Ground", "#374151", "#f3f4f6"),
        ("Chiltern Athletic", "CHL", "Chiltern Stadium", "#166534", "#dcfce7"),
        ("Spire Royals", "SPR", "Spire Coliseum", "#6b21a8", "#f3e8ff"),
        ("Dales United", "DLS", "Dales Park", "#1e293b", "#94a3b8"),
        ("Potteries Town", "POT", "Kiln Arena", "#9a3412", "#ffedd5")
    ],
    "Spain": [
        ("Iberian Madrid", "IBM", "Iberian Coliseum", "#1e3a8a", "#fbbf24"),
        ("Castile Vanguard", "CSV", "Vanguard Stadium", "#b91c1c", "#ffffff"),
        ("Catalan Vanguard", "CTV", "Estadi Nou", "#047857", "#facc15"),
        ("Barcelona Stars", "BCS", "Starlight Arena", "#7c3aed", "#e0e7ff"),
        ("Turia Valencia", "TRV", "Turia Park", "#c2410c", "#fed7aa"),
        ("Andalucia Sevilla", "ANS", "Alcazar Stadium", "#be123c", "#fecdd3"),
        ("Sevilla Crest", "SVC", "Palmas Coliseum", "#15803d", "#ffffff"),
        ("Basque Athletic", "BSQ", "Lion Ground", "#991b1b", "#ffffff"),
        ("Bilbao Thunder", "BLB", "Thunder Park", "#0284c7", "#f0f9ff"),
        ("Villarreal Gold", "VRG", "Ceramic Stadium", "#ca8a04", "#fef08a"),
        ("San Sebastian Blue", "SSB", "Bahia Arena", "#1d4ed8", "#ffffff"),
        ("Aragon Crown", "ARC", "Imperial Coliseum", "#6b21a8", "#f3e8ff"),
        ("Costa del Sol FC", "CDS", "Solar Stadium", "#0284c7", "#ffffff"),
        ("Alhambra Stars", "ALH", "Sierra Arena", "#047857", "#fef08a"),
        ("Galicia Vigo", "GLV", "Atlantic Ground", "#0284c7", "#ffffff"),
        ("Riazor Waves", "RZW", "Wave Coliseum", "#1e40af", "#ffffff"),
        ("Asturias Miners", "ASM", "Forge Ground", "#b91c1c", "#374151"),
        ("Cantabria Green", "CNG", "Verde Arena", "#15803d", "#dcfce7"),
        ("Cordoba Caliphs", "CDC", "Arcadia Stadium", "#166534", "#ffffff"),
        ("Castile Violet", "CSL", "Violet Park", "#581c87", "#ffffff")
    ],
    "Italy": [
        ("Lombardy Red", "LBR", "San Cristoforo", "#b91c1c", "#111827"),
        ("Madonnina Blue", "MDB", "Duomo Arena", "#1d4ed8", "#111827"),
        ("Capitoline Wolves", "CPW", "Colosseo Stadium", "#991b1b", "#eab308"),
        ("Capitoline Eagles", "CPE", "Aquila Arena", "#38bdf8", "#ffffff"),
        ("Piedmont Zebras", "PDZ", "Alps Stadium", "#111827", "#ffffff"),
        ("Torino Bulls", "TRB", "Toro Ground", "#831843", "#ffffff"),
        ("Vesuvius Napoli", "VSN", "Golfo Coliseum", "#0284c7", "#ffffff"),
        ("Renaissance Firenze", "RNF", "Medici Arena", "#7c3aed", "#ffffff"),
        ("Ligurian Sailors", "LGS", "Porto Stadium", "#1e3a8a", "#dc2626"),
        ("Emilia Rosso", "EMR", "Torri Ground", "#b91c1c", "#1d4ed8"),
        ("Verona Mastiffs", "VRM", "Arena di Verona", "#eab308", "#1e3a8a"),
        ("Orobici Bergamo", "OBB", "Colle Arena", "#1e3a8a", "#111827"),
        ("Friuli White", "FRW", "Friuli Park", "#111827", "#ffffff"),
        ("Sardinia Islanders", "SRI", "Isola Stadium", "#991b1b", "#1e3a8a"),
        ("Ducal Parma", "DCP", "Ducale Arena", "#eab308", "#1e3a8a"),
        ("Apulia Mariners", "APM", "Adriatico Ground", "#dc2626", "#ffffff"),
        ("Lagoon Serenissima", "LGS", "Serenissima Park", "#15803d", "#f97316"),
        ("Brescia Lions", "BSL", "Leonessa Coliseum", "#1d4ed8", "#ffffff"),
        ("Tuscan Towers", "TST", "Torri Arena", "#111827", "#15803d"),
        ("Sicily Trinacria", "SCT", "Etna Stadium", "#db2777", "#111827")
    ],
    "Germany": [
        ("Bavaria Munich", "BVM", "Bavaria Arena", "#dc2626", "#ffffff"),
        ("Munich Crown", "MNC", "Kaiser Park", "#1d4ed8", "#ffffff"),
        ("Ruhr Dortmund", "RHD", "Westfalen Ground", "#eab308", "#111827"),
        ("Ruhr Miners", "RHM", "Knappen Arena", "#1d4ed8", "#ffffff"),
        ("Capital Berlin", "CPB", "Olympia Coliseum", "#1d4ed8", "#ffffff"),
        ("Berlin Iron", "BLI", "Alte Forsterei", "#dc2626", "#ffffff"),
        ("Rhine Frankfurt", "RNF", "Adler Stadium", "#111827", "#dc2626"),
        ("North Sea Hamburg", "NSH", "Hafen Arena", "#1d4ed8", "#dc2626"),
        ("Swabian Stuttgart", "SWB", "Neckar Ground", "#dc2626", "#ffffff"),
        ("Cathedral Koln", "CDK", "Dom Coliseum", "#dc2626", "#ffffff"),
        ("Saxony Leipzig", "SXL", "Zentral Stadium", "#dc2626", "#1d4ed8"),
        ("Weser Bremen", "WSB", "Weser Ground", "#15803d", "#ffffff"),
        ("Rhine Dusseldorf", "RND", "Rheinstadion", "#dc2626", "#ffffff"),
        ("Lower Saxony United", "LSU", "Niedersachsen Park", "#111827", "#15803d"),
        ("Franconian Nurnberg", "FKN", "Franken Stadium", "#831843", "#ffffff"),
        ("Black Forest Freiburg", "BFF", "Schwarzwald Arena", "#dc2626", "#111827"),
        ("Fugger Augsburg", "FGA", "Fugger Ground", "#dc2626", "#15803d"),
        ("Carnival Mainz", "CNM", "Bruchweg Arena", "#dc2626", "#ffffff"),
        ("Elbe Dresden", "EBD", "Dynamo Coliseum", "#eab308", "#111827"),
        ("Baltic Kiel", "BTK", "Holstein Park", "#1d4ed8", "#ffffff")
    ],
    "France": [
        ("Paris Lumiere", "PLM", "Parc des Lumieres", "#1e3a8a", "#dc2626"),
        ("Paris Capital", "PCP", "Capitale Arena", "#0f172a", "#38bdf8"),
        ("Mediterranean Marseille", "MDM", "Velodrome Maritime", "#0284c7", "#ffffff"),
        ("Rhone Lyon", "RNL", "Rhone Coliseum", "#1d4ed8", "#dc2626"),
        ("Riviera Monaco", "RVM", "Louis Palace Ground", "#dc2626", "#ffffff"),
        ("Flanders Lille", "FLL", "Grand Nord Stadium", "#dc2626", "#1e3a8a"),
        ("Gironde Bordeaux", "GRB", "Atlantique Arena", "#1e3a8a", "#ffffff"),
        ("Atlantic Nantes", "ATN", "Beaujoire Ground", "#eab308", "#15803d"),
        ("Breton Rennes", "BTR", "Armorique Stadium", "#dc2626", "#111827"),
        ("Cote d'Azur Nice", "CAN", "Riviera Stadium", "#dc2626", "#111827"),
        ("Occitanie Toulouse", "OCT", "Garonne Arena", "#7c3aed", "#ffffff"),
        ("Alsace Strasbourg", "ASS", "Meinau Ground", "#1d4ed8", "#ffffff"),
        ("Herault Montpellier", "HRM", "Mosson Park", "#1e3a8a", "#ea580c"),
        ("Northern Lens", "NTL", "Bollaert Coliseum", "#dc2626", "#eab308"),
        ("Champagne Reims", "CPR", "Auguste Park", "#dc2626", "#ffffff"),
        ("Lorraine Metz", "LRM", "Symphorien Ground", "#831843", "#ffffff"),
        ("Loire Greens", "LRG", "Geoffroy Stadium", "#15803d", "#ffffff"),
        ("Anjou Angers", "AJA", "Raymond Arena", "#111827", "#ffffff"),
        ("Finistere Brest", "FNB", "Francis Ground", "#dc2626", "#ffffff"),
        ("Port Le Havre", "PLH", "Ocean Stadium", "#1e3a8a", "#38bdf8")
    ],
    "Brazil": [
        ("Guanabara Red", "GBR", "Maracana Prime", "#dc2626", "#111827"),
        ("Carioca Waves", "CRW", "Sao Januario", "#111827", "#ffffff"),
        ("Paulista Vanguard", "PLV", "Morumbi Coliseum", "#dc2626", "#111827"),
        ("Sao Paulo Stars", "SPS", "Allianz Arena", "#15803d", "#ffffff"),
        ("Alvinegro Coastal", "AVC", "Vila Belmiro", "#111827", "#ffffff"),
        ("Gaucho Porto", "GCP", "Arena do Gremio", "#0284c7", "#111827"),
        ("Porto Alegre Reds", "PAR", "Beira-Rio", "#dc2626", "#ffffff"),
        ("Mineiro Belo", "MNB", "Mineirao Stadium", "#111827", "#ffffff"),
        ("Belo Cruzeiro", "BLC", "Pampulha Arena", "#1d4ed8", "#ffffff"),
        ("Baiano Salvador", "BNS", "Fonte Nova", "#1d4ed8", "#dc2626"),
        ("Paranaense Green", "PNG", "Baixada Arena", "#dc2626", "#111827"),
        ("Pernambuco Recife", "PBR", "Ilha do Retiro", "#dc2626", "#111827"),
        ("Ceara Fortaleza", "CRF", "Castelao Coliseum", "#1d4ed8", "#dc2626"),
        ("Federal Brasilia", "FDB", "Mane Garrincha", "#eab308", "#15803d"),
        ("Campinas Stars", "CMS", "Brinco Arena", "#15803d", "#ffffff"),
        ("Central Goiania", "CTG", "Serra Dourada", "#15803d", "#ffffff"),
        ("Island Florianopolis", "ISF", "Ressacada Park", "#1d4ed8", "#ffffff"),
        ("Amazon Belem", "AMB", "Mangueirao", "#1d4ed8", "#ffffff"),
        ("Solimoes Manaus", "SLM", "Amazonia Arena", "#15803d", "#eab308"),
        ("Pantanal Cuiaba", "PTC", "Pantanal Stadium", "#eab308", "#15803d")
    ],
    "Argentina": [
        ("Plata Vanguard", "PLV", "Monumental Arena", "#dc2626", "#ffffff"),
        ("Porteno Gold", "PTG", "Bombonera Coliseum", "#1e3a8a", "#eab308"),
        ("Avellaneda Crimson", "AVC", "Libertadores Ground", "#dc2626", "#ffffff"),
        ("Avellaneda Academia", "AVA", "Cilindro Stadium", "#38bdf8", "#ffffff"),
        ("Parana Rosario", "PRR", "Gigante de Arroyito", "#1e3a8a", "#eab308"),
        ("Rosario Red Stars", "RRS", "Coloso del Parque", "#dc2626", "#111827"),
        ("Sierras Cordoba", "SRC", "Kempes Coliseum", "#1d4ed8", "#ffffff"),
        ("Andes Mendoza", "ADM", "Malvinas Stadium", "#1d4ed8", "#ffffff"),
        ("Diagonal La Plata", "DLP", "Estudiantes Ground", "#dc2626", "#ffffff"),
        ("Atlantic Mar del Plata", "AMP", "Minella Arena", "#15803d", "#eab308"),
        ("Tucuman Sun", "TCS", "Monumental Tucuman", "#38bdf8", "#ffffff"),
        ("Santa Fe River", "SFR", "Brigadier Ground", "#dc2626", "#111827"),
        ("Salta Gauchos", "STG", "Padre Martearena", "#831843", "#ffffff"),
        ("Cuyo San Juan", "CYS", "Bicentenario Arena", "#15803d", "#111827"),
        ("Patagonia Neuquen", "PTN", "Sur Coliseum", "#1d4ed8", "#eab308"),
        ("Quilmes Rovers", "QMR", "Centenario Ground", "#1e3a8a", "#ffffff"),
        ("Lanus City", "LNC", "Fortaleza Arena", "#831843", "#ffffff"),
        ("Banfield Athletic", "BFA", "Florencio Sola", "#15803d", "#ffffff"),
        ("South Coast Bahia", "SCB", "Carminatti Stadium", "#eab308", "#111827"),
        ("Chaco Resistencia", "CKR", "Centenario Chaco", "#dc2626", "#eab308")
    ],
    "USA": [
        ("Empire New York", "ENY", "Empire Arena", "#1d4ed8", "#dc2626"),
        ("New York Metros", "NYM", "Gotham Coliseum", "#38bdf8", "#111827"),
        ("Pacific Los Angeles", "PLA", "Starlight Park", "#111827", "#eab308"),
        ("Angeles Starlight", "AST", "Dignity Coliseum", "#1e3a8a", "#eab308"),
        ("Windy City Chicago", "WCC", "Soldier Meadow", "#dc2626", "#1e3a8a"),
        ("Biscayne Miami", "BCM", "Biscayne Stadium", "#db2777", "#111827"),
        ("Emerald Seattle", "EMS", "Lumen Arena", "#15803d", "#1d4ed8"),
        ("Lone Star Austin", "LSA", "Q2 Park", "#15803d", "#111827"),
        ("Peachtree Atlanta", "PTA", "Mercedes Dome", "#dc2626", "#111827"),
        ("Texan Dallas", "TXD", "Toyota Arena", "#dc2626", "#1d4ed8"),
        ("Bay Area San Francisco", "BSF", "PayPal Park", "#1d4ed8", "#111827"),
        ("Liberty Philadelphia", "LBP", "Subaru Stadium", "#1e3a8a", "#eab308"),
        ("Harbor Boston", "HBB", "Gillette Arena", "#1e3a8a", "#dc2626"),
        ("Rose City Portland", "RCP", "Providence Ground", "#15803d", "#ca8a04"),
        ("Rocky Mountain Denver", "RMD", "Dick's Park", "#831843", "#38bdf8"),
        ("Space City Houston", "SCH", "Shell Energy Stadium", "#ea580c", "#111827"),
        ("Capitol Washington", "CPW", "Audi Field", "#111827", "#dc2626"),
        ("Music City Nashville", "MCN", "Geodis Coliseum", "#eab308", "#1e3a8a"),
        ("Sunshine Orlando", "SSO", "Exploria Arena", "#7c3aed", "#eab308"),
        ("Queen City Charlotte", "QCC", "Bank of America Arena", "#38bdf8", "#111827")
    ],
    "Japan": [
        ("Metropolis Tokyo", "MTK", "National Stadium", "#1d4ed8", "#dc2626"),
        ("Tokyo Vanguard", "TKV", "Ajinomoto Arena", "#15803d", "#ffffff"),
        ("Sakura Osaka", "SKO", "Nagai Coliseum", "#db2777", "#1e3a8a"),
        ("Osaka Crest", "OSC", "Panasonic Stadium", "#1d4ed8", "#111827"),
        ("Bay Yokohama", "BYK", "Nissan Stadium", "#1d4ed8", "#dc2626"),
        ("Castle Nagoya", "CNG", "Toyota Dome", "#dc2626", "#ca8a04"),
        ("Snow Sapporo", "SNS", "Sapporo Dome", "#dc2626", "#111827"),
        ("Hakata Fukuoka", "HKF", "Best Denki Arena", "#1e3a8a", "#38bdf8"),
        ("Port Kobe", "PKB", "Noevir Stadium", "#831843", "#ffffff"),
        ("Imperial Kyoto", "IKT", "Sanga Stadium", "#7c3aed", "#ffffff"),
        ("Peace Hiroshima", "PCH", "Edion Peace Wing", "#7c3aed", "#ffffff"),
        ("Forest Sendai", "FSD", "Yurtec Stadium", "#ca8a04", "#1d4ed8"),
        ("Saitama Crimson", "STC", "Saitama 2002", "#dc2626", "#111827"),
        ("Frontier Kawasaki", "FTK", "Todoroki Arena", "#38bdf8", "#111827"),
        ("Chiba Coast", "CBC", "Fukuda Arena", "#ca8a04", "#15803d"),
        ("Swan Niigata", "SWN", "Big Swan Stadium", "#ea580c", "#1d4ed8"),
        ("Fuji Shizuoka", "FJS", "IAI Stadium", "#ea580c", "#ffffff"),
        ("Kumamoto Flame", "KMF", "Egao Kenko Ground", "#dc2626", "#ffffff"),
        ("Okayama Pheasant", "OKP", "City Light Arena", "#831843", "#ffffff"),
        ("Volcano Kagoshima", "VKK", "Shiranami Stadium", "#1e3a8a", "#ffffff")
    ],
    "India": [
        ("Coastal Mumbai", "CMB", "Mumbai Football Arena", "#1d4ed8", "#ca8a04"),
        ("Bengal Kolkata", "BGK", "Salt Lake Coliseum", "#831843", "#ca8a04"),
        ("Kolkata Pioneers", "KKP", "Yuva Bharati Arena", "#15803d", "#831843"),
        ("Cyber Bengaluru", "CBB", "Kanteerava Stadium", "#1d4ed8", "#dc2626"),
        ("Mandovi Goa", "MDG", "Fatorda Coliseum", "#ea580c", "#1d4ed8"),
        ("Marina Chennai", "MNC", "Jawaharlal Nehru Stadium", "#1d4ed8", "#ca8a04"),
        ("Malabar Kerala", "MBK", "Kaloor Stadium", "#ca8a04", "#1d4ed8"),
        ("Northern Delhi", "NDL", "Ambedkar Stadium", "#dc2626", "#111827"),
        ("Deccan Hyderabad", "DCH", "Gachibowli Stadium", "#ca8a04", "#111827"),
        ("Maratha Pune", "MTP", "Balewadi Stadium", "#ea580c", "#7c3aed"),
        ("Brahmaputra Guwahati", "BPG", "Sarusajai Arena", "#ffffff", "#dc2626"),
        ("Steel Jamshedpur", "STJ", "JRD Tata Sports Complex", "#dc2626", "#1e3a8a"),
        ("Sabarmati Ahmedabad", "SMA", "TransStadia Coliseum", "#dc2626", "#ca8a04"),
        ("Tricity Chandigarh", "TCC", "Sector 42 Stadium", "#1d4ed8", "#ffffff"),
        ("Pink City Jaipur", "PCJ", "Sawai Mansingh Arena", "#db2777", "#ca8a04"),
        ("Kalinga Bhubaneswar", "KGB", "Kalinga Stadium", "#111827", "#7c3aed"),
        ("Nawabs Lucknow", "NWL", "Ekana Football Complex", "#15803d", "#ca8a04"),
        ("Highlands Shillong", "HLS", "Polo Grounds", "#dc2626", "#ffffff"),
        ("Malabar Kozhikode", "MBZ", "EMS Stadium", "#15803d", "#ca8a04"),
        ("Manipur Imphal", "MPI", "Khuman Lampak Stadium", "#ea580c", "#15803d")
    ]
}

class WorldGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_fresh_world(self, user_name: str, user_country: str, user_position: Position) -> WorldState:
        world = WorldState(
            world_id=f"wld_seed_{self.seed}",
            seed=self.seed,
            user_player_id="user_player_temp"
        )
        
        all_clubs: Dict[str, Club] = {}
        all_players: Dict[str, Player] = {}
        all_leagues: Dict[str, League] = {}

        # 1. Generate 10 Leagues and 200 Fictional Clubs (20 per league)
        for l_idx, l_cfg in enumerate(LEAGUE_CONFIGS):
            league_id = f"lg_{l_cfg['prefix'].lower()}"
            club_ids: List[str] = []
            fictional_clubs_pool = FICTIONAL_CLUBS_BY_COUNTRY[l_cfg["country"]]
            league_clubs: List[Club] = []
            
            for c_idx in range(20):
                club_id = f"clb_{l_cfg['prefix'].lower()}_{c_idx+1}"
                club_name, short_name, stadium_name, pri_col, sec_col = fictional_clubs_pool[c_idx]
                
                # Hierarchy: Rank 1-4 are historical giants, 5-10 challengers, 11-20 mid-table/underdogs
                if c_idx < 4:
                    league_titles = self.rng.randint(9, 20)
                    tournament_titles = self.rng.randint(2, 6)
                    infra = self.rng.choice([4, 5])
                    budget = self.rng.randint(120, 185)
                    stadium_cap = self.rng.randint(62000, 85000)
                    past_years = [str(2024 - y) for y in sorted(self.rng.sample(range(1, 25), min(league_titles, 6)))]
                elif c_idx < 10:
                    league_titles = self.rng.randint(2, 6)
                    tournament_titles = 1 if self.rng.random() < 0.35 else 0
                    infra = self.rng.randint(2, 4)
                    budget = self.rng.randint(70, 115)
                    stadium_cap = self.rng.randint(42000, 58000)
                    past_years = [str(2024 - y) for y in sorted(self.rng.sample(range(1, 25), min(league_titles, 3)))]
                else:
                    league_titles = 1 if self.rng.random() < 0.20 else 0
                    tournament_titles = 0
                    infra = self.rng.randint(1, 3)
                    budget = self.rng.randint(40, 68)
                    stadium_cap = self.rng.randint(24000, 38000)
                    past_years = ["2008"] if league_titles > 0 else []
                
                founded_year = self.rng.randint(1885, 1928)
                rival_tuple = fictional_clubs_pool[(c_idx + 1) % 20]
                
                # Generate 2 Historical Retired Club Legends
                from src.engine.models.club import ClubLegend
                _, _, leg_name1 = get_random_name_for_country(l_cfg["country"], self.rng)
                _, _, leg_name2 = get_random_name_for_country(l_cfg["country"], self.rng)
                legends = [
                    ClubLegend(
                        player_id=f"leg_{club_id}_1",
                        name=leg_name1,
                        country=l_cfg["country"],
                        position="FWD",
                        years_active=f"{self.rng.randint(1996, 2004)}-{self.rng.randint(2010, 2018)}",
                        matches=self.rng.randint(340, 580),
                        goals=self.rng.randint(140, 310),
                        assists=self.rng.randint(60, 150),
                        trophies=league_titles + tournament_titles,
                        legacy_score=round(self.rng.uniform(8.7, 9.9), 2)
                    ),
                    ClubLegend(
                        player_id=f"leg_{club_id}_2",
                        name=leg_name2,
                        country=l_cfg["country"],
                        position=self.rng.choice(["MID", "DEF"]),
                        years_active=f"{self.rng.randint(2002, 2008)}-{self.rng.randint(2015, 2022)}",
                        matches=self.rng.randint(310, 520),
                        goals=self.rng.randint(30, 95),
                        assists=self.rng.randint(70, 180),
                        trophies=max(1, league_titles - 2),
                        legacy_score=round(self.rng.uniform(8.2, 9.5), 2)
                    )
                ]
                
                club = Club(
                    id=club_id,
                    name=club_name,
                    short_name=short_name,
                    league_id=league_id,
                    country=l_cfg["country"],
                    budget=budget,
                    infrastructure_level=infra,
                    primary_color=pri_col,
                    secondary_color=sec_col,
                    last_season_rank=c_idx + 1,
                    recent_ranks=[
                        max(1, min(20, c_idx + 1 + self.rng.randint(-1, 1))),
                        max(1, min(20, c_idx + 1 + self.rng.randint(-1, 1))),
                        c_idx + 1
                    ],
                    founded_year=founded_year,
                    stadium_name=stadium_name,
                    stadium_capacity=stadium_cap,
                    historical_rival=rival_tuple[0],
                    league_titles=league_titles,
                    tournament_titles=tournament_titles,
                    title_years=past_years,
                    legends=legends
                )
                
                # Generate 20 players for this club (2 GK, 6 DEF, 6 MID, 6 FWD)
                self._generate_club_squad(club, all_players, l_cfg["country"])
                all_clubs[club_id] = club
                club_ids.append(club_id)
                league_clubs.append(club)
                
            fixtures = self._generate_double_round_robin_fixtures(club_ids)
            
            # Generate 10 Years of Past League Champions
            top_league_clubs = sorted(league_clubs, key=lambda c: c.league_titles, reverse=True)
            past_champs = []
            for y_back in range(1, 11):
                c_winner = self.rng.choice(top_league_clubs[:4])
                _, _, top_scorer_name = get_random_name_for_country(l_cfg["country"], self.rng)
                past_champs.append({
                    "season_label": f"{2024 - y_back}/{str(2025 - y_back)[-2:]}",
                    "club_name": c_winner.name,
                    "club_id": c_winner.id,
                    "points": self.rng.randint(84, 98),
                    "top_scorer": f"{top_scorer_name} ({self.rng.randint(24, 38)} Goals)"
                })
                
            league = League(
                id=league_id,
                name=l_cfg["name"],
                country=l_cfg["country"],
                founded_year=self.rng.randint(1888, 1929),
                most_successful_club=top_league_clubs[0].name,
                record_scorer=f"38 Goals — {top_league_clubs[0].legends[0].name} (2014)",
                past_champions=past_champs,
                club_ids=club_ids,
                fixtures=fixtures
            )
            all_leagues[league_id] = league

        world.clubs = all_clubs
        world.players = all_players
        world.leagues = all_leagues

        # 2. Setup Continental Tournament Heritage
        all_club_list = list(all_clubs.values())
        top_euro_clubs = sorted(all_club_list, key=lambda c: c.tournament_titles + c.league_titles, reverse=True)
        past_tourney_winners = []
        for y_back in range(1, 11):
            w = self.rng.choice(top_euro_clubs[:8])
            ru_candidates = [c for c in top_euro_clubs[:8] if c.id != w.id]
            ru = self.rng.choice(ru_candidates)
            past_tourney_winners.append({
                "season_label": f"{2024 - y_back}/{str(2025 - y_back)[-2:]}",
                "winner_name": w.name,
                "winner_club_id": w.id,
                "runner_up_name": ru.name,
                "runner_up_club_id": ru.id,
                "score": f"{self.rng.randint(1, 3)} - {self.rng.randint(0, 1)}"
            })
        world.tournament.past_winners = past_tourney_winners
        world.tournament.most_successful_club = top_euro_clubs[0].name

        # 3. Create User Character in their home country's youth academy (Domestic Start Rule)
        domestic_clubs = [
            c for c in all_clubs.values() 
            if c.country.strip().lower() == user_country.strip().lower()
        ]
        if not domestic_clubs:
            domestic_clubs = list(all_clubs.values())
            
        user_club = self.rng.choice(domestic_clubs)
        
        user_player = self._create_user_player(user_name, user_country, user_position, user_club)
        world.players[user_player.id] = user_player
        world.user_player_id = user_player.id
        
        # Add user to club's roster (replacing one player of same position to stay at 20)
        same_pos_players = [pid for pid in user_club.player_ids if world.players[pid].position == user_position]
        if same_pos_players:
            removed_id = same_pos_players[-1]
            user_club.player_ids.remove(removed_id)
            world.free_agent_ids.append(removed_id)
            world.players[removed_id].contract = None
            
        user_club.player_ids.append(user_player.id)
        
        # 4. Initialize National Teams for International Football
        from src.engine.international_engine import InternationalEngine
        intl_engine = InternationalEngine(self.seed)
        world.national_teams = intl_engine.initialize_national_teams()
        
        return world

    def _generate_club_squad(self, club: Club, players_dict: Dict[str, Player], country: str):
        pos_distribution = (
            [Position.GK] * 2 +
            [Position.DEF] * 6 +
            [Position.MID] * 6 +
            [Position.FWD] * 6
        )
        
        for pos in pos_distribution:
            # 65% domestic player, 35% international star from global pool
            if self.rng.random() < 0.65:
                p_country = country
            else:
                p_country = self.rng.choice(ALL_SUPPORTED_COUNTRIES)
                
            _, _, name = get_random_name_for_country(p_country, self.rng)
            age = self.rng.randint(18, 33)
            
            # Rating generation
            base_rating = self.rng.randint(62, 82)
            if club.budget > 100 and self.rng.random() < 0.25:
                base_rating = self.rng.randint(80, 88)
                
            pot = min(100, max(base_rating, base_rating + self.rng.randint(2, 12))) if age <= 24 else base_rating
            
            p_id = f"ply_{club.id}_{len(club.player_ids) + 1}"
            contract = Contract(
                club_id=club.id,
                club_name=club.name,
                years_remaining=self.rng.randint(2, 4),
                total_years=4
            )
            
            att = max(30, min(100, base_rating + self.rng.randint(-5, 5)))
            play = max(30, min(100, base_rating + self.rng.randint(-5, 5)))
            defe = max(30, min(100, base_rating + self.rng.randint(-5, 5)))
            phys = max(30, min(100, base_rating + self.rng.randint(-5, 5)))
            
            traits = assign_initial_traits(pos, att, play, defe, phys, base_rating, self.rng)
            
            player = Player(
                id=p_id,
                name=name,
                country=p_country,
                age=age,
                position=pos,
                overall_rating=base_rating,
                potential=min(100, pot),
                attacking=att,
                playmaking=play,
                defending=defe,
                physical=phys,
                contract=contract,
                traits=traits
            )
            players_dict[p_id] = player
            club.player_ids.append(p_id)

    def _create_user_player(self, name: str, country: str, position: Position, club: Club) -> Player:
        p_id = f"usr_seed_{self.seed}"
        
        # User starting rating based on club infrastructure (1-5)
        # Starting age is strictly 17, with potential up to 100
        base_pot = 92 + (club.infrastructure_level * 1) + self.rng.randint(2, 6)
        potential = min(100, max(95, base_pot))
        overall = max(55, int(potential * 0.70))
        
        contract = Contract(
            club_id=club.id,
            club_name=club.name,
            years_remaining=3,
            total_years=3
        )
        
        att = overall + (6 if position == Position.FWD else (-6 if position in [Position.DEF, Position.GK] else 0))
        play = overall + (6 if position == Position.MID else 0)
        defe = overall + (8 if position in [Position.DEF, Position.GK] else -8)
        phys = overall + self.rng.randint(-2, 4)
        
        user_traits = assign_initial_traits(position, att, play, defe, phys, overall, self.rng)
        if not user_traits:
            if position == Position.FWD:
                user_traits = ["🎯 Clinical Finisher"]
            elif position == Position.MID:
                user_traits = ["🎩 Midfield Maestro"]
            elif position == Position.DEF:
                user_traits = ["🧱 Defensive Anchor"]
            else:
                user_traits = ["🧤 Acrobatic Wall"]
        
        return Player(
            id=p_id,
            name=name,
            country=country,
            age=17,
            position=position,
            is_user=True,
            overall_rating=overall,
            potential=potential,
            attacking=max(30, min(100, att)),
            playmaking=max(30, min(100, play)),
            defending=max(30, min(100, defe)),
            physical=max(30, min(100, phys)),
            contract=contract,
            traits=user_traits
        )

    def _generate_double_round_robin_fixtures(self, club_ids: List[str]) -> List[List[Dict[str, str]]]:
        """Generates 38 rounds of home & away fixtures for 20 clubs"""
        n = len(club_ids) # 20
        teams = list(club_ids)
        rounds: List[List[Dict[str, str]]] = []
        
        # First half (19 rounds)
        for r in range(n - 1):
            round_matches = []
            for i in range(n // 2):
                h = teams[i]
                a = teams[n - 1 - i]
                if r % 2 == 1:
                    h, a = a, h
                round_matches.append({"home_id": h, "away_id": a})
            rounds.append(round_matches)
            # Rotate
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]
            
        # Second half (reverse home/away)
        for r in range(n - 1):
            round_matches = []
            for m in rounds[r]:
                round_matches.append({"home_id": m["away_id"], "away_id": m["home_id"]})
            rounds.append(round_matches)
            
        return rounds
