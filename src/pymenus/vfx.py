import numpy as np
import pygame as pg


class _Settings:
    LIFETIME = 1 / 2
    SPEED = 100
    KITE = 8 / LIFETIME * np.array([4,1,2,1]).reshape(-1,1)


class Sparks:
    def __init__(self):
        self.lifetime = np.zeros(0)
        self.pos = np.zeros(0)
        self.angle = np.zeros(0)
        self.color = np.zeros(0)
    
    def add_new_particles(self, pos: np.ndarray, angle: np.ndarray, color: np.ndarray):
        lifetime = np.full_like(angle, _Settings.LIFETIME)
        if self.lifetime.size == 0:
            self.lifetime = lifetime
            self.pos = pos
            self.angle = angle
            self.color = color
        else:
            # append
            self.lifetime = np.hstack([self.lifetime, lifetime])
            self.pos = np.vstack([self.pos, pos])
            self.angle = np.hstack([self.angle, angle])
            self.color = np.vstack([self.color, color])
    
    def update(self, dt: float):
        if self.lifetime.size == 0:
            return

        # move sparks
        self.pos = self.pos + _Settings.SPEED * dt * np.column_stack([
            np.cos(self.angle),
            np.sin(self.angle)
        ])

        # destroy sparks
        self.lifetime = self.lifetime - dt
        alive = self.lifetime > 0
        self.lifetime = self.lifetime[alive]
        self.pos = self.pos[alive]
        self.angle = self.angle[alive]
        self.color = self.color[alive]
    
    def render(self, display: pg.Surface):
        for lifetime, pos, angle, color in zip(self.lifetime, self.pos, self.angle, self.color):
            # kite shape
            polygon = pos + np.array([
                [np.cos(angle), np.sin(angle)],
                [np.cos(angle + np.pi/2), np.sin(angle + np.pi/2)],
                [np.cos(angle + np.pi), np.sin(angle + np.pi)],
                [np.cos(angle - np.pi/2), np.sin(angle - np.pi/2)],
            ]) * lifetime * _Settings.KITE
            pg.draw.polygon(display, color.astype(float), polygon)
