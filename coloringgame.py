import pygame
import sys

# Inicializar Pygame
pygame.init()

# Configuración inicial
TILE_SIZE = 20
ZOOM_INITIAL = 1.0
ZOOM_MIN = 0.3
ZOOM_MAX = 5.0
ZOOM_STEP = 0.1
PALETTE_WIDTH = 140
TOOLBAR_WIDTH = 60
SCROLL_SPEED = 5
BUTTON_SIZE = 40

# Cargar imagen
image = pygame.image.load("imagen.png")
clock = pygame.time.Clock()
GRID_WIDTH, GRID_HEIGHT = image.get_size()

# Configurar pantalla
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
pygame.display.set_caption("Pixel Art Painter")

# Colores
WHITE = (255, 255, 255)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)
BLACK = (0, 0, 0)

# Variables de control
zoom = ZOOM_INITIAL
offset_x, offset_y = 0, 0
dragging = False
last_mouse_pos = (0, 0)
palette_scroll = 0
current_tool = "brush"
drawing = False

# Preparar imagen base y colores
image = pygame.transform.scale(image, (GRID_WIDTH, GRID_HEIGHT))
original_colors = []
color_to_number = {}
number_to_color = []
counter = 1

for y in range(GRID_HEIGHT):
    row = []
    for x in range(GRID_WIDTH):
        color = image.get_at((x, y))[:3]
        row.append(color)
        if color not in color_to_number:
            color_to_number[color] = counter
            number_to_color.append(color)
            counter += 1
    original_colors.append(row)

# Estado del juego
player_colors = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
selected_number = 1
remaining_counts = [0] * len(number_to_color)

# Fuentes
font = pygame.font.SysFont("Arial", 14)
small_font = pygame.font.SysFont("Arial", 12)

# Funciones auxiliares
def calculate_remaining_pixels():
    counts = [0] * len(number_to_color)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if player_colors[y][x] is None:
                original_color = original_colors[y][x]
                color_num = color_to_number[original_color] - 1
                counts[color_num] += 1
    return counts

def screen_to_grid(pos):
    x, y = pos
    grid_x = int((x - offset_x - TOOLBAR_WIDTH) / (TILE_SIZE * zoom))
    grid_y = int((y - offset_y) / (TILE_SIZE * zoom))
    return grid_x, grid_y

def flood_fill(x, y, target_number, replacement_color):
    original_color = original_colors[y][x]
    original_num = color_to_number[original_color]
    
    if original_num != target_number:
        return
    
    queue = [(x, y)]
    visited = set()
    
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            continue
        
        current_original = original_colors[y][x]
        current_painted = player_colors[y][x]
        
        if color_to_number[current_original] == target_number and current_painted != replacement_color:
            player_colors[y][x] = replacement_color
            visited.add((x, y))
            
            queue.append((x + 1, y))
            queue.append((x - 1, y))
            queue.append((x, y + 1))
            queue.append((x, y - 1))

def draw_toolbar():
    pygame.draw.rect(screen, LIGHT_GRAY, (0, 0, TOOLBAR_WIDTH, SCREEN_HEIGHT))
    
    tools = [
        ("🖌️", "brush"),
        ("🪣", "bucket"),
        ("💾", "save")
    ]
    
    for i, (emoji, tool) in enumerate(tools):
        y = 20 + i * (BUTTON_SIZE + 10)
        rect = pygame.Rect(10, y, BUTTON_SIZE, BUTTON_SIZE)
        
        color = DARK_GRAY if current_tool == tool else WHITE
        pygame.draw.rect(screen, color, rect, border_radius=5)
        
        border_color = BLACK if current_tool == tool else DARK_GRAY
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=5)
        
        text = small_font.render(emoji, True, BLACK)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

def draw_palette():
    global remaining_counts
    remaining_counts = calculate_remaining_pixels()
    
    palette_surface = pygame.Surface((PALETTE_WIDTH, SCREEN_HEIGHT))
    palette_surface.fill(WHITE)
    
    visible_items = (SCREEN_HEIGHT - 20) // (BUTTON_SIZE + 5)
    start_index = max(0, min(palette_scroll, len(number_to_color) - visible_items))
    
    for i in range(start_index, min(start_index + visible_items, len(number_to_color))):
        color = number_to_color[i]
        y_pos = 20 + (i - start_index) * (BUTTON_SIZE + 5)
        rect = pygame.Rect(10, y_pos, BUTTON_SIZE, BUTTON_SIZE)
        
        pygame.draw.rect(palette_surface, color, rect, border_radius=3)
        
        if selected_number == i + 1:
            pygame.draw.rect(palette_surface, BLACK, rect, 2, border_radius=3)
        
        count_text = f"{i+1} ({remaining_counts[i]})"
        text = small_font.render(count_text, True, BLACK)
        text_width = text.get_width()
        text_x = rect.right + 5
        text_y = rect.centery - 8
        
        if text_x + text_width > PALETTE_WIDTH - 5:
            text_x = PALETTE_WIDTH - text_width - 5
        
        palette_surface.blit(text, (text_x, text_y))
    
    screen.blit(palette_surface, (SCREEN_WIDTH - PALETTE_WIDTH, 0))
    
    if len(number_to_color) > visible_items:
        scroll_height = (visible_items / len(number_to_color)) * SCREEN_HEIGHT
        scroll_pos = (start_index / len(number_to_color)) * SCREEN_HEIGHT
        pygame.draw.rect(screen, DARK_GRAY, 
                        (SCREEN_WIDTH - 10, scroll_pos, 8, scroll_height), border_radius=4)

def draw_grid():
    screen.fill(WHITE)
    
    start_x = max(0, int((-offset_x - TOOLBAR_WIDTH) // (TILE_SIZE * zoom)))
    start_y = max(0, int(-offset_y // (TILE_SIZE * zoom)))
    end_x = min(GRID_WIDTH, int((SCREEN_WIDTH - offset_x - TOOLBAR_WIDTH) // (TILE_SIZE * zoom)) + 1)
    end_y = min(GRID_HEIGHT, int((SCREEN_HEIGHT - offset_y) // (TILE_SIZE * zoom)) + 1)

    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            rect = pygame.Rect(
                TOOLBAR_WIDTH + offset_x + x * TILE_SIZE * zoom,
                offset_y + y * TILE_SIZE * zoom,
                TILE_SIZE * zoom,
                TILE_SIZE * zoom
            )
            
            color = player_colors[y][x] if player_colors[y][x] else (240, 240, 240)
            pygame.draw.rect(screen, color, rect)
            
            if not player_colors[y][x]:
                num = color_to_number[original_colors[y][x]]
                text = font.render(str(num), True, DARK_GRAY)
                screen.blit(text, (rect.x + 2, rect.y + 2))
            
            pygame.draw.rect(screen, LIGHT_GRAY, rect, 1)

# Bucle principal
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    grid_x, grid_y = screen_to_grid(mouse_pos)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if mouse_pos[0] < TOOLBAR_WIDTH:
                    if 20 <= mouse_pos[1] <= 20 + 3*(BUTTON_SIZE + 10):
                        index = (mouse_pos[1] - 20) // (BUTTON_SIZE + 10)
                        tools = ["brush", "bucket", "save"]
                        if index < len(tools):
                            current_tool = tools[index]
                            if current_tool == "save":
                                surf = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
                                for y in range(GRID_HEIGHT):
                                    for x in range(GRID_WIDTH):
                                        color = player_colors[y][x] if player_colors[y][x] else WHITE
                                        surf.set_at((x, y), color)
                                pygame.image.save(surf, "resultado.png")
                                current_tool = "brush"
                
                elif mouse_pos[0] > SCREEN_WIDTH - PALETTE_WIDTH:
                    rel_y = mouse_pos[1] - 20
                    selected_number = (rel_y // (BUTTON_SIZE + 5)) + 1
                    selected_number = min(max(selected_number, 1), len(number_to_color))
                
                else:
                    drawing = True
                    if current_tool == "bucket" and 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                        original_color = original_colors[grid_y][grid_x]
                        target_number = color_to_number[original_color]
                        replacement_color = number_to_color[selected_number - 1]
                        flood_fill(grid_x, grid_y, target_number, replacement_color)
            
            elif event.button == 3:
                dragging = True
                last_mouse_pos = mouse_pos
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                drawing = False
            elif event.button == 3:
                dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                dx = mouse_pos[0] - last_mouse_pos[0]
                dy = mouse_pos[1] - last_mouse_pos[1]
                offset_x += dx
                offset_y += dy
                last_mouse_pos = mouse_pos
                
            if drawing and current_tool == "brush":
                if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                    target_color = original_colors[grid_y][grid_x]
                    if selected_number == color_to_number[target_color]:
                        player_colors[grid_y][grid_x] = number_to_color[selected_number - 1]

        elif event.type == pygame.MOUSEWHEEL:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                zoom += event.y * ZOOM_STEP
                zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))
            else:
                palette_scroll -= event.y * SCROLL_SPEED
                palette_scroll = max(0, min(palette_scroll, len(number_to_color) - 1))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                zoom = ZOOM_INITIAL
                offset_x, offset_y = 0, 0

    draw_grid()
    draw_toolbar()
    draw_palette()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()