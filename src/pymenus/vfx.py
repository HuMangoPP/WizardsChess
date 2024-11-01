import numpy as np
import pygame as pg


class _Settings:
    LIFETIME = 1/2
    SPEED = 100


class Sparks:
    def __init__(self):
        self.lifetime = np.zeros(0)
        self.pos = np.zeros(0)
        self.angle = np.zeros(0)
    
    def add_new_particles(self, pos: np.ndarray, angle: np.ndarray):
        lifetime = np.full_like(angle, _Settings.LIFETIME)
        if self.lifetime.size == 0:
            self.lifetime = lifetime
            self.pos = pos
            self.angle = angle
        else:
            # append
            self.lifetime = np.hstack([self.lifetime, lifetime])
            self.pos = np.vstack([self.pos, pos])
            self.angle = np.hstack([self.angle, angle])
    
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
    
    def render(self, display: pg.Surface):
        for lifetime, pos, angle in zip(self.lifetime, self.pos, self.angle):
            # kite shape
            polygon = pos + np.array([
                [np.cos(angle), np.sin(angle)],
                [np.cos(angle + np.pi/2), np.sin(angle + np.pi/2)],
                [np.cos(angle + np.pi), np.sin(angle + np.pi)],
                [np.cos(angle - np.pi/2), np.sin(angle - np.pi/2)],
            ]) * np.array([20,5,5,5]).reshape(-1,1)
            pg.draw.polygon(display, (255,255,255), polygon)
