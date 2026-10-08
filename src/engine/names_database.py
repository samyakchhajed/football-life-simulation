import random
from typing import Dict, List, Tuple

COUNTRY_NAMES_DB: Dict[str, Dict[str, List[str]]] = {
    "England": {
        "first": ["Oliver", "Harry", "George", "Noah", "Arthur", "Jack", "Charlie", "Thomas", "Henry", "Freddie", "Marcus", "Mason", "Declan", "Jude", "Cole"],
        "last": ["Smith", "Jones", "Williams", "Taylor", "Brown", "Wilson", "Johnson", "Davies", "Walker", "Sterling", "Kane", "Bellingham", "Saka", "Foden", "Palmer"]
    },
    "Spain": {
        "first": ["Alejandro", "Mateo", "Lucas", "Leo", "Daniel", "Hugo", "Manuel", "Pablo", "Alvaro", "Adrian", "Gavi", "Pedri", "Lamine", "Rodri", "Ferran"],
        "last": ["Garcia", "Rodriguez", "Gonzalez", "Fernandez", "Lopez", "Martinez", "Sanchez", "Perez", "Torres", "Ramos", "Navarro", "Yamal", "Ruiz", "Morata", "Olmo"]
    },
    "France": {
        "first": ["Gabriel", "Leo", "Raphael", "Louis", "Lucas", "Jules", "Adam", "Arthur", "Hugo", "Antoine", "Kylian", "Aurelien", "Eduardo", "Theo", "Ousmane"],
        "last": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Moreau", "Mbappe", "Griezmann", "Camavinga", "Tchouameni", "Hernandez", "Dembele"]
    },
    "Germany": {
        "first": ["Noah", "Matteo", "Elias", "Finn", "Leon", "Theo", "Paul", "Emil", "Henry", "Jonas", "Jamal", "Florian", "Kai", "Joshua", "Leroy"],
        "last": ["Muller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Musiala", "Wirtz", "Havertz", "Kimmich", "Sane", "Gundogan", "Kroos"]
    },
    "Italy": {
        "first": ["Leonardo", "Francesco", "Alessandro", "Lorenzo", "Mattia", "Tommaso", "Gabriele", "Andrea", "Riccardo", "Edoardo", "Nicolo", "Federico", "Gianluigi", "Sandro", "Giacomo"],
        "last": ["Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Barella", "Chiesa", "Donnarumma", "Tonali", "Bastoni", "Dimarco", "Raspadori"]
    },
    "Portugal": {
        "first": ["Afonso", "Rodrigo", "Martim", "Santiago", "Duarte", "Tomas", "Lourenco", "Salvador", "Gabriel", "Miguel", "Bruno", "Bernardo", "Ruben", "Rafael", "Diogo"],
        "last": ["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues", "Martins", "Fernandes", "Dias", "Leao", "Jota", "Cancelo", "Neves", "Ramos"]
    },
    "Netherlands": {
        "first": ["Noah", "Sem", "Liam", "Lucas", "Daan", "Finn", "Levi", "Luuk", "Mees", "Bram", "Frenkie", "Virgil", "Cody", "Xavi", "Jeremie"],
        "last": ["De Jong", "Van Dijk", "De Vries", "Van de Berg", "Bakker", "Visser", "Smit", "Gakpo", "Simons", "Frimpong", "Depay", "Ake", "Dumfries", "Koopmeiners", "Timber"]
    },
    "Belgium": {
        "first": ["Arthur", "Noah", "Jules", "Louis", "Lucas", "Liam", "Adam", "Victor", "Mathis", "Finn", "Kevin", "Romelu", "Jeremy", "Amadou", "Leandro"],
        "last": ["Peeters", "Janssens", "Maes", "Jacobs", "Willems", "Mertens", "Claes", "Wouters", "De Bruyne", "Lukaku", "Doku", "Onana", "Trossard", "Tielemans", "Castagne"]
    },
    "Norway": {
        "first": ["Jakob", "Emil", "Filip", "Noah", "Oliver", "Aksel", "William", "Lucas", "Isak", "Kasper", "Erling", "Martin", "Alexander", "Sander", "Antonio"],
        "last": ["Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Nilsen", "Pedersen", "Kristiansen", "Haaland", "Odegaard", "Sorloth", "Berge", "Nusa", "Aasgaard", "Ryerson"]
    },
    "Sweden": {
        "first": ["William", "Liam", "Noah", "Hugo", "Lucas", "Oliver", "Elias", "Adam", "August", "Arvid", "Viktor", "Alexander", "Dejan", "Emil", "Lucas"],
        "last": ["Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Gyokeres", "Isak", "Kulusevski", "Forsberg", "Bergvall", "Lindelof", "Holm"]
    },
    "Croatia": {
        "first": ["Luka", "Ivan", "Marko", "David", "Mateo", "Jakov", "Filip", "Petar", "Josip", "Mihael", "Dominik", "Josko", "Andrej", "Mario", "Borna"],
        "last": ["Horvat", "Kovacevic", "Babic", "Maric", "Juric", "Novak", "Vukovic", "Knez", "Modric", "Kovacic", "Gvardiol", "Livakovic", "Kramaric", "Pasalic", "Sosa"]
    },
    "Denmark": {
        "first": ["William", "Alfred", "Oscar", "Noah", "Karl", "Lucas", "Oliver", "Arthur", "August", "Malthe", "Rasmus", "Christian", "Pierre", "Mikkel", "Joachim"],
        "last": ["Nielsen", "Jensen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen", "Sorensen", "Hojlund", "Eriksen", "Hojbjerg", "Damsgaard", "Andersen", "Kjaer", "Maehle"]
    },
    "Russia": {
        "first": ["Aleksandr", "Mikhail", "Maksim", "Artyom", "Ivan", "Dmitry", "Daniil", "Matvey", "Ilya", "Kirill", "Aleksei", "Fedor", "Anton", "Sergei", "Nikita"],
        "last": ["Ivanov", "Smirnov", "Kuznetsov", "Popov", "Vasiliev", "Petrov", "Sokolov", "Mikhailov", "Golovin", "Miranchuk", "Chalov", "Safonov", "Barinov", "Dzyuba", "Akinfeev"]
    },
    "Brazil": {
        "first": ["Gabriel", "Lucas", "Matheus", "Arthur", "Heitor", "Bernardo", "Davi", "Miguel", "Enzo", "Rafael", "Vinicius", "Rodrygo", "Endrick", "Neymar", "Casemiro"],
        "last": ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Junior", "Goes", "Felipe", "Guimaraes", "Paqueta", "Alisson", "Ederson"]
    },
    "Argentina": {
        "first": ["Mateo", "Bautista", "Juan", "Felipe", "Bruno", "Joaquin", "Thiago", "Santino", "Valentin", "Lautaro", "Lionel", "Julian", "Enzo", "Alexis", "Rodrigo"],
        "last": ["Gonzalez", "Rodriguez", "Gomez", "Fernandez", "Lopez", "Diaz", "Martinez", "Perez", "Messi", "Alvarez", "Romero", "Mac Allister", "De Paul", "Dybala", "Garnacho"]
    },
    "Uruguay": {
        "first": ["Santiago", "Mateo", "Agustin", "Lucas", "Nicolas", "Matias", "Joaquin", "Sebastian", "Rodrigo", "Emiliano", "Federico", "Darwin", "Ronald", "Manuel", "Facundo"],
        "last": ["Rodriguez", "Gonzalez", "Hernandez", "Perez", "Garcia", "Martinez", "Valverde", "Nunez", "Araujo", "Ugarte", "Bentancur", "Pellistri", "Gimenez", "Suarez", "Cavani"]
    },
    "Colombia": {
        "first": ["Samuel", "Santiago", "Matias", "Emiliano", "Maximiliano", "Jeronimo", "Emmanuel", "Martin", "Alejandro", "Juan", "Luis", "James", "Jhon", "Davinson", "Richard"],
        "last": ["Rodriguez", "Gomez", "Gonzalez", "Martinez", "Garcia", "Lopez", "Hernandez", "Sanchez", "Diaz", "Duran", "Arias", "Rios", "Sinisterra", "Lucumi", "Munoz"]
    },
    "India": {
        "first": ["Aarav", "Vihaan", "Vivaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishan", "Shaurya", "Sunil", "Manvir", "Sahal", "Anirudh", "Lallianzuala"],
        "last": ["Sharma", "Patel", "Verma", "Singh", "Kumar", "Rao", "Gupta", "Reddy", "Joshi", "Nair", "Chhetri", "Thapa", "Samad", "Chhangte", "Bose"]
    },
    "Australia": {
        "first": ["Oliver", "Noah", "Jack", "Henry", "William", "Leo", "Charlie", "Lucas", "Thomas", "Hudson", "Riley", "Nestory", "Garang", "Harry", "Jordan"],
        "last": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson", "White", "Martin", "Anderson", "Irankunda", "Kuol", "Souttar", "Bos", "Baccus"]
    },
    "Japan": {
        "first": ["Ren", "Haruto", "Minato", "Yuto", "Riku", "Souta", "Sota", "Yuuto", "Aoi", "Hinata", "Kaoru", "Takefusa", "Wataru", "Daizen", "Ritsu"],
        "last": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato", "Mitoma", "Kubo", "Endo", "Maeda", "Doan"]
    },
    "South Korea": {
        "first": ["Min-jun", "Seo-jun", "Ha-jun", "Do-yun", "Eun-woo", "Si-woo", "Ji-ho", "Ye-jun", "Yu-jun", "Joo-won", "Heung-min", "Kang-in", "Min-jae", "Hee-chan", "Hyun-seok"],
        "last": ["Kim", "Lee", "Park", "Jeong", "Jung", "Choi", "Cho", "Kang", "Yoon", "Jang", "Son", "Hwang", "Hong", "Song", "Oh"]
    },
    "USA": {
        "first": ["Liam", "Noah", "Oliver", "James", "Elijah", "William", "Henry", "Lucas", "Benjamin", "Theodore", "Christian", "Weston", "Folarin", "Tyler", "Timothy"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Pulisic", "McKennie", "Balogun", "Adams", "Weah"]
    }
}

COUNTRY_FEMALE_FIRST_NAMES: Dict[str, List[str]] = {
    "England": ["Sophie", "Olivia", "Amelia", "Emily", "Charlotte", "Ava", "Isla", "Freya", "Ella", "Grace", "Mia", "Ruby", "Chloe", "Alice", "Daisy"],
    "Spain": ["Lucia", "Sofia", "Martina", "Maria", "Paula", "Julia", "Emma", "Valeria", "Daniela", "Alba", "Carmen", "Elena", "Sara", "Clara", "Vega"],
    "France": ["Emma", "Jade", "Louise", "Alice", "Chloe", "Lina", "Lea", "Rose", "Anna", "Mila", "Ines", "Camille", "Juliette", "Manon", "Adele"],
    "Germany": ["Mia", "Emma", "Hannah", "Sophia", "Emilia", "Lina", "Ella", "Clara", "Marie", "Lea", "Leonie", "Leni", "Anna", "Laura", "Luisa"],
    "Italy": ["Sofia", "Giulia", "Aurora", "Ginevra", "Alice", "Emma", "Giorgia", "Beatrice", "Greta", "Vittoria", "Chiara", "Martina", "Elena", "Francesca", "Sara"],
    "Portugal": ["Maria", "Leonor", "Matilde", "Beatriz", "Carolina", "Mariana", "Ana", "Ines", "Margarida", "Sofia", "Francisca", "Lara", "Laura", "Alice", "Clara"],
    "Netherlands": ["Emma", "Julia", "Mila", "Tess", "Sophie", "Zoe", "Sara", "Nora", "Yara", "Liv", "Eva", "Lieke", "Fleur", "Lotte", "Roos"],
    "Belgium": ["Olivia", "Emma", "Mila", "Louise", "Alice", "Lina", "Elena", "Juliette", "Lucie", "Camille", "Sofia", "Anna", "Ella", "Victoria", "Clara"],
    "Norway": ["Nora", "Emma", "Ella", "Olivia", "Sofie", "Maja", "Frida", "Astrid", "Ingrid", "Sara", "Emilie", "Tiril", "Ada", "Signe", "Hedda"],
    "Sweden": ["Alice", "Maja", "Elsa", "Astrid", "Wilma", "Freja", "Olivia", "Alma", "Ella", "Ebba", "Klara", "Stella", "Agnes", "Saga", "Signe"],
    "Croatia": ["Mia", "Lucija", "Sara", "Ana", "Ema", "Petra", "Lana", "Nika", "Marta", "Elena", "Dora", "Iva", "Klara", "Laura", "Tea"],
    "Denmark": ["Alma", "Ida", "Clara", "Ella", "Olivia", "Freja", "Emma", "Sofia", "Karla", "Nora", "Laura", "Mathilde", "Anna", "Sara", "Astrid"],
    "Russia": ["Sofia", "Anna", "Maria", "Victoria", "Alisa", "Polina", "Eva", "Aleksandra", "Anastasia", "Daria", "Ksenia", "Ekaterina", "Elizaveta", "Elena", "Valeria"],
    "Brazil": ["Helena", "Alice", "Laura", "Manuela", "Valentina", "Sophia", "Isabella", "Heloisa", "Luiza", "Julia", "Lorena", "Livia", "Maria", "Giovanna", "Beatriz"],
    "Argentina": ["Emma", "Olivia", "Martina", "Isabella", "Alma", "Catalina", "Mia", "Delfina", "Valentina", "Sofia", "Julieta", "Lucia", "Camila", "Victoria", "Renata"],
    "Uruguay": ["Martina", "Catalina", "Isabella", "Emma", "Valentina", "Sofia", "Julieta", "Lucia", "Camila", "Delfina", "Maria", "Victoria", "Clara", "Paula", "Florencia"],
    "Colombia": ["Luciana", "Isabella", "Salome", "Mariana", "Gabriela", "Valeria", "Samantha", "Valentina", "Antonella", "Camila", "Daniela", "Sara", "Sofia", "Maria", "Laura"],
    "India": ["Ananya", "Diya", "Aadhya", "Priya", "Saanvi", "Isha", "Riya", "Kavya", "Tara", "Tanvi", "Mira", "Pooja", "Shreya", "Aditi", "Meera"],
    "Australia": ["Charlotte", "Isla", "Olivia", "Amelia", "Mia", "Ava", "Grace", "Willow", "Harper", "Chloe", "Ruby", "Ella", "Evie", "Sophie", "Zoe"],
    "Japan": ["Yui", "Hina", "Aoi", "Rin", "Sakura", "Mei", "Mio", "Koharu", "Akari", "Yuna", "Kanna", "Nanami", "Saki", "Riko", "Ema"],
    "South Korea": ["Seo-ah", "Ha-yoon", "Seo-yun", "Ji-woo", "Ha-eun", "Ji-a", "Ah-rin", "Soo-ah", "Chae-won", "Min-seo", "Ji-yoo", "Eun-seo", "Da-eun", "Yu-na", "Ye-eun"],
    "USA": ["Olivia", "Emma", "Charlotte", "Amelia", "Sophia", "Isabella", "Ava", "Mia", "Evelyn", "Harper", "Luna", "Camila", "Gianna", "Elizabeth", "Eleanor"]
}

RELATIONSHIP_BACKSTORIES: List[Dict[str, str]] = [
    {
        "id": "childhood_sweetheart",
        "title": "🏡 Childhood Sweetheart",
        "icon": "🏡",
        "tagline": "Hometown Roots & Academy Days",
        "description": "You grew up together in your hometown before your academy breakthrough, sharing humble beginnings.",
        "meet_narrative": "Met childhood sweetheart {partner} back home, who has stood by your side since your grassroots academy days.",
        "wedding_narrative": "Celebrated a fairytale wedding with childhood sweetheart {partner}, surrounded by hometown friends and youth academy mentors.",
        "child_narrative": "Welcomed {child} with childhood sweetheart {partner}, creating a warm family grounded in your hometown values."
    },
    {
        "id": "college_friend",
        "title": "🎓 University & Studies Friend",
        "icon": "🎓",
        "tagline": "Youth Academy & Campus Studies",
        "description": "Met during your youth days while balancing training with campus studies, sharing ambitions and curiosity.",
        "meet_narrative": "Met partner {partner} during youth studies, bonding over shared intellectual curiosity and ambition away from football.",
        "wedding_narrative": "Celebrated wedding ceremony with {partner}, bringing together university companions and club teammates.",
        "child_narrative": "Welcomed {child} with {partner}, nurturing a curious, loving, and academic family household."
    },
    {
        "id": "charity_gala",
        "title": "✨ Grassroots Charity & Community Gala",
        "icon": "✨",
        "tagline": "Philanthropy & Shared Purpose",
        "description": "Crossed paths at a grassroots youth charity foundation event, connecting over helping local youth.",
        "meet_narrative": "Met partner {partner} at a grassroots youth foundation gala, instantly bonding over community impact and purpose.",
        "wedding_narrative": "Married partner {partner} in an elegant charity gala ceremony, pledging wedding proceeds to grassroots youth foundations.",
        "child_narrative": "Welcomed {child} with {partner}, instilling deep empathy, community spirit, and kindness."
    },
    {
        "id": "neighborhood_cafe",
        "title": "☕ Serendipitous City Encounter",
        "icon": "☕",
        "tagline": "Quiet Sanctuary & Grounded Life",
        "description": "A chance, peaceful meeting at a neighborhood coffee shop away from the noise and media spotlight.",
        "meet_narrative": "Met partner {partner} in a quiet neighborhood café, finding peaceful grounding away from the stadium roar and media glare.",
        "wedding_narrative": "Married partner {partner} in an intimate, private coastal celebration surrounded by closest family.",
        "child_narrative": "Welcomed {child} with {partner}, filling your private sanctuary with laughter and warmth."
    },
    {
        "id": "creative_professional",
        "title": "📸 Creative & Media Professional",
        "icon": "📸",
        "tagline": "Modern Passion & Shared Ambition",
        "description": "Met through an architectural & lifestyle photography shoot, connecting over modern design and travel.",
        "meet_narrative": "Met creative professional {partner} during an editorial shoot, connecting over modern design, travel, and artistic passion.",
        "wedding_narrative": "Celebrated a breathtaking wedding with {partner} at a picturesque destination covered across global lifestyle media.",
        "child_narrative": "Welcomed {child} with {partner}, embarking on a vibrant, creative family chapter."
    }
]

ALL_SUPPORTED_COUNTRIES: List[str] = list(COUNTRY_NAMES_DB.keys())

def get_random_name_for_country(country: str, rng: random.Random) -> Tuple[str, str, str]:
    """Returns (first_name, last_name, full_name) tailored to nationality"""
    pool = COUNTRY_NAMES_DB.get(country, COUNTRY_NAMES_DB["England"])
    first = rng.choice(pool["first"])
    last = rng.choice(pool["last"])
    return first, last, f"{first} {last}"

def get_random_female_name_for_country(country: str, rng: random.Random) -> Tuple[str, str, str]:
    """Returns (first_name, last_name, full_name) tailored to nationality for partner/female names"""
    first_pool = COUNTRY_FEMALE_FIRST_NAMES.get(country, COUNTRY_FEMALE_FIRST_NAMES["England"])
    last_pool = COUNTRY_NAMES_DB.get(country, COUNTRY_NAMES_DB["England"])["last"]
    first = rng.choice(first_pool)
    last = rng.choice(last_pool)
    return first, last, f"{first} {last}"

def get_relationship_backstories() -> List[Dict[str, str]]:
    """Returns the available meeting backstory archetypes"""
    return list(RELATIONSHIP_BACKSTORIES)
