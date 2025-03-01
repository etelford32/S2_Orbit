import pygame
import math
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1024, 768
BACKGROUND = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

# Physical constants
G = 6.67430e-11  # Gravitational constant
c = 3e8          # Speed of light
M_SagA = 4.154e6 * 1.989e30  # Sagittarius A* mass
J = 0.616 * G * (M_SagA**2) / c  # Angular momentum
AU = 1.496e11    # Astronomical Unit

class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
    
    def world_to_screen(self, x, y):
        screen_x = WIDTH//2 + (x/AU - self.offset_x) * self.zoom
        screen_y = HEIGHT//2 + (y/AU - self.offset_y) * self.zoom
        return int(screen_x), int(screen_y)

class BlackHole:
    def __init__(self):
        self.mass = M_SagA
        self.rs = 2 * G * self.mass / (c**2)  # Schwarzschild radius
        self.position = (0, 0)
        self.a = J / (self.mass * c)  # Spin parameter
        
    def draw(self, screen, camera):
        x, y = camera.world_to_screen(*self.position)
        radius = max(5, int(20 * camera.zoom))
        
        # Draw event horizon
        pygame.draw.circle(screen, WHITE, (x, y), radius, 1)
        
        # Draw ergosphere
        ergo_radius = int(radius * 2)
        pygame.draw.circle(screen, (50, 50, 50), (x, y), ergo_radius, 1)

class S2Star:
    def __init__(self):
        self.semi_major = 120 * AU
        self.eccentricity = 0.884
        self.period = 16.0 * 365.25 * 24 * 3600  # 16 years in seconds
        self.current_time = 0
        self.position = (self.semi_major, 0)
        self.velocity = 0.0
        self.orbit_points = []
        
        # Calculate orbital parameters
        self.semi_minor = self.semi_major * math.sqrt(1 - self.eccentricity**2)
        self.focal_dist = math.sqrt(self.semi_major**2 - self.semi_minor**2)
        
    def solve_kepler(self, M, max_iter=100):
        """Solve Kepler's equation for eccentric anomaly"""
        E = M  # Initial guess
        for _ in range(max_iter):
            E_next = E - (E - self.eccentricity * math.sin(E) - M) / (1 - self.eccentricity * math.cos(E))
            if abs(E_next - E) < 1e-8:
                return E_next
            E = E_next
        return E
        
    def update(self, dt):
        # Update time and calculate mean anomaly
        self.current_time += dt
        M = 2 * math.pi * (self.current_time % self.period) / self.period
        
        # Solve Kepler's equation
        E = self.solve_kepler(M)
        
        # Calculate true anomaly
        nu = 2 * math.atan(math.sqrt((1 + self.eccentricity)/(1 - self.eccentricity)) * math.tan(E/2))
        
        # Calculate radius
        r = self.semi_major * (1 - self.eccentricity**2) / (1 + self.eccentricity * math.cos(nu))
        
        # Calculate position
        x = r * math.cos(nu)
        y = r * math.sin(nu)
        self.position = (x, y)
        
        # Calculate velocity (scalar)
        self.velocity = math.sqrt(G * M_SagA * (2/r - 1/self.semi_major))
        
        # Store orbit points
        self.orbit_points.append((x, y))
        if len(self.orbit_points) > 500:
            self.orbit_points.pop(0)
    
    def draw(self, screen, camera):
        # Draw orbit path
        if len(self.orbit_points) > 1:
            points = [camera.world_to_screen(x, y) for x, y in self.orbit_points]
            pygame.draw.lines(screen, (100, 100, 100), False, points, 1)
        
        # Draw star
        x, y = camera.world_to_screen(*self.position)
        pygame.draw.circle(screen, YELLOW, (x, y), 5)

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Sagittarius A* - S2 Orbit Simulation")
    clock = pygame.time.Clock()
    
    black_hole = BlackHole()
    s2 = S2Star()
    camera = Camera()
    camera.zoom = 1.0  # Initial zoom for better visibility
    
    running = True
    paused = False
    time_scale = 640000.0  # Start with 1 day/frame
    min_scale = 3600.0    # Minimum 1 hour/frame
    max_scale = 31536000.0  # Maximum 1 year/frame
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    camera.zoom *= 1.1
                elif event.key == pygame.K_DOWN:
                    camera.zoom /= 1.1
                elif event.key == pygame.K_LEFT:
                    time_scale = max(time_scale / 2, min_scale)
                elif event.key == pygame.K_RIGHT:
                    time_scale = min(time_scale * 2, max_scale)
        
        if not paused:
            s2.update(time_scale)
        
        screen.fill(BACKGROUND)
        black_hole.draw(screen, camera)
        s2.draw(screen, camera)
        
        # Draw info
        font = pygame.font.SysFont(None, 24)
        time_unit = "years" if time_scale >= 31536000 else "days" if time_scale >= 86400 else "hours"
        time_value = time_scale / (31536000 if time_unit == "years" else 86400 if time_unit == "days" else 3600)
        
        info = [
            f"Time Scale: {time_value:.1f} {time_unit}/frame",
            f"S2 Velocity: {s2.velocity/1000:,.0f} km/s",
            f"Zoom: {camera.zoom:.1f}x",
            f"{'PAUSED' if paused else 'RUNNING'}"
        ]
        
        for i, line in enumerate(info):
            text = font.render(line, True, WHITE)
            screen.blit(text, (10, 10 + i * 25))
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
