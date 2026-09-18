import math
try:
    import pygame
except ImportError:
    pygame = None

# ==============================================================================
# DESIGN SYSTEM & COLOR TOKENS (Premium Modern Pixel / Tile Puzzle Aesthetic)
# ==============================================================================
BG_DARK = (15, 20, 28)          # #0F141C Deep desaturated charcoal-navy
BG_HEADER = (18, 25, 36)        # #121924 Top bar background
CARD_BG = (23, 32, 45)          # #17202D Slate card body
CARD_BORDER = (40, 56, 76)      # #28384C Crisp card border
CARD_HEADER = (29, 41, 57)      # #1D2939 Elevated card header
CARD_INNER = (20, 28, 40)       # #141C28 Inset card/pill background

TEXT_MAIN = (246, 248, 252)     # #F6F8FC High contrast white-silver
TEXT_MUTED = (150, 165, 185)    # #96A5B9 Secondary silver-blue
TEXT_DIM = (105, 122, 146)      # #697A92 Tertiary faint text
ACCENT_CYAN = (44, 174, 214)    # #2CAED6 Tech Cyan
ACCENT_GREEN = (48, 198, 114)   # #30C672 Success emerald
ACCENT_AMBER = (246, 170, 42)   # #F6AA2A Warm gold
ACCENT_CORAL = (230, 88, 72)    # #E65848 Goal coral-crimson

# Playfield Frame & Floor
BOARD_FRAME = (32, 25, 18)      # #201912 Warm dark wood-stone backing
BOARD_BORDER = (68, 54, 38)     # #443626 Frame outer border
BOARD_HILITE = (98, 78, 56)     # #624E38 Inner frame bevel highlight
FLOOR_LIGHT = (238, 226, 204)   # #EEE2CC Warm light sandstone
FLOOR_DARK = (229, 216, 190)    # #E5D8BE Shaded sandstone
FLOOR_MORTAR = (214, 200, 174)  # #D6C8AE Tile mortar seam

# Masonry Brick Walls
WALL_BASE = (94, 88, 70)        # #5E5846 Olive-stone foundation
WALL_HILITE = (138, 130, 106)   # #8A826A Top/left bevel highlight
WALL_SHADOW = (54, 50, 38)      # #363226 Bottom/right bevel shadow
WALL_MORTAR = (34, 31, 22)      # #221F16 Dark mortar joint

# Stylized Wooden Crates
WOOD_BODY = (218, 126, 42)      # #DA7E2A Honey wood body
WOOD_FRAME = (154, 82, 24)      # #9A5218 Outer plank frame
WOOD_HILITE = (246, 170, 78)    # #F6AA4E Top rim highlight
WOOD_SHADOW = (102, 48, 10)     # #66300A Bottom shadow
WOOD_INSET = (190, 106, 28)     # #BE6A1C Recessed center panel
WOOD_RIVET = (235, 190, 105)    # #EBBE69 Polished brass corner studs

# Goals & Box-on-Goal
GOAL_RING = (228, 88, 74)       # #E4584A Concentric crimson-coral ring
GOAL_INNER = (252, 134, 120)    # #FC8678 Inner ring
GOAL_GOLD = (255, 214, 100)     # #FFD664 Center jewel diamond
BOX_GOAL_BORDER = (255, 218, 76)# #FFDA4C Radiant golden rim
BOX_GOAL_HALO = (255, 204, 48, 75)

# Agents
A1_COLOR = (42, 162, 198)       # #2AA2C6 Teal-Cyan operative
A1_HILITE = (94, 210, 244)      # #5ED2F4
A1_DARK = (20, 92, 114)         # #145C72

A2_COLOR = (228, 86, 60)        # #E4563C Terracotta-Coral operative
A2_HILITE = (250, 136, 114)     # #FA8872
A2_DARK = (140, 44, 24)         # #8C2C18

SOLO_COLOR = (40, 150, 186)     # Solo adventurer jacket


# ==============================================================================
# FONT & TEXT MANAGEMENT
# ==============================================================================
_FONT_CACHE = {}

def get_font(size, bold=False):
    if pygame is None: return None
    key = (size, bold)
    if key not in _FONT_CACHE:
        fonts = ['segoeui', 'sfprodisplay', 'helveticaneue', 'dejavusans', 'arial']
        f = None
        for name in fonts:
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                if f: break
            except Exception:
                continue
        if not f:
            f = pygame.font.Font(None, size)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]

def text(surface, val, pos, size=15, color=TEXT_MAIN, bold=False, align="topleft"):
    if not str(val): return
    if not pygame.font.get_init():
        pygame.font.init()
    f = get_font(size, bold)
    if not f: return
    try:
        img = f.render(str(val), True, color)
    except pygame.error:
        _FONT_CACHE.clear()
        f = get_font(size, bold)
        img = f.render(str(val), True, color)
    r = img.get_rect()
    setattr(r, align, pos)
    surface.blit(img, r)


def rounded(surface, rect, color, radius=10, border=None, border_width=1):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_width > 0:
        pygame.draw.rect(surface, border, rect, border_width, border_radius=radius)


# ==============================================================================
# PROCEDURAL VECTOR ICONS & EMOTE SYSTEM (Celebration & Crying Emotes)
# ==============================================================================
def draw_icon_star(surface, center, size, color):
    cx, cy = center
    d = size
    pts = [
        (cx, cy - d),
        (cx + d * 0.35, cy - d * 0.35),
        (cx + d, cy),
        (cx + d * 0.35, cy + d * 0.35),
        (cx, cy + d),
        (cx - d * 0.35, cy + d * 0.35),
        (cx - d, cy),
        (cx - d * 0.35, cy - d * 0.35)
    ]
    pygame.draw.polygon(surface, color, pts)

def draw_icon_play(surface, rect, color):
    cx, cy = rect.center
    sz = min(rect.width, rect.height) * 0.38
    pts = [
        (cx - sz * 0.6, cy - sz),
        (cx + sz * 0.8, cy),
        (cx - sz * 0.6, cy + sz)
    ]
    pygame.draw.polygon(surface, color, pts)

def draw_icon_pause(surface, rect, color):
    cx, cy = rect.center
    bw = max(2, int(rect.width * 0.12))
    bh = int(rect.height * 0.46)
    gap = max(3, int(rect.width * 0.14))
    pygame.draw.rect(surface, color, (cx - gap - bw, cy - bh // 2, bw, bh), border_radius=1)
    pygame.draw.rect(surface, color, (cx + gap, cy - bh // 2, bw, bh), border_radius=1)

def draw_icon_prev(surface, rect, color):
    cx, cy = rect.center
    sz = min(rect.width, rect.height) * 0.34
    pts = [
        (cx + sz * 0.5, cy - sz),
        (cx - sz * 0.7, cy),
        (cx + sz * 0.5, cy + sz)
    ]
    pygame.draw.polygon(surface, color, pts)

def draw_icon_next(surface, rect, color):
    cx, cy = rect.center
    sz = min(rect.width, rect.height) * 0.34
    pts = [
        (cx - sz * 0.5, cy - sz),
        (cx + sz * 0.7, cy),
        (cx - sz * 0.5, cy + sz)
    ]
    pygame.draw.polygon(surface, color, pts)

def draw_icon_reset(surface, rect, color):
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.28
    pygame.draw.arc(surface, color, (cx - r, cy - r, r * 2, r * 2), 0.5, 5.8, max(2, int(r * 0.3)))
    arrow_pts = [
        (cx + r * 0.8, cy - r * 0.4),
        (cx + r * 1.3, cy - r * 0.8),
        (cx + r * 0.4, cy - r * 0.9)
    ]
    pygame.draw.polygon(surface, color, arrow_pts)

def draw_emote_bubble(surface, pos, emote="celebrate"):
    """
    Renders an expressive speech / reaction bubble above an agent on the board.
    - 'celebrate': Radiant golden crown with sparkling jewels and celebratory stars (Winner).
    - 'cry': Crying face with closed squinting eyes and bright blue teardrops (Loser).
    - 'tie': Friendly handshake / neutral balance badge (Tie match).
    """
    bw, bh = 34, 26
    bx = pos[0] - bw // 2
    by = pos[1] - bh - 6
    bubble_rect = pygame.Rect(bx, by, bw, bh)
    
    # 1. Bubble Drop Shadow
    shadow_s = pygame.Surface((bw + 4, bh + 4), pygame.SRCALPHA)
    pygame.draw.rect(shadow_s, (8, 12, 16, 110), (2, 2, bw, bh), border_radius=8)
    surface.blit(shadow_s, (bx, by))
    
    # 2. Bubble Body & Tail
    if emote == "celebrate":
        bg_col = (255, 252, 235)
        border_col = (245, 175, 42)
    elif emote == "cry":
        bg_col = (236, 246, 255)
        border_col = (68, 142, 226)
    else: # tie
        bg_col = (246, 248, 252)
        border_col = (140, 155, 175)
        
    rounded(surface, bubble_rect, bg_col, radius=7, border=border_col, border_width=1)
    
    # Pointer Tail down to the agent's head
    tail_pts = [
        (pos[0] - 4, by + bh - 1),
        (pos[0] + 4, by + bh - 1),
        (pos[0], by + bh + 4)
    ]
    pygame.draw.polygon(surface, bg_col, tail_pts)
    pygame.draw.line(surface, border_col, tail_pts[0], tail_pts[2], 1)
    pygame.draw.line(surface, border_col, tail_pts[1], tail_pts[2], 1)
    
    # 3. Emote Graphics
    cx, cy = bubble_rect.centerx, bubble_rect.centery
    if emote == "celebrate":
        # Golden Crown (3-point royal crown) + Jewels
        cy_top = cy - 5
        crown_pts = [
            (cx - 8, cy + 4),
            (cx - 8, cy_top),
            (cx - 4, cy),
            (cx, cy_top - 2),
            (cx + 4, cy),
            (cx + 8, cy_top),
            (cx + 8, cy + 4)
        ]
        pygame.draw.polygon(surface, (255, 198, 28), crown_pts)
        pygame.draw.polygon(surface, (186, 124, 12), crown_pts, width=1)
        # Crown jewels
        pygame.draw.circle(surface, (235, 45, 45), (cx, cy_top - 2), 1)
        pygame.draw.circle(surface, (45, 165, 245), (cx - 7, cy_top), 1)
        pygame.draw.circle(surface, (45, 165, 245), (cx + 7, cy_top), 1)
        # Victory sparkles
        draw_icon_star(surface, (cx + 11, cy - 6), 3, (255, 215, 0))
    elif emote == "cry":
        # Crying eyes: squinting closed eyes (> <)
        pygame.draw.line(surface, (40, 60, 95), (cx - 7, cy - 3), (cx - 3, cy - 1), 2)
        pygame.draw.line(surface, (40, 60, 95), (cx - 7, cy + 1), (cx - 3, cy - 1), 2)
        pygame.draw.line(surface, (40, 60, 95), (cx + 3, cy - 1), (cx + 7, cy - 3), 2)
        pygame.draw.line(surface, (40, 60, 95), (cx + 3, cy - 1), (cx + 7, cy + 1), 2)
        # Sad mouth
        pygame.draw.arc(surface, (50, 70, 100), (cx - 4, cy + 2, 8, 6), 0, math.pi, 2)
        # Flowing blue teardrops
        for tx in (cx - 6, cx + 6):
            pygame.draw.circle(surface, (42, 154, 252), (tx, cy + 4), 2)
            pygame.draw.polygon(surface, (42, 154, 252), [(tx - 2, cy + 4), (tx + 2, cy + 4), (tx, cy + 1)])
    else: # tie
        # Neutral face / friendly balance (-_-)
        pygame.draw.line(surface, (65, 75, 90), (cx - 7, cy - 2), (cx - 2, cy - 2), 2)
        pygame.draw.line(surface, (65, 75, 90), (cx + 2, cy - 2), (cx + 7, cy - 2), 2)
        pygame.draw.line(surface, (65, 75, 90), (cx - 4, cy + 3), (cx + 4, cy + 3), 2)


# ==============================================================================
# PROCEDURAL SPRITE & TILE ENGINE (Cached Surfaces for 60 FPS)
# ==============================================================================
_SPRITE_CACHE = {}

def _get_cache_key(name, tile, *args):
    return (name, tile, *args)

def draw_floor_tile(surface, cell, r, c):
    tile = cell.width
    base = FLOOR_LIGHT if (r + c) % 2 == 0 else FLOOR_DARK
    pygame.draw.rect(surface, base, cell)
    
    # 1px subtle top/left inner highlight, bottom/right soft shadow
    pygame.draw.line(surface, (252, 244, 228), (cell.left, cell.top), (cell.right - 1, cell.top), 1)
    pygame.draw.line(surface, (252, 244, 228), (cell.left, cell.top), (cell.left, cell.bottom - 1), 1)
    pygame.draw.line(surface, FLOOR_MORTAR, (cell.left, cell.bottom - 1), (cell.right - 1, cell.bottom - 1), 1)
    pygame.draw.line(surface, FLOOR_MORTAR, (cell.right - 1, cell.top), (cell.right - 1, cell.bottom - 1), 1)
    
    # Tiny subtle stone flecks
    pseudo = (r * 23 + c * 37) % 100
    if pseudo < 35:
        fx = cell.left + 8 + (pseudo * 3) % (max(1, tile - 18))
        fy = cell.top + 8 + (pseudo * 7) % (max(1, tile - 18))
        pygame.draw.line(surface, (200, 186, 158), (fx, fy), (fx + 3, fy), 1)
    if pseudo > 72:
        fx = cell.left + 12 + (pseudo * 5) % (max(1, tile - 24))
        fy = cell.top + 10 + (pseudo * 2) % (max(1, tile - 20))
        pygame.draw.circle(surface, (255, 250, 235), (fx, fy), 1)

def draw_wall_tile(surface, cell):
    tile = cell.width
    key = _get_cache_key('wall', tile)
    if key not in _SPRITE_CACHE:
        s = pygame.Surface((tile, tile), pygame.SRCALPHA)
        pygame.draw.rect(s, WALL_BASE, (0, 0, tile, tile))
        
        # Outer bevel highlight & shadow
        pygame.draw.line(s, WALL_HILITE, (0, 0), (tile - 1, 0), 2)
        pygame.draw.line(s, WALL_HILITE, (0, 0), (0, tile - 1), 2)
        pygame.draw.line(s, WALL_SHADOW, (0, tile - 1), (tile - 1, tile - 1), 2)
        pygame.draw.line(s, WALL_SHADOW, (tile - 1, 0), (tile - 1, tile - 1), 2)
        
        # Masonry Brick Course Lines
        mid_y = tile // 2
        pygame.draw.line(s, WALL_MORTAR, (1, mid_y), (tile - 2, mid_y), 2)
        pygame.draw.line(s, WALL_HILITE, (1, mid_y + 1), (tile - 2, mid_y + 1), 1)
        
        split_top = tile // 2
        pygame.draw.line(s, WALL_MORTAR, (split_top, 1), (split_top, mid_y - 1), 2)
        pygame.draw.line(s, WALL_HILITE, (split_top + 1, 1), (split_top + 1, mid_y - 1), 1)
        
        split_bot1 = tile // 4
        split_bot2 = 3 * tile // 4
        for sx in (split_bot1, split_bot2):
            pygame.draw.line(s, WALL_MORTAR, (sx, mid_y + 1), (sx, tile - 2), 2)
            pygame.draw.line(s, WALL_HILITE, (sx + 1, mid_y + 1), (sx + 1, tile - 2), 1)
            
        pygame.draw.rect(s, (116, 108, 88), (3, 3, split_top - 5, mid_y - 5), 1)
        pygame.draw.rect(s, (116, 108, 88), (split_top + 3, 3, tile - split_top - 5, mid_y - 5), 1)
        _SPRITE_CACHE[key] = s
    surface.blit(_SPRITE_CACHE[key], cell.topleft)

def draw_goal(surface, cell):
    tile = cell.width
    key = _get_cache_key('goal', tile)
    if key not in _SPRITE_CACHE:
        s = pygame.Surface((tile, tile), pygame.SRCALPHA)
        scx, scy = tile // 2, tile // 2
        r_outer = max(11, int(tile * 0.38))
        r_inner = max(6, int(tile * 0.24))
        
        # Soft radial aura ring
        pygame.draw.circle(s, (226, 88, 74, 45), (scx, scy), r_outer + 4)
        # Outer vibrant coral ring
        pygame.draw.circle(s, GOAL_RING, (scx, scy), r_outer, width=max(2, tile // 15))
        # Inner fine coral ring
        pygame.draw.circle(s, GOAL_INNER, (scx, scy), r_inner, width=max(1, tile // 26))
        
        # Center golden jewel diamond
        d_size = max(4, int(tile * 0.12))
        diamond = [
            (scx, scy - d_size),
            (scx + d_size, scy),
            (scx, scy + d_size),
            (scx - d_size, scy)
        ]
        pygame.draw.polygon(s, GOAL_GOLD, diamond)
        pygame.draw.polygon(s, (255, 245, 190), diamond, width=1)
        pygame.draw.circle(s, (255, 255, 255), (scx, scy), max(1, d_size // 3))
        _SPRITE_CACHE[key] = s
    surface.blit(_SPRITE_CACHE[key], cell.topleft)

def draw_box(surface, cell, owner=0, on_goal=False):
    tile = cell.width
    margin = max(4, int(tile * 0.08))
    box_rect = cell.inflate(-margin * 2, -margin * 2)
    w, h = box_rect.size
    
    # 1. Soft drop shadow underneath box
    shadow_offset = max(3, int(tile * 0.06))
    shadow_rect = box_rect.move(shadow_offset, shadow_offset)
    shadow_s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_s, (16, 14, 12, 95), (0, 0, w, h), border_radius=6)
    surface.blit(shadow_s, shadow_rect.topleft)
    
    # 2. Render Box Sprite
    key = _get_cache_key('crate_v3', tile, owner, on_goal)
    if key not in _SPRITE_CACHE:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, WOOD_FRAME, (0, 0, w, h), border_radius=6)
        
        inset = max(3, int(w * 0.13))
        inner_rect = pygame.Rect(inset, inset, w - inset * 2, h - inset * 2)
        pygame.draw.rect(s, WOOD_INSET, inner_rect, border_radius=3)
        
        plank_h = inner_rect.height / 3.0
        for i in range(3):
            pr = pygame.Rect(inner_rect.x, int(inner_rect.y + i * plank_h), inner_rect.width, int(math.ceil(plank_h)))
            pygame.draw.rect(s, WOOD_BODY, pr.inflate(-1, -1), border_radius=2)
            if i < 2:
                sy = int(inner_rect.y + (i + 1) * plank_h)
                pygame.draw.line(s, WOOD_SHADOW, (inner_rect.left, sy), (inner_rect.right - 1, sy), 1)
        
        # Diagonal X Wooden Braces
        x_col = WOOD_FRAME
        x_hi = WOOD_HILITE
        th = max(2, int(w * 0.09))
        pygame.draw.line(s, x_col, (inner_rect.left + 2, inner_rect.top + 2), (inner_rect.right - 2, inner_rect.bottom - 2), th)
        pygame.draw.line(s, x_col, (inner_rect.left + 2, inner_rect.bottom - 2), (inner_rect.right - 2, inner_rect.top + 2), th)
        pygame.draw.line(s, x_hi, (inner_rect.left + 2, inner_rect.top + 1), (inner_rect.right - 2, inner_rect.bottom - 3), 1)
        pygame.draw.line(s, x_hi, (inner_rect.left + 2, inner_rect.bottom - 3), (inner_rect.right - 2, inner_rect.top + 1), 1)
        
        # Outer Frame Bevel
        pygame.draw.line(s, WOOD_HILITE, (2, 1), (w - 3, 1), 2)
        pygame.draw.line(s, WOOD_HILITE, (1, 2), (1, h - 3), 2)
        pygame.draw.line(s, WOOD_SHADOW, (2, h - 2), (w - 2, h - 2), 2)
        pygame.draw.line(s, WOOD_SHADOW, (w - 2, 2), (w - 2, h - 2), 2)
        
        # Brass Corner Rivets
        rv_off = max(2, int(inset * 0.45))
        rv_rad = max(1, int(w * 0.038))
        for rx, ry in [(rv_off, rv_off), (w - rv_off - 1, rv_off), 
                       (rv_off, h - rv_off - 1), (w - rv_off - 1, h - rv_off - 1)]:
            pygame.draw.circle(s, WOOD_RIVET, (rx, ry), rv_rad)
            pygame.draw.circle(s, (255, 240, 170), (rx, ry), max(1, rv_rad // 2))

        # Competitive Ownership Styling
        if owner == 1:
            pygame.draw.rect(s, A1_COLOR, (0, 0, w, h), width=max(2, int(w * 0.075)), border_radius=6)
            pygame.draw.rect(s, (210, 245, 255), (2, 2, w - 4, h - 4), width=1, border_radius=4)
            badge_w, badge_h = max(18, int(w * 0.46)), max(13, int(h * 0.34))
            badge_rect = pygame.Rect(3, 3, badge_w, badge_h)
            rounded(s, badge_rect, A1_DARK, radius=4, border=A1_HILITE, border_width=1)
            bf = get_font(max(10, int(badge_h * 0.72)), bold=True)
            if bf:
                b_img = bf.render("A1", True, (255, 255, 255))
                s.blit(b_img, b_img.get_rect(center=badge_rect.center))
        elif owner == 2:
            pygame.draw.rect(s, A2_COLOR, (0, 0, w, h), width=max(2, int(w * 0.075)), border_radius=6)
            pygame.draw.rect(s, (255, 225, 215), (2, 2, w - 4, h - 4), width=1, border_radius=4)
            badge_w, badge_h = max(18, int(w * 0.46)), max(13, int(h * 0.34))
            badge_rect = pygame.Rect(w - badge_w - 3, 3, badge_w, badge_h)
            rounded(s, badge_rect, A2_DARK, radius=4, border=A2_HILITE, border_width=1)
            bf = get_font(max(10, int(badge_h * 0.72)), bold=True)
            if bf:
                b_img = bf.render("A2", True, (255, 255, 255))
                s.blit(b_img, b_img.get_rect(center=badge_rect.center))

        # Box on Goal: Radiant Golden Trim & Victory Star Emblem
        if on_goal:
            gold_th = max(2, int(w * 0.08))
            pygame.draw.rect(s, BOX_GOAL_BORDER, (0, 0, w, h), width=gold_th, border_radius=6)
            pygame.draw.rect(s, (255, 252, 220), (gold_th, gold_th, w - gold_th * 2, h - gold_th * 2), width=1, border_radius=4)
            
            star_size = max(5, int(w * 0.17))
            cx, cy = w // 2, h // 2
            if owner == 0:
                jewel = [
                    (cx, cy - star_size),
                    (cx + star_size, cy),
                    (cx, cy + star_size),
                    (cx - star_size, cy)
                ]
                pygame.draw.polygon(s, (255, 230, 88), jewel)
                pygame.draw.polygon(s, (150, 86, 24), jewel, width=1)
                pygame.draw.circle(s, (255, 255, 255), (cx, cy), max(1, star_size // 3))
            else:
                star_center = (w - star_size - 4, h - star_size - 4)
                pygame.draw.circle(s, (255, 215, 0), star_center, star_size)
                pygame.draw.circle(s, (255, 255, 255), star_center, max(2, star_size // 2))

        _SPRITE_CACHE[key] = s
    surface.blit(_SPRITE_CACHE[key], box_rect.topleft)

def draw_agent(surface, cell, label="P", color=SOLO_COLOR, direction="South"):
    tile = cell.width
    cx, cy = cell.center
    
    # 1. Soft character drop shadow
    sw, sh = int(tile * 0.54), int(tile * 0.28)
    shadow_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_s, (14, 16, 22, 95), (0, 0, sw, sh))
    surface.blit(shadow_s, (cx - sw // 2, cy + int(tile * 0.20)))
    
    # 2. Character Sprite Cache
    key = _get_cache_key('agent_v3', tile, label, color, direction)
    if key not in _SPRITE_CACHE:
        s = pygame.Surface((tile, tile), pygame.SRCALPHA)
        scx, scy = tile // 2, tile // 2
        
        is_solo = (label == "P")
        is_a1 = (label == "A1" or color == A1_COLOR)
        is_a2 = (label == "A2" or color == A2_COLOR)
        
        if is_solo:
            suit_col = SOLO_COLOR
            suit_hi = (76, 202, 236)
            suit_dark = (18, 88, 112)
            cap_col = (48, 54, 68)     # Explorer charcoal cap
        elif is_a1:
            suit_col = A1_COLOR
            suit_hi = A1_HILITE
            suit_dark = A1_DARK
            cap_col = (26, 42, 62)     # Navy operative cap
        else:
            suit_col = A2_COLOR
            suit_hi = A2_HILITE
            suit_dark = A2_DARK
            cap_col = (56, 28, 24)     # Maroon engineer cap
            
        skin_col = (252, 220, 186)
        boot_col = (34, 26, 22)
        
        head_rad = max(7, int(tile * 0.19))
        char_rad = max(9, int(tile * 0.28))
        
        # Shoes / Boots
        boot_w, boot_h = max(5, int(tile * 0.14)), max(4, int(tile * 0.11))
        by = scy + int(tile * 0.22)
        if direction == "North":
            pygame.draw.ellipse(s, boot_col, (scx - int(tile * 0.16), by - 2, boot_w, boot_h))
            pygame.draw.ellipse(s, boot_col, (scx + int(tile * 0.04), by - 2, boot_w, boot_h))
        elif direction == "East":
            pygame.draw.ellipse(s, boot_col, (scx - 2, by, boot_w + 4, boot_h))
        elif direction == "West":
            pygame.draw.ellipse(s, boot_col, (scx - boot_w - 2, by, boot_w + 4, boot_h))
        else: # South
            pygame.draw.ellipse(s, boot_col, (scx - int(tile * 0.17), by, boot_w, boot_h))
            pygame.draw.ellipse(s, boot_col, (scx + int(tile * 0.04), by, boot_w, boot_h))

        # Torso / Jacket
        body_y = scy + int(tile * 0.02)
        body_w, body_h = int(char_rad * 1.6), int(char_rad * 1.1)
        body_rect = pygame.Rect(scx - body_w // 2, body_y, body_w, body_h)
        rounded(s, body_rect, suit_col, radius=int(body_h * 0.45), border=suit_dark, border_width=1)
        
        if direction == "South":
            pygame.draw.line(s, suit_hi, (scx, body_rect.top + 2), (scx, body_rect.bottom - 2), 2)
            pygame.draw.line(s, (230, 185, 80), (scx - 4, body_rect.bottom - 3), (scx + 4, body_rect.bottom - 3), 2)
        elif direction == "East":
            pygame.draw.line(s, suit_hi, (scx + 3, body_rect.top + 2), (scx + 3, body_rect.bottom - 2), 2)
        elif direction == "West":
            pygame.draw.line(s, suit_hi, (scx - 3, body_rect.top + 2), (scx - 3, body_rect.bottom - 2), 2)

        # Arms / Sleeves
        arm_w, arm_h = max(4, int(tile * 0.12)), max(6, int(tile * 0.17))
        pygame.draw.ellipse(s, suit_col, (body_rect.left - 2, body_rect.top + 1, arm_w, arm_h))
        pygame.draw.ellipse(s, suit_col, (body_rect.right - arm_w + 2, body_rect.top + 1, arm_w, arm_h))

        # Head & Cap
        head_y = scy - int(tile * 0.13)
        pygame.draw.circle(s, skin_col, (scx, head_y), head_rad)
        
        cap_h = int(head_rad * 1.25)
        cap_rect = pygame.Rect(scx - head_rad - 1, head_y - head_rad - 1, (head_rad + 1) * 2, cap_h)
        pygame.draw.ellipse(s, cap_col, cap_rect)
        
        if direction == "North":
            pygame.draw.circle(s, cap_col, (scx, head_y), head_rad)
            # Expedition Backpack with dual leather straps
            bp_w, bp_h = int(body_w * 0.68), int(body_h * 0.72)
            bp_rect = pygame.Rect(scx - bp_w // 2, body_rect.top + 2, bp_w, bp_h)
            rounded(s, bp_rect, (96, 66, 44), radius=3, border=(66, 44, 28), border_width=1)
            pygame.draw.line(s, (140, 100, 70), (bp_rect.left + 3, bp_rect.top + 1), (bp_rect.left + 3, bp_rect.bottom - 1), 2)
            pygame.draw.line(s, (140, 100, 70), (bp_rect.right - 4, bp_rect.top + 1), (bp_rect.right - 4, bp_rect.bottom - 1), 2)
        elif direction == "East":
            pygame.draw.ellipse(s, (22, 26, 36), (scx + 2, head_y - 2, head_rad, 4))
            pygame.draw.circle(s, (32, 32, 38), (scx + head_rad - 3, head_y + 1), 2)
            pygame.draw.circle(s, (255, 255, 255), (scx + head_rad - 3, head_y), 1)
        elif direction == "West":
            pygame.draw.ellipse(s, (22, 26, 36), (scx - head_rad - 2, head_y - 2, head_rad, 4))
            pygame.draw.circle(s, (32, 32, 38), (scx - head_rad + 3, head_y + 1), 2)
            pygame.draw.circle(s, (255, 255, 255), (scx - head_rad + 3, head_y), 1)
        else: # South
            pygame.draw.circle(s, (30, 30, 36), (scx - 4, head_y + 2), 2)
            pygame.draw.circle(s, (30, 30, 36), (scx + 4, head_y + 2), 2)
            pygame.draw.circle(s, (255, 255, 255), (scx - 4, head_y + 1), 1)
            pygame.draw.circle(s, (255, 255, 255), (scx + 4, head_y + 1), 1)

        # Competitive Number Shield (Only for A1 / A2)
        if not is_solo and (is_a1 or is_a2):
            chest_badge_r = pygame.Rect(scx - 7, body_rect.centery - 5, 14, 11)
            rounded(s, chest_badge_r, (255, 255, 255), radius=2, border=suit_dark, border_width=1)
            bf = get_font(10, bold=True)
            if bf:
                badge_lbl = "1" if is_a1 else "2"
                bimg = bf.render(badge_lbl, True, suit_dark)
                s.blit(bimg, bimg.get_rect(center=chest_badge_r.center))

        _SPRITE_CACHE[key] = s
    surface.blit(_SPRITE_CACHE[key], cell.topleft)


# ==============================================================================
# BOARD RENDERING (Hero Playfield)
# ==============================================================================
def draw_board(surface, board, state, rect, box_owners=None, facing_dir=None, emotes=None):
    pad = 28
    avail_w = rect.width - pad
    avail_h = rect.height - pad
    tile = min(avail_w // board.width, avail_h // board.height)
    tile = max(38, min(92, tile))
    
    board_px_w = tile * board.width
    board_px_h = tile * board.height
    ox = rect.x + (rect.width - board_px_w) // 2
    oy = rect.y + (rect.height - board_px_h) // 2
    
    # Board Frame Container (Warm Stone/Wood Backing)
    frame_margin = 18
    frame_rect = pygame.Rect(ox - frame_margin, oy - frame_margin, 
                             board_px_w + frame_margin * 2, board_px_h + frame_margin * 2)
    
    # 1. Soft Outer Shadow for Playfield
    shadow_surf = pygame.Surface((frame_rect.width + 22, frame_rect.height + 22), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (6, 10, 16, 140), (11, 11, frame_rect.width, frame_rect.height), border_radius=18)
    surface.blit(shadow_surf, (frame_rect.x - 11, frame_rect.y - 11))
    
    # 2. Main Frame Box with rounded corners, double border, and corner brass rivets
    rounded(surface, frame_rect, BOARD_FRAME, radius=14, border=BOARD_BORDER, border_width=2)
    pygame.draw.rect(surface, BOARD_HILITE, frame_rect.inflate(-4, -4), 1, border_radius=12)
    
    # Corner brass brackets on frame
    for cx, cy in [(frame_rect.left + 8, frame_rect.top + 8),
                   (frame_rect.right - 8, frame_rect.top + 8),
                   (frame_rect.left + 8, frame_rect.bottom - 8),
                   (frame_rect.right - 8, frame_rect.bottom - 8)]:
        pygame.draw.circle(surface, (180, 145, 80), (cx, cy), 3)
        pygame.draw.circle(surface, (245, 220, 150), (cx, cy), 1)

    # 3. Tiles: Floor and Walls
    for r in range(board.height):
        for c in range(board.width):
            p = (r, c)
            if hasattr(board, 'valid_cells') and board.valid_cells and p not in board.valid_cells:
                continue
            cell = pygame.Rect(ox + c * tile, oy + r * tile, tile, tile)
            if p in board.walls:
                draw_wall_tile(surface, cell)
            else:
                draw_floor_tile(surface, cell, r, c)
                
    # 4. Target Goals
    for p in board.goals:
        cell = pygame.Rect(ox + p[1] * tile, oy + p[0] * tile, tile, tile)
        draw_goal(surface, cell)

    # 5. Boxes / Crates
    if state and hasattr(state, 'boxes'):
        owners = box_owners or (state.owner_map() if hasattr(state, 'owner_map') else {})
        for p in state.boxes:
            cell = pygame.Rect(ox + p[1] * tile, oy + p[0] * tile, tile, tile)
            owner = owners.get(p, 0)
            on_goal = (p in board.goals)
            draw_box(surface, cell, owner=owner, on_goal=on_goal)

    # 6. Agents & Expressive Emote Bubbles
    if state:
        f_dir = facing_dir or "South"
        if hasattr(state, 'player'):
            cell = pygame.Rect(ox + state.player[1] * tile, oy + state.player[0] * tile, tile, tile)
            draw_agent(surface, cell, label="P", color=SOLO_COLOR, direction=f_dir)
            
        if hasattr(state, 'p1'):
            cell1 = pygame.Rect(ox + state.p1[1] * tile, oy + state.p1[0] * tile, tile, tile)
            d1 = f_dir if isinstance(f_dir, str) else f_dir[0]
            draw_agent(surface, cell1, label="A1", color=A1_COLOR, direction=d1)
            # Floating Emote Bubble above A1
            if emotes and state.p1 in emotes:
                draw_emote_bubble(surface, (cell1.centerx, cell1.top - 2), emotes[state.p1])
                
        if hasattr(state, 'p2'):
            cell2 = pygame.Rect(ox + state.p2[1] * tile, oy + state.p2[0] * tile, tile, tile)
            d2 = "South" if isinstance(f_dir, str) else f_dir[1]
            draw_agent(surface, cell2, label="A2", color=A2_COLOR, direction=d2)
            # Floating Emote Bubble above A2
            if emotes and state.p2 in emotes:
                draw_emote_bubble(surface, (cell2.centerx, cell2.top - 2), emotes[state.p2])


# ==============================================================================
# UI COMPONENTS (Header, Cards, Badges, Timeline)
# ==============================================================================
def draw_badge(surface, x, y, label, bg_color, text_color=TEXT_MAIN, icon_type=None, h=28):
    f = get_font(12, bold=True)
    txt_surf = f.render(label, True, text_color)
    tw = txt_surf.get_width()
    icon_w = 18 if icon_type else 0
    w = tw + 24 + icon_w
    badge_rect = pygame.Rect(x, y, w, h)
    rounded(surface, badge_rect, bg_color, radius=h // 2, border=CARD_BORDER, border_width=1)
    
    tx = x + 12
    if icon_type == "star":
        draw_icon_star(surface, (tx + 5, y + h // 2), 5, text_color)
        tx += icon_w
    elif icon_type == "dot":
        pygame.draw.circle(surface, text_color, (tx + 5, y + h // 2), 3)
        tx += icon_w
    elif icon_type == "check":
        pts = [(tx + 2, y + h // 2), (tx + 5, y + h // 2 + 3), (tx + 10, y + h // 2 - 4)]
        pygame.draw.lines(surface, text_color, False, pts, 2)
        tx += icon_w

    surface.blit(txt_surf, (tx, y + (h - txt_surf.get_height()) // 2))
    return w

def draw_pill_metric(surface, x, y, w, h, label, value, val_color=TEXT_MAIN):
    rect = pygame.Rect(x, y, w, h)
    rounded(surface, rect, CARD_INNER, radius=8, border=CARD_BORDER, border_width=1)
    text(surface, label.upper(), (x + 12, y + 8), size=11, color=TEXT_DIM, bold=True)
    text(surface, str(value), (x + 12, y + 26), size=17, color=val_color, bold=True)

def draw_stat_bar(surface, x, y, w, h, label, val, max_val, color=ACCENT_CYAN):
    text(surface, label, (x, y), size=13, color=TEXT_MUTED)
    val_str = str(val)
    f = get_font(13, bold=True)
    v_img = f.render(val_str, True, TEXT_MAIN)
    surface.blit(v_img, (x + w - v_img.get_width(), y))
    
    bar_y = y + 20
    bar_h = 6
    bg_r = pygame.Rect(x, bar_y, w, bar_h)
    rounded(surface, bg_r, (32, 44, 60), radius=3)
    
    fill_ratio = min(1.0, max(0.04, (val / max(1, max_val)) if max_val else 0.5))
    fill_w = int(w * fill_ratio)
    fill_r = pygame.Rect(x, bar_y, fill_w, bar_h)
    rounded(surface, fill_r, color, radius=3)

def draw_keycap(surface, x, y, key, label):
    kf = get_font(11, bold=True)
    k_img = kf.render(key, True, TEXT_MAIN)
    kw = max(26, k_img.get_width() + 12)
    kh = 22
    kr = pygame.Rect(x, y, kw, kh)
    rounded(surface, kr, (36, 48, 66), radius=5, border=(64, 84, 110), border_width=1)
    surface.blit(k_img, k_img.get_rect(center=kr.center))
    
    text(surface, label, (x + kw + 8, y + 4), size=12, color=TEXT_MUTED)
    return kw + 10 + kf.render(label, True, TEXT_MUTED).get_width() + 16

def draw_top_bar(surface, title, subtitle, badges=None):
    width, _ = surface.get_size()
    bar_rect = pygame.Rect(0, 0, width, 64)
    pygame.draw.rect(surface, BG_HEADER, bar_rect)
    pygame.draw.line(surface, CARD_BORDER, (0, 63), (width, 63), 1)
    
    # Title & Subtitle Badge
    text(surface, title, (28, 16), size=21, color=TEXT_MAIN, bold=True)
    
    sub_x = 28 + get_font(21, bold=True).render(title, True, TEXT_MAIN).get_width() + 16
    draw_badge(surface, sub_x, 18, subtitle, (32, 44, 60), TEXT_MUTED, h=26)
    
    if badges:
        cur_x = width - 28
        for b in reversed(badges):
            lbl, bg_col, text_col, icon_type = b
            f = get_font(12, bold=True)
            icon_w = 18 if icon_type else 0
            w = f.render(lbl, True, text_col).get_width() + 24 + icon_w
            cur_x -= w
            draw_badge(surface, cur_x, 18, lbl, bg_col, text_col, icon_type, h=28)
            cur_x -= 10

def draw_bottom_timeline(surface, current_step, max_steps, paused=True, status="PLAYING"):
    width, height = surface.get_size()
    t_rect = pygame.Rect(24, height - 76, width - 48, 60)
    rounded(surface, t_rect, CARD_BG, radius=10, border=CARD_BORDER, border_width=1)
    
    # Step Counter Pill
    step_str = f"STEP {current_step:02d} / {max_steps:02d}"
    text(surface, step_str, (t_rect.x + 20, t_rect.y + 21), size=14, color=ACCENT_CYAN, bold=True)
    
    # Visual Interactive Scrub Bar with Step Ticks
    bar_x = t_rect.x + 160
    bar_w = 420
    bar_y = t_rect.y + 27
    bar_h = 6
    bg_track = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
    rounded(surface, bg_track, (36, 48, 64), radius=3)
    
    if 1 < max_steps <= 35:
        for st in range(max_steps + 1):
            tx = bar_x + int(bar_w * (st / max_steps))
            pygame.draw.circle(surface, (54, 70, 92), (tx, bar_y + 3), 1)

    prog = (current_step / max(1, max_steps)) if max_steps > 0 else 0
    prog = min(1.0, max(0.0, prog))
    prog_w = int(bar_w * prog)
    if prog_w > 0:
        rounded(surface, pygame.Rect(bar_x, bar_y, prog_w, bar_h), ACCENT_CYAN, radius=3)
        
    # Glowing Scrubber Knob with halo
    knob_x = bar_x + prog_w
    knob_y = bar_y + bar_h // 2
    pygame.draw.circle(surface, (44, 174, 214, 90), (knob_x, knob_y), 8)
    pygame.draw.circle(surface, (255, 255, 255), (knob_x, knob_y), 6)
    pygame.draw.circle(surface, ACCENT_CYAN, (knob_x, knob_y), 4)
    
    # Playback Visual Buttons (Vector Icons)
    btn_x = bar_x + bar_w + 32
    by = t_rect.y + 16
    btn_w = 34
    btn_h = 28
    
    r_prev = pygame.Rect(btn_x, by, btn_w, btn_h)
    rounded(surface, r_prev, CARD_HEADER, radius=6, border=CARD_BORDER)
    draw_icon_prev(surface, r_prev, TEXT_MAIN)
    
    r_play = pygame.Rect(btn_x + 40, by, btn_w + 10, btn_h)
    play_col = ACCENT_AMBER if not paused else ACCENT_CYAN
    rounded(surface, r_play, play_col, radius=6)
    if paused:
        draw_icon_play(surface, r_play, BG_DARK)
    else:
        draw_icon_pause(surface, r_play, BG_DARK)
    
    r_next = pygame.Rect(btn_x + 90, by, btn_w, btn_h)
    rounded(surface, r_next, CARD_HEADER, radius=6, border=CARD_BORDER)
    draw_icon_next(surface, r_next, TEXT_MAIN)
    
    r_reset = pygame.Rect(btn_x + 130, by, btn_w, btn_h)
    rounded(surface, r_reset, CARD_HEADER, radius=6, border=CARD_BORDER)
    draw_icon_reset(surface, r_reset, TEXT_MAIN)

    # Keyboard Shortcuts Chips
    kx = btn_x + 184
    kx += draw_keycap(surface, kx, by + 3, "SPACE", "Play/Pause")
    kx += draw_keycap(surface, kx, by + 3, "ARROWS", "Step")
    kx += draw_keycap(surface, kx, by + 3, "R", "Reset")


# ==============================================================================
# MAIN SCENES: SINGLE REPLAY & COMPETITIVE ARENA
# ==============================================================================
def single_scene(surface, board, result, algorithm, index, paused=True, status_override=None):
    width, height = surface.get_size()
    surface.fill(BG_DARK)
    
    is_solved = getattr(result, 'solved', False) if result else False
    max_steps = len(result.actions) if result and result.actions else 0
    is_finished = (index >= max_steps and max_steps > 0)
    
    if status_override is not None:
        status_label = status_override
    elif not is_solved:
        status_label = "UNSOLVABLE"
    elif is_finished:
        status_label = "FINISHED"
    elif paused:
        status_label = "PAUSED" if index > 0 else "READY"
    else:
        status_label = "PLAYING"

    status_color = (
        ACCENT_GREEN if status_label == "FINISHED"
        else (ACCENT_CORAL if status_label == "UNSOLVABLE"
        else (ACCENT_AMBER if status_label == "PAUSED"
        else (ACCENT_CYAN if status_label == "PLAYING"
        else TEXT_MUTED)))
    )
    status_icon = "check" if status_label == "FINISHED" else ("x" if status_label == "UNSOLVABLE" else "dot")
    
    # 1. Top Bar
    badges = [
        (f"MAP: {board.width}x{board.height}", (34, 46, 62), TEXT_MUTED, None),
        (f"ALGO: {algorithm.upper()}", (30, 60, 85), ACCENT_CYAN, None),
        (status_label, (26, 52, 40) if is_finished else (34, 52, 68), status_color, status_icon),
    ]
    draw_top_bar(surface, "SOKOBAN AI", "SEARCH & REPLAY LAB", badges)
    
    # 2. Layout Geometry
    board_rect = pygame.Rect(24, 76, 836, height - 164)
    panel_rect = pygame.Rect(880, 76, 376, height - 164)
    
    facing_dir = "South"
    if index > 0 and result and result.actions and (index - 1) < len(result.actions):
        facing_dir = result.actions[index - 1]

    if result and result.solution_states and index < len(result.solution_states):
        state = result.solution_states[index]
    else:
        from ..state import State
        state = State(board.initial_player, board.initial_boxes)

    draw_board(surface, board, state, board_rect, facing_dir=facing_dir)
    
    # 3. Right Control Panel
    px, py, pw = panel_rect.x, panel_rect.y, panel_rect.width
    
    # Card 1: Search Overview
    c1_h = 150
    c1 = pygame.Rect(px, py, pw, c1_h)
    rounded(surface, c1, CARD_BG, radius=12, border=CARD_BORDER, border_width=1)
    rounded(surface, pygame.Rect(px, py, pw, 34), CARD_HEADER, radius=12)
    pygame.draw.rect(surface, CARD_HEADER, (px, py + 22, pw, 12))
    pygame.draw.line(surface, CARD_BORDER, (px, py + 34), (px + pw, py + 34), 1)
    text(surface, "SEARCH OVERVIEW", (px + 16, py + 9), size=12, color=TEXT_MUTED, bold=True)
    
    pill_w = (pw - 40) // 2
    pill_h = 46
    draw_pill_metric(surface, px + 14, py + 44, pill_w, pill_h, "ALGORITHM", algorithm.upper(), ACCENT_CYAN)
    draw_pill_metric(surface, px + 22 + pill_w, py + 44, pill_w, pill_h, "PLAYBACK", status_label, status_color)
    draw_pill_metric(surface, px + 14, py + 95, pill_w, pill_h, "SOLUTION", "SOLVED" if is_solved else "UNSOLVABLE", ACCENT_GREEN if is_solved else ACCENT_CORAL)
    draw_pill_metric(surface, px + 22 + pill_w, py + 95, pill_w, pill_h, "STEP", f"{index} / {max_steps}", TEXT_MAIN)
    
    # Card 2: Performance Telemetry
    c2_y = py + c1_h + 14
    c2_h = 226
    c2 = pygame.Rect(px, c2_y, pw, c2_h)
    rounded(surface, c2, CARD_BG, radius=12, border=CARD_BORDER, border_width=1)
    rounded(surface, pygame.Rect(px, c2_y, pw, 34), CARD_HEADER, radius=12)
    pygame.draw.rect(surface, CARD_HEADER, (px, c2_y + 22, pw, 12))
    pygame.draw.line(surface, CARD_BORDER, (px, c2_y + 34), (px + pw, c2_y + 34), 1)
    text(surface, "PERFORMANCE TELEMETRY", (px + 16, c2_y + 9), size=12, color=TEXT_MUTED, bold=True)
    
    exp_nodes = result.expanded_nodes if result else 0
    gen_nodes = result.generated_nodes if result else 0
    max_front = result.max_frontier_size if result else 0
    elapsed_ms = result.elapsed_ms if result else 0.0

    max_exp_scale = max(200, exp_nodes * 2)
    draw_stat_bar(surface, px + 16, c2_y + 46, pw - 32, 6, "Expanded Nodes", exp_nodes, max_exp_scale, ACCENT_CYAN)
    
    max_gen_scale = max(400, gen_nodes * 2)
    draw_stat_bar(surface, px + 16, c2_y + 88, pw - 32, 6, "Generated Nodes", gen_nodes, max_gen_scale, (92, 164, 230))
    
    max_front_scale = max(100, max_front * 2)
    draw_stat_bar(surface, px + 16, c2_y + 130, pw - 32, 6, "Max Frontier Size", max_front, max_front_scale, ACCENT_AMBER)
    
    pygame.draw.line(surface, CARD_BORDER, (px + 16, c2_y + 176), (px + pw - 16, c2_y + 176), 1)
    text(surface, "Execution Runtime", (px + 16, c2_y + 190), size=13, color=TEXT_MUTED)
    f_rt = f"{elapsed_ms:.3f} ms"
    draw_badge(surface, px + pw - 124, c2_y + 184, f_rt, (36, 52, 70), ACCENT_GREEN, h=24)
    
    # Card 3: Interactive Controls Reference
    c3_y = c2_y + c2_h + 14
    c3_h = panel_rect.bottom - c3_y
    c3 = pygame.Rect(px, c3_y, pw, c3_h)
    rounded(surface, c3, CARD_BG, radius=12, border=CARD_BORDER, border_width=1)
    rounded(surface, pygame.Rect(px, c3_y, pw, 32), CARD_HEADER, radius=12)
    pygame.draw.rect(surface, CARD_HEADER, (px, c3_y + 20, pw, 12))
    pygame.draw.line(surface, CARD_BORDER, (px, c3_y + 32), (px + pw, c3_y + 32), 1)
    text(surface, "CONTROLS GUIDE", (px + 16, c3_y + 8), size=12, color=TEXT_DIM, bold=True)
    
    ky = c3_y + 42
    draw_keycap(surface, px + 18, ky, "SPACE", "Toggle auto replay playback")
    draw_keycap(surface, px + 18, ky + 28, "ARROWS", "Step backward / forward")
    draw_keycap(surface, px + 18, ky + 56, "R", "Reset puzzle to start")
    draw_keycap(surface, px + 18, ky + 84, "ESC", "Exit application")

    # 4. Bottom Replay Timeline
    draw_bottom_timeline(surface, index, max_steps, paused=paused, status=status_label)



def competitive_scene(surface, board, state, step_limit, agent_names=('A*', 'GBFS')):
    width, height = surface.get_size()
    surface.fill(BG_DARK)
    
    # Compute scores and match standing
    s1, s2 = state.scores(board.goals)
    is_finished = (state.step >= step_limit)
    
    # Determine Emotes:
    # Winner gets celebration (crown + sparkles), Loser gets crying face with tears, Tie gets neutral/handshake
    if s1 > s2:
        emote1, emote2 = "celebrate", "cry"
        leader_str = "AGENT 1 WINS!" if is_finished else "AGENT 1 LEADS"
        leader_col = A1_COLOR
    elif s2 > s1:
        emote1, emote2 = "cry", "celebrate"
        leader_str = "AGENT 2 WINS!" if is_finished else "AGENT 2 LEADS"
        leader_col = A2_COLOR
    else:
        emote1, emote2 = "tie", "tie"
        leader_str = "TIE MATCH"
        leader_col = ACCENT_AMBER
        
    status_str = "MATCH OVER" if is_finished else "ROUND ACTIVE"
    status_col = ACCENT_GREEN if is_finished else ACCENT_CYAN
    
    # 1. Top Bar
    badges = [
        (f"MAP: {board.width}x{board.height}", (34, 46, 62), TEXT_MUTED, None),
        (f"{agent_names[0]} vs {agent_names[1]}", (38, 54, 72), TEXT_MAIN, None),
        (leader_str, (32, 48, 64), leader_col, "star"),
        (status_str, (26, 52, 40) if is_finished else (34, 52, 68), status_col, "dot"),
    ]
    draw_top_bar(surface, "SOKOBAN DUEL", "COMPETITIVE MULTI-AGENT ARENA", badges)
    
    # 2. Layout Geometry
    board_rect = pygame.Rect(24, 76, 836, height - 164)
    panel_rect = pygame.Rect(880, 76, 376, height - 164)
    
    # Pass Emotes for A1 and A2 to draw above their heads!
    emotes_map = {}
    if hasattr(state, 'p1'): emotes_map[state.p1] = emote1
    if hasattr(state, 'p2'): emotes_map[state.p2] = emote2
    
    # Draw Playfield with Floating Emotes
    draw_board(surface, board, state, board_rect, box_owners=state.owner_map(), emotes=emotes_map)
    
    # 3. Right Control Panel
    px, py, pw = panel_rect.x, panel_rect.y, panel_rect.width
    
    # Card 1: Duel Scorecard with Reaction Emote Badges
    c1_h = 176
    c1 = pygame.Rect(px, py, pw, c1_h)
    rounded(surface, c1, CARD_BG, radius=12, border=CARD_BORDER, border_width=1)
    rounded(surface, pygame.Rect(px, py, pw, 34), CARD_HEADER, radius=12)
    pygame.draw.rect(surface, CARD_HEADER, (px, py + 22, pw, 12))
    pygame.draw.line(surface, CARD_BORDER, (px, py + 34), (px + pw, py + 34), 1)
    text(surface, "MATCH SCOREBOARD", (px + 16, py + 9), size=12, color=TEXT_MUTED, bold=True)
    
    # Dual Agent Score Boxes with VS Divider
    sw = (pw - 52) // 2
    sh = 82
    
    # Agent 1 Score Box
    r_a1 = pygame.Rect(px + 14, py + 42, sw, sh)
    a1_bg = (22, 44, 60) if emote1 != "celebrate" else (22, 54, 72)
    rounded(surface, r_a1, a1_bg, radius=8, border=A1_COLOR, border_width=2)
    text(surface, "AGENT 1", (r_a1.x + 10, r_a1.y + 7), size=11, color=A1_HILITE, bold=True)
    text(surface, agent_names[0], (r_a1.x + 10, r_a1.y + 21), size=12, color=TEXT_MUTED)
    text(surface, str(s1), (r_a1.right - 26, r_a1.y + 24), size=24, color=TEXT_MAIN, bold=True, align="center")
    text(surface, "completed", (r_a1.x + 10, r_a1.y + 40), size=10, color=TEXT_DIM)
    
    # Reaction Badge Pill inside Agent 1 box
    a1_emote_rect = pygame.Rect(r_a1.x + 8, r_a1.y + 58, sw - 16, 18)
    if emote1 == "celebrate":
        rounded(surface, a1_emote_rect, (36, 68, 48), radius=9, border=ACCENT_GREEN, border_width=1)
        draw_icon_star(surface, (a1_emote_rect.left + 16, a1_emote_rect.centery), 4, (255, 215, 60))
        text(surface, "WINNER" if is_finished else "WINNING", (a1_emote_rect.centerx + 8, a1_emote_rect.centery), size=10, color=(255, 230, 100), bold=True, align="center")
    elif emote1 == "cry":
        rounded(surface, a1_emote_rect, (32, 44, 66), radius=9, border=(80, 140, 210), border_width=1)
        td_cx, td_cy = a1_emote_rect.left + 16, a1_emote_rect.centery
        pygame.draw.circle(surface, (70, 160, 255), (td_cx, td_cy + 1), 2)
        pygame.draw.polygon(surface, (70, 160, 255), [(td_cx - 2, td_cy + 1), (td_cx + 2, td_cy + 1), (td_cx, td_cy - 3)])
        text(surface, "DEFEAT" if is_finished else "LOSING", (a1_emote_rect.centerx + 8, a1_emote_rect.centery), size=10, color=(160, 205, 255), bold=True, align="center")
    else:
        rounded(surface, a1_emote_rect, (44, 48, 58), radius=9, border=CARD_BORDER, border_width=1)
        text(surface, "TIED MATCH", a1_emote_rect.center, size=10, color=TEXT_MUTED, bold=True, align="center")
    
    # VS Center Badge
    vs_rect = pygame.Rect(px + 14 + sw + 3, py + 72, 20, 20)
    rounded(surface, vs_rect, CARD_HEADER, radius=10, border=CARD_BORDER)
    text(surface, "VS", vs_rect.center, size=9, color=TEXT_MUTED, bold=True, align="center")
    
    # Agent 2 Score Box
    r_a2 = pygame.Rect(px + 28 + sw + 10, py + 42, sw, sh)
    a2_bg = (54, 32, 28) if emote2 != "celebrate" else (68, 38, 32)
    rounded(surface, r_a2, a2_bg, radius=8, border=A2_COLOR, border_width=2)
    text(surface, "AGENT 2", (r_a2.x + 10, r_a2.y + 7), size=11, color=A2_HILITE, bold=True)
    text(surface, agent_names[1], (r_a2.x + 10, r_a2.y + 21), size=12, color=TEXT_MUTED)
    text(surface, str(s2), (r_a2.right - 26, r_a2.y + 24), size=24, color=TEXT_MAIN, bold=True, align="center")
    text(surface, "completed", (r_a2.x + 10, r_a2.y + 40), size=10, color=TEXT_DIM)
    
    # Reaction Badge Pill inside Agent 2 box
    a2_emote_rect = pygame.Rect(r_a2.x + 8, r_a2.y + 58, sw - 16, 18)
    if emote2 == "celebrate":
        rounded(surface, a2_emote_rect, (36, 68, 48), radius=9, border=ACCENT_GREEN, border_width=1)
        draw_icon_star(surface, (a2_emote_rect.left + 16, a2_emote_rect.centery), 4, (255, 215, 60))
        text(surface, "WINNER" if is_finished else "WINNING", (a2_emote_rect.centerx + 8, a2_emote_rect.centery), size=10, color=(255, 230, 100), bold=True, align="center")
    elif emote2 == "cry":
        rounded(surface, a2_emote_rect, (32, 44, 66), radius=9, border=(80, 140, 210), border_width=1)
        td_cx, td_cy = a2_emote_rect.left + 16, a2_emote_rect.centery
        pygame.draw.circle(surface, (70, 160, 255), (td_cx, td_cy + 1), 2)
        pygame.draw.polygon(surface, (70, 160, 255), [(td_cx - 2, td_cy + 1), (td_cx + 2, td_cy + 1), (td_cx, td_cy - 3)])
        text(surface, "DEFEAT" if is_finished else "LOSING", (a2_emote_rect.centerx + 8, a2_emote_rect.centery), size=10, color=(160, 205, 255), bold=True, align="center")
    else:
        rounded(surface, a2_emote_rect, (44, 48, 58), radius=9, border=CARD_BORDER, border_width=1)
        text(surface, "TIED MATCH", a2_emote_rect.center, size=10, color=TEXT_MUTED, bold=True, align="center")

    # Leader Banner inside Card 1
    b_lead = pygame.Rect(px + 14, py + 132, pw - 28, 32)
    rounded(surface, b_lead, CARD_HEADER, radius=6)
    text(surface, "MATCH STANDING:", (b_lead.x + 12, b_lead.centery), size=11, color=TEXT_MUTED, bold=True, align="midleft")
    text(surface, leader_str, (b_lead.right - 12, b_lead.centery), size=12, color=leader_col, bold=True, align="midright")

    # Card 2: Match Progress & Rules
    c2_y = py + c1_h + 14
    c2_h = 138
    c2 = pygame.Rect(px, c2_y, pw, c2_h)
    rounded(surface, c2, CARD_BG, radius=12, border=CARD_BORDER, border_width=1)
    rounded(surface, pygame.Rect(px, c2_y, pw, 34), CARD_HEADER, radius=12)
    pygame.draw.rect(surface, CARD_HEADER, (px, c2_y + 22, pw, 12))
    pygame.draw.line(surface, CARD_BORDER, (px, c2_y + 34), (px + pw, c2_y + 34), 1)
    text(surface, "ROUND PROGRESS", (px + 16, c2_y + 9), size=12, color=TEXT_MUTED, bold=True)
    
    draw_stat_bar(surface, px + 16, c2_y + 46, pw - 32, 6, "Turn Limit", state.step, step_limit, ACCENT_CYAN)
    
    text(surface, "Decision Model", (px + 16, c2_y + 88), size=12, color=TEXT_MUTED)
    text(surface, "Simultaneous with Pre-Resolution", (px + 16, c2_y + 106), size=12, color=TEXT_MAIN, bold=True)

    # Card 3: Box Ownership Legend
    c3_y = c2_y + c2_h + 14
    c3_h = panel_rect.bottom - c3_y
    c3 = pygame.Rect(px, c3_y, pw, c3_h)
    rounded(surface, c3, CARD_BG, radius=12, border=CARD_BORDER, border_width=1)
    rounded(surface, pygame.Rect(px, c3_y, pw, 32), CARD_HEADER, radius=12)
    pygame.draw.rect(surface, CARD_HEADER, (px, c3_y + 20, pw, 12))
    pygame.draw.line(surface, CARD_BORDER, (px, c3_y + 32), (px + pw, c3_y + 32), 1)
    text(surface, "OWNERSHIP VISUAL IDENTITY", (px + 16, c3_y + 8), size=12, color=TEXT_DIM, bold=True)
    
    leg_items = [
        ("A1 Owned Box", A1_COLOR, "A1", "Cyan Double Rim + Shield"),
        ("A2 Owned Box", A2_COLOR, "A2", "Coral Dotted Rim + Shield"),
        ("Neutral Wooden Crate", WOOD_BODY, "B", "Unclaimed wooden crate"),
    ]
    ly = c3_y + 42
    for title, col, badge_lbl, desc in leg_items:
        mini_rect = pygame.Rect(px + 16, ly, 30, 30)
        rounded(surface, mini_rect, WOOD_BODY, radius=4, border=col, border_width=2)
        if badge_lbl != "B":
            b_r = pygame.Rect(mini_rect.x + 2, mini_rect.y + 2, 14, 10)
            rounded(surface, b_r, col, radius=2)
        text(surface, title, (px + 56, ly + 2), size=13, color=TEXT_MAIN, bold=True)
        text(surface, desc, (px + 56, ly + 16), size=11, color=TEXT_MUTED)
        ly += 38

    # 4. Bottom Timeline
    draw_bottom_timeline(surface, state.step, step_limit, paused=True, status=status_str)


# ==============================================================================
# LEGACY COMPATIBILITY HELPERS
# ==============================================================================
def header(surface, title, subtitle):
    draw_top_bar(surface, title, subtitle)

def pill(surface, label, value, x, y, color):
    draw_pill_metric(surface, x, y, 150, 52, label, value, color)
