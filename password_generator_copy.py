"""
Password Generator Module
Generate secure passwords and passphrases.
"""

import secrets
import string
import math


class PasswordGenerator:
    """Generate secure passwords and passphrases."""
    
    # Common word list for passphrases (EFF word list subset)
    WORDLIST = [
        "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
        "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
        "acoustic", "acquire", "across", "action", "actor", "actress", "actual", "adapt",
        "add", "addict", "address", "adjust", "admit", "adult", "advance", "advice",
        "aerobic", "affair", "afford", "afraid", "again", "age", "agent", "agree",
        "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol",
        "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha",
        "already", "also", "alter", "always", "amateur", "amazing", "among", "amount",
        "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle", "announce",
        "annual", "another", "answer", "antenna", "antique", "anxiety", "any", "apart",
        "apology", "appear", "apple", "approve", "april", "arch", "arctic", "area",
        "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange",
        "arrest", "arrive", "arrow", "art", "artist", "artwork", "ask", "aspect",
        "assault", "asset", "assist", "assume", "asthma", "athlete", "atom", "attack",
        "attend", "attitude", "attract", "auction", "audit", "august", "aunt", "author",
        "auto", "autumn", "average", "avocado", "avoid", "awake", "aware", "away",
        "awesome", "awful", "awkward", "axis", "baby", "bachelor", "bacon", "badge",
        "bag", "balance", "balcony", "ball", "bamboo", "banana", "banner", "bar",
        "barely", "bargain", "barrel", "base", "basic", "basket", "battle", "beach",
        "bean", "beauty", "because", "become", "beef", "before", "begin", "behave",
        "behind", "believe", "below", "belt", "bench", "benefit", "best", "betray",
        "better", "between", "beyond", "bicycle", "bid", "bike", "bind", "biology",
        "bird", "birth", "bitter", "black", "blade", "blame", "blanket", "blast",
        "bleak", "bless", "blind", "blood", "blossom", "blouse", "blue", "blur",
        "blush", "board", "boat", "body", "boil", "bomb", "bone", "bonus",
        "book", "boost", "border", "boring", "borrow", "boss", "bottom", "bounce",
        "box", "boy", "bracket", "brain", "brand", "brass", "brave", "bread",
        "breeze", "brick", "bridge", "brief", "bright", "bring", "brisk", "broccoli",
        "broken", "bronze", "broom", "brother", "brown", "brush", "bubble", "buddy",
        "budget", "buffalo", "build", "bulb", "bulk", "bullet", "bundle", "bunker",
        "burden", "burger", "burst", "bus", "business", "busy", "butter", "buyer",
        "buzz", "cabbage", "cabin", "cable", "cactus", "cage", "cake", "call",
        "calm", "camera", "camp", "can", "canal", "cancel", "candy", "cannon",
        "canoe", "canvas", "canyon", "capable", "capital", "captain", "car", "carbon",
        "card", "cargo", "carpet", "carry", "cart", "case", "cash", "casino",
        "castle", "casual", "cat", "catalog", "catch", "category", "cattle", "caught",
        "cause", "caution", "cave", "ceiling", "celery", "cement", "census", "century",
        "cereal", "certain", "chair", "chalk", "champion", "change", "chaos", "chapter",
        "charge", "chase", "chat", "cheap", "check", "cheese", "chef", "cherry",
        "chest", "chicken", "chief", "child", "chimney", "choice", "choose", "chronic",
        "chunk", "circle", "citizen", "city", "civil", "claim", "clap", "clarify",
        "claw", "clay", "clean", "clerk", "clever", "click", "client", "cliff",
        "climb", "clinic", "clip", "clock", "close", "cloth", "cloud", "clown",
        "club", "clump", "cluster", "clutch", "coach", "coast", "coconut", "code",
        "coffee", "coil", "coin", "collect", "color", "column", "combine", "come",
        "comfort", "comic", "common", "company", "concert", "conduct", "confirm", "congress",
        "connect", "consider", "control", "convince", "cook", "cool", "copper", "copy",
        "coral", "core", "corn", "correct", "cost", "cotton", "couch", "country",
        "couple", "course", "cousin", "cover", "coyote", "crack", "cradle", "craft",
        "cram", "crane", "crash", "crater", "crawl", "crazy", "cream", "credit",
        "creek", "crew", "cricket", "crime", "crisp", "critic", "crop", "cross",
        "crouch", "crowd", "crucial", "cruel", "cruise", "crumble", "crunch", "crush",
        "cry", "crystal", "cube", "culture", "cup", "cupboard", "curious", "current",
        "curtain", "curve", "cushion", "custom", "cute", "cycle", "dad", "damage",
        "damp", "dance", "danger", "daring", "dash", "daughter", "dawn", "day",
        "deal", "debate", "debris", "decade", "december", "decide", "decline", "decorate",
        "decrease", "deer", "defense", "define", "defy", "degree", "delay", "deliver",
        "demand", "demise", "denial", "dentist", "deny", "depart", "depend", "deposit",
        "depth", "deputy", "derive", "describe", "desert", "design", "desk", "despair",
        "destroy", "detail", "detect", "develop", "device", "devote", "diagram", "dial",
        "diamond", "diary", "dice", "diesel", "diet", "differ", "digital", "dignity",
        "dilemma", "dinner", "dinosaur", "direct", "dirt", "disagree", "discover", "disease",
        "dish", "dismiss", "disorder", "display", "distance", "divert", "divide", "divorce",
        "dizzy", "doctor", "document", "dog", "doll", "dolphin", "domain", "donate",
        "donkey", "donor", "door", "dose", "double", "dove", "draft", "dragon",
        "drama", "drastic", "draw", "dream", "dress", "drift", "drill", "drink",
        "drip", "drive", "drop", "drum", "dry", "duck", "dumb", "dune",
        "during", "dust", "dutch", "duty", "dwarf", "dynamic", "eager", "eagle",
        "early", "earn", "earth", "easily", "east", "easy", "echo", "ecology",
        "economy", "edge", "edit", "educate", "effort", "egg", "eight", "either",
        "elbow", "elder", "electric", "elegant", "element", "elephant", "elevator", "elite",
        "else", "embark", "embody", "embrace", "emerge", "emotion", "employ", "empower",
        "empty", "enable", "enact", "end", "endless", "endorse", "enemy", "energy",
        "enforce", "engage", "engine", "enhance", "enjoy", "enlist", "enough", "enrich",
        "enroll", "ensure", "enter", "entire", "entry", "envelope", "episode", "equal",
        "equip", "era", "erase", "erode", "erosion", "error", "erupt", "escape",
        "essay", "essence", "estate", "eternal", "ethics", "evidence", "evil", "evoke",
        "evolve", "exact", "example", "excess", "exchange", "excite", "exclude", "excuse",
        "execute", "exercise", "exhaust", "exhibit", "exile", "exist", "exit", "exotic",
        "expand", "expect", "expire", "explain", "expose", "express", "extend", "extra",
        "eye", "fabric", "face", "faculty", "fade", "faint", "faith", "fall",
        "false", "fame", "family", "famous", "fan", "fancy", "fantasy", "farm",
        "fashion", "fat", "fatal", "father", "fatigue", "fault", "favorite", "feature",
        "february", "federal", "fee", "feed", "feel", "female", "fence", "festival",
        "fetch", "fever", "few", "fiber", "fiction", "field", "figure", "file",
        "film", "filter", "final", "find", "fine", "finger", "finish", "fire",
        "firm", "first", "fiscal", "fish", "fit", "fitness", "fix", "flag",
        "flame", "flash", "flat", "flavor", "flee", "flight", "flip", "float",
        "flock", "floor", "flower", "fluid", "flush", "fly", "foam", "focus",
        "fog", "foil", "fold", "follow", "food", "foot", "force", "forest",
        "forget", "fork", "fortune", "forum", "forward", "fossil", "foster", "found",
        "fox", "fragile", "frame", "frequent", "fresh", "friend", "fringe", "frog",
        "front", "frost", "frown", "frozen", "fruit", "fuel", "fun", "funny",
        "furnace", "fury", "future", "gadget", "gain", "galaxy", "gallery", "game",
        "gap", "garage", "garbage", "garden", "garlic", "garment", "gas", "gasp",
        "gate", "gather", "gauge", "gaze", "general", "genius", "genre", "gentle",
        "genuine", "gesture", "ghost", "giant", "gift", "giggle", "ginger", "giraffe",
        "girl", "give", "glad", "glance", "glare", "glass", "glide", "glimpse",
        "globe", "gloom", "glory", "glove", "glow", "glue", "goat", "goddess",
        "gold", "good", "goose", "gorilla", "gospel", "gossip", "govern", "gown",
        "grab", "grace", "grain", "grant", "grape", "grass", "gravity", "great",
        "green", "grid", "grief", "grit", "grocery", "group", "grow", "grunt",
        "guard", "guess", "guide", "guilt", "guitar", "gun", "gym", "habit",
        "hair", "half", "hammer", "hamster", "hand", "happy", "harbor", "hard",
        "harsh", "harvest", "hat", "have", "hawk", "hazard", "head", "health",
        "heart", "heavy", "hedgehog", "height", "hello", "helmet", "help", "hen",
        "hero", "hidden", "high", "hill", "hint", "hip", "hire", "history",
        "hobby", "hockey", "hold", "hole", "holiday", "hollow", "home", "honey",
        "hood", "hope", "horn", "horror", "horse", "hospital", "host", "hotel",
        "hour", "hover", "hub", "huge", "human", "humble", "humor", "hundred"
    ]
    
    def __init__(self):
        self.default_length = 20
        self.default_words = 5
    
    def generate_password(self, length=None, uppercase=True, lowercase=True, 
                         numbers=True, symbols=True, exclude_ambiguous=True):
        """
        Generate a random password.
        
        Args:
            length: Password length (default: 20)
            uppercase: Include uppercase letters
            lowercase: Include lowercase letters
            numbers: Include numbers
            symbols: Include symbols
            exclude_ambiguous: Exclude ambiguous characters (0, O, l, 1, I)
        
        Returns:
            str: Generated password
        """
        length = length or self.default_length
        
        # Build character set
        chars = ""
        if lowercase:
            chars += string.ascii_lowercase
        if uppercase:
            chars += string.ascii_uppercase
        if numbers:
            chars += string.digits
        if symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if exclude_ambiguous:
            ambiguous = "0O1lI"
            chars = ''.join(c for c in chars if c not in ambiguous)
        
        if not chars:
            chars = string.ascii_letters + string.digits
        
        # Generate password
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        return password
    
    def generate_passphrase(self, words=None, separator="-", capitalize=False):
        """
        Generate a passphrase using random words.
        
        Args:
            words: Number of words (default: 5)
            separator: Word separator (default: "-")
            capitalize: Capitalize each word
        
        Returns:
            str: Generated passphrase
        """
        words = words or self.default_words
        
        selected_words = [secrets.choice(self.WORDLIST) for _ in range(words)]
        
        if capitalize:
            selected_words = [word.capitalize() for word in selected_words]
        
        return separator.join(selected_words)
    
    def generate_pin(self, length=6):
        """
        Generate a numeric PIN.
        
        Args:
            length: PIN length (default: 6)
        
        Returns:
            str: Generated PIN
        """
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def calculate_entropy(self, password):
        """
        Calculate password entropy in bits.
        
        Args:
            password: Password to analyze
        
        Returns:
            float: Entropy in bits
        """
        charset_size = 0
        
        if any(c in string.ascii_lowercase for c in password):
            charset_size += 26
        if any(c in string.ascii_uppercase for c in password):
            charset_size += 26
        if any(c in string.digits for c in password):
            charset_size += 10
        if any(c in string.punctuation for c in password):
            charset_size += 32
        
        if charset_size == 0:
            return 0
        
        entropy = len(password) * math.log2(charset_size)
        return round(entropy, 2)
    
    def get_strength(self, password):
        """
        Get password strength rating.
        
        Args:
            password: Password to analyze
        
        Returns:
            dict: Strength analysis
        """
        entropy = self.calculate_entropy(password)
        
        if entropy < 28:
            rating = "very_weak"
            description = "Very Weak - Easy to crack"
        elif entropy < 36:
            rating = "weak"
            description = "Weak - Could be cracked quickly"
        elif entropy < 60:
            rating = "reasonable"
            description = "Reasonable - Moderate protection"
        elif entropy < 128:
            rating = "strong"
            description = "Strong - Good protection"
        else:
            rating = "very_strong"
            description = "Very Strong - Excellent protection"
        
        return {
            "password_length": len(password),
            "entropy_bits": entropy,
            "rating": rating,
            "description": description
        }
    
    def generate_username_password_pair(self, username_length=12, password_length=20):
        """
        Generate a username and password pair.
        
        Args:
            username_length: Length of username
            password_length: Length of password
        
        Returns:
            dict: Username and password pair
        """
        # Username: lowercase + numbers only
        username_chars = string.ascii_lowercase + string.digits
        username = ''.join(secrets.choice(username_chars) for _ in range(username_length))
        
        # Password: full character set
        password = self.generate_password(length=password_length)
        
        return {
            "username": username,
            "password": password,
            "strength": self.get_strength(password)
        }

