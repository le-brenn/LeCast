# LeCast is a simple raycasting engine of sorts written in Pygame.
# Copyright (C) 2022 Brennan F.
# If for some reason you want to email me, brenn.or.something@gmail.com

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pygame, sys, os
from numpy import *

# Classes #
class Player(pygame.sprite.Sprite):
    def __init__(self, xy, angle):
        super().__init__()
        self.image = pygame.Surface((16, 16))
        self.x = xy[0]
        self.y = xy[1]
        self.map_x = int(self.x / TILESIZE)
        self.map_y = int(self.y / TILESIZE)
        self.angle = deg2rad(angle)
        self.dx = cos(self.angle)
        self.dy = sin(self.angle)
    
    def rotate(self, rotation_speed):
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.angle -= deg2rad(rotation_speed)
            if self.angle < 0: self.angle += pi*2
        if key[pygame.K_RIGHT]:
            self.angle += deg2rad(rotation_speed)
            if self.angle > pi: self.angle -= pi*2
        self.dx = cos(self.angle)
        self.dy = sin(self.angle)

    def move(self, move_speed):
        key = pygame.key.get_pressed()
        if key[pygame.K_UP]:
            self.x += self.dx * move_speed
            self.y += self.dy * move_speed
        if key[pygame.K_DOWN]:
            self.x -= self.dx * move_speed
            self.y -= self.dy * move_speed


class Map:
    def __init__(self, list, size, wh):
        self.list = list
        self.size = size
        self.w = int(wh[0])
        self.h = int(wh[1])
    
    def draw(self, screen):
        for y in range(self.h):
            for x in range(self.w):
                if self.list[y*self.w+x] == 1:
                    screen.blit(pygame.Surface((self.size, self.size)), pygame.Rect(x*self.size, y*self.size, self.size, self.size))

class Caster:
    def __init__(self, fov, player):
        self.fov = fov
        self.player = player
        
    def cast(self, map, screen):
        self.ray_x, self.ray_y = 0, 0
        self.ray_offset_x, self.ray_offset_y = 0, 0
        self.ray_angle = self.player.angle - deg2rad(self.fov/2)
        if self.ray_angle < 0: self.ray_angle += 2*pi
        if self.ray_angle > 2*pi: self.ray_angle -= 2*pi
        self.depth_of_field = 0
        self.ray_map_x, self.ray_map_y = int(self.ray_x / map.size), int(self.ray_y / map.size)
        self.ray_map_pos = 0
        self.distance = 0

        for ray in range(self.fov * 8):
            # horizontal intersections
            self.depth_of_field = 0
            self.distance_h = 100000
            self.ray_hx, self.ray_hy = self.player.x, self.player.y
            self.atan = -1/tan(self.ray_angle)

            if self.ray_angle > pi: # looking up
                self.ray_y = ((int(self.player.y) >> 6) << 6) - 0.0001
                self.ray_x = (self.player.y - self.ray_y) * self.atan + self.player.x
                self.ray_offset_y = -map.size
                self.ray_offset_x = -self.ray_offset_y*self.atan
            if self.ray_angle < pi: # looking down
                self.ray_y = ((int(self.player.y) >> 6) << 6) + map.size
                self.ray_x = (self.player.y - self.ray_y) * self.atan + self.player.x
                self.ray_offset_y = map.size
                self.ray_offset_x = -self.ray_offset_y * self.atan
            if self.ray_angle == 0 or self.ray_angle == pi: # can't intersect horiz
                self.ray_x = self.player.x
                self.ray_y = self.player.y
                self.depth_of_field = map.w
            
            while self.depth_of_field < map.w:
                self.ray_map_x = int(self.ray_x / map.size)
                self.ray_map_y = int(self.ray_y / map.size)
                self.ray_map_pos = self.ray_map_y * map.w + self.ray_map_x
                if self.ray_map_pos > 0 and self.ray_map_pos < map.w * map.h and map.list[self.ray_map_pos] == 1: # hit wall
                    self.ray_hx = self.ray_x
                    self.ray_hy = self.ray_y
                    self.distance_h = sqrt((self.ray_hx - self.player.x) * (self.ray_hx - self.player.x) + (self.ray_hy - self.player.y) * (self.ray_hy - self.player.y))
                    self.depth_of_field = map.w
                else:
                    self.ray_x += self.ray_offset_x
                    self.ray_y += self.ray_offset_y
                    self.depth_of_field += 1            

        # vertical intersections
            self.depth_of_field = 0
            self.distance_v = 100000
            self.ray_vx, self.ray_vy = self.player.x, self.player.y
            self.ntan = -tan(self.ray_angle)

            if self.ray_angle > PI2 and self.ray_angle < PI3: # looking left
                self.ray_x = ((int(self.player.x) >> 6) << 6) - 0.0001
                self.ray_y = (self.player.x - self.ray_x) * self.ntan + self.player.y
                self.ray_offset_x = -map.size
                self.ray_offset_y = -self.ray_offset_x*self.ntan
            if self.ray_angle < PI2 or self.ray_angle > PI3: # looking right
                self.ray_x = ((int(self.player.x) >> 6) << 6) + map.size
                self.ray_y = (self.player.x - self.ray_x) * self.ntan + self.player.y
                self.ray_offset_x = map.size
                self.ray_offset_y = -self.ray_offset_x * self.ntan
            if self.ray_angle == 0 or self.ray_angle == pi: # can't intersect vert
                self.ray_x = self.player.x
                self.ray_y = self.player.y
                self.depth_of_field = map.w
            
            while self.depth_of_field < map.w:
                self.ray_map_x = int(self.ray_x / map.size)
                self.ray_map_y = int(self.ray_y / map.size)
                self.ray_map_pos = self.ray_map_y * map.w + self.ray_map_x
                if self.ray_map_pos > 0 and self.ray_map_pos < map.w * map.h and map.list[self.ray_map_pos] == 1: # hit wall
                    self.ray_vx = self.ray_x
                    self.ray_vy = self.ray_y
                    self.distance_v = sqrt((self.ray_vx - self.player.x) * (self.ray_vx - self.player.x) + (self.ray_vy - self.player.y) * (self.ray_vy - self.player.y))
                    self.depth_of_field = map.w
                else:
                    self.ray_x += self.ray_offset_x
                    self.ray_y += self.ray_offset_y
                    self.depth_of_field += 1       

            if self.distance_v < self.distance_h:
                self.distance = self.distance_v
                self.ray_x = self.ray_vx
                self.ray_y = self.ray_vy
                self.color = [0, 255, 255]
            elif self.distance_h < self.distance_v:
                self.distance = self.distance_h
                self.ray_x = self.ray_hx
                self.ray_y = self.ray_hy
                self.color = [0, 150, 150]

            self.fixa = self.player.angle - self.ray_angle
            if self.fixa < 0: self.fixa += 2*pi
            if self.fixa > 2*pi: self.fixa -= 2*pi
            self.distance = self.distance * cos(self.fixa)
            self.line_height = (64 * H) / self.distance
            if self.line_height > H:
                self.line_height = H
            self.line_offset = (H / 2) - self.line_height / 2
            pygame.draw.line(screen, self.color, (ray, self.line_offset), (ray, self.line_height + self.line_offset), 1)

            self.ray_angle += DEGREE / 8
            if self.ray_angle < 0: self.ray_angle += 2*pi
            if self.ray_angle > 2*pi: self.ray_angle -= 2*pi

            

def draw_grid(screen):
    for y in range(0, H, TILESIZE):
        for x in range(0, 512, TILESIZE):
            rect = pygame.Rect(x, y, TILESIZE, TILESIZE)
            pygame.draw.rect(screen, GRAY, rect, 1)

# Constants #
PI2 = pi / 2
PI3 = 3 * pi / 2
DEGREE = deg2rad(1)
W = 512
H = 512
TILESIZE = 64
WHITE = (255,255,255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)

# Setup #
pygame.init()
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
pygame.display.set_caption('LeCast 0.1, LeBrenn 2022')
debug_font = pygame.font.SysFont('', 16)
fps = 'swaws'

background = pygame.image.load(os.path.join('background.png'))

test_map = [
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1,
            1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1,
            1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1,
            1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
]

map = Map(test_map, TILESIZE, (20, 20))

player = Player((128, 288), 0)
caster = Caster(64, player)

# Game Loop #
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    player.rotate(8)
    player.move(4)

    fps_counter = debug_font.render(fps, True, BLACK)
    
    screen.fill(WHITE)
    screen.blit(background, background.get_rect(topleft=(0, 0)))
    caster.cast(map, screen)
    screen.blit(fps_counter, fps_counter.get_rect(topleft=(0, 0)))
    pygame.display.flip()
    clock.tick(60)
    fps = f'{int(clock.get_fps())}'
