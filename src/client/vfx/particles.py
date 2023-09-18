import pygame as pg
import numpy as np
import math, random

NUM_PARTICLES = 1
LIFETIME = 0.5
MAJOR_AXIS = 10
MINOR_AXIS = 2

def get_circle(radius: float, color: tuple[int, int, int]) -> pg.Surface:
    surf = pg.Surface((2*radius, 2*radius))
    pg.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf


def get_spark(minor_axis: float, major_axis: float, pos: 'np.ndarray[np.float32]', 
              angle: float) -> list['np.ndarray[np.float32]']:
    norm_angle = angle + math.pi/2
    points = [
        pos - major_axis*3/4 * np.array([math.cos(angle), math.sin(angle)]),
        pos - minor_axis/2 * np.array([math.cos(norm_angle), math.sin(norm_angle)]),
        pos + major_axis/4 * np.array([math.cos(angle), math.sin(angle)]),
        pos + minor_axis/2 * np.array([math.cos(norm_angle), math.sin(norm_angle)]),
    ]
    return points


class Sparks:
    def __init__(self, anchor: tuple[int, int], glow: tuple[int, int, int], groups: int=1):
        self.anchor = anchor
        self.particles = []
        self.groups = groups
        self.glow = glow
        self.spawn_rate = 0.025
        self.spawn_time = 0

    def spawn_particles(self):
        for i in range(NUM_PARTICLES * self.groups):
            angle_range = 2 * math.pi
            angle = 3 * math.pi / 2 + random.uniform(0, angle_range) - angle_range / 2
            pos = np.array(self.anchor) + MAJOR_AXIS * np.array([math.cos(angle), math.sin(angle)])
            vel = random.uniform(50, 100) * np.array([math.cos(angle), math.sin(angle)])
            lifetime = LIFETIME * random.uniform(0.5, 1)
            self.particles.append([
                pos, vel, lifetime
            ])
    
    def update(self, dt: float, new_anchor: tuple[int, int], should_spawn: bool=True):
        if should_spawn:
            self.spawn_time += dt
            if self.spawn_time >= self.spawn_rate:
                self.anchor = new_anchor
                self.spawn_particles()
                self.spawn_time = 0
        
        for i in range(len(self.particles)-1, -1, -1):
            # self.particles[i][1] = self.particles[i][1] + np.array([0, 400]) * dt
            self.particles[i][0] = self.particles[i][0] + self.particles[i][1] * dt
            self.particles[i][2] -= dt
            if self.particles[i][2] <= 0:
                self.particles.pop(i)
    
    def render(self, display: pg.Surface):
        for particle in self.particles:
            drawpos = particle[0]
            minor_axis = MINOR_AXIS * particle[2] * 5
            major_axis = MAJOR_AXIS * particle[2] * 7
            angle = math.atan2(particle[1][1], particle[1][0])
            spark_points = get_spark(minor_axis, major_axis, drawpos, angle)
            pg.draw.polygon(display, (255, 255, 255), spark_points)

            glow = get_circle(major_axis, self.glow)
            drawpos = np.array(drawpos) - np.array([major_axis, major_axis])
            display.blit(glow, drawpos, special_flags=pg.BLEND_RGB_ADD)


class Bolt:
    def __init__(self, start: np.ndarray, end: np.ndarray, colour: tuple, t: float):
        self.endpoints = np.array([start, end])
        self.pos = start
        self.vel = (end - start) / t
        self.sparks = Sparks(self.pos, colour, 2)
    
    def update(self, dt: float):
        self.pos = self.pos + self.vel * dt
        if not np.all(np.logical_and(
                np.min(self.endpoints, axis=0) <= self.pos,
                self.pos <= np.max(self.endpoints, axis=0)
            )
        ):
            self.pos = self.endpoints[1]
            self.sparks.update(dt, self.pos, should_spawn=False)
            return True
        self.sparks.update(dt, self.pos)
        return False
    
    def render(self, display: pg.Surface):
        self.sparks.render(display)
