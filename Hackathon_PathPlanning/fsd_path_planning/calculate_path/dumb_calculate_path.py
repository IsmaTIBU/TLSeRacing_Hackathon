#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Dumb replacement for CalculatePath.
Ignores cones and always returns a straight line in vehicle heading.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np


@dataclass
class PathCalculationInput:
    """Minimal input data structure."""
    left_cones: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))
    right_cones: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))
    left_to_right_matches: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=int))
    right_to_left_matches: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=int))
    position_global: np.ndarray = field(default_factory=lambda: np.zeros(2))
    direction_global: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0]))
    global_path: Optional[np.ndarray] = None


class PathParameterizer:
    """Dummy class kept for compatibility (not used)."""
    def parameterize(self, points: np.ndarray) -> np.ndarray:
        # returns Nx4 with theta, x, y, curvature=0
        diffs = np.linalg.norm(np.diff(points, axis=0), axis=1)
        dists = np.concatenate(([0.0], diffs)).cumsum()
        theta = dists
        curvature = np.zeros(len(points))
        return np.column_stack((theta, points[:, 0], points[:, 1], curvature))


class DumbCalculatePath:
    """
    Dumb path calculator that always generates a straight line.
    API matches the original one so full_pipeline can import it unchanged.
    """

    def __init__(
        self,
        smoothing: float = 0.0,
        predict_every: float = 0.1,
        maximal_distance_for_valid_path: float = 5.0,
        max_deg: int = 1,
        mpc_path_length: float = 20.0,
        mpc_prediction_horizon: int = 40,
    ):
        self.scalars = type(
            "S",
            (),
            {
                "mpc_path_length": mpc_path_length,
                "mpc_prediction_horizon": mpc_prediction_horizon,
                "maximal_distance_for_valid_path": maximal_distance_for_valid_path,
            },
        )()
        self.input = PathCalculationInput()
        self.previous_paths = []
        self.mpc_paths = []
        self.parameterizer = PathParameterizer()

    def set_new_input(self, new_input: PathCalculationInput) -> None:
        self.input = new_input

    def _straight_path_points(self) -> np.ndarray:
        pos = np.asarray(self.input.position_global).reshape(2)
        dir_vec = np.asarray(self.input.direction_global, dtype=float).reshape(2)
        n = np.linalg.norm(dir_vec)
        if n == 0:
            dir_vec = np.array([1.0, 0.0])
        else:
            dir_vec /= n

        N = int(max(2, getattr(self.scalars, "mpc_prediction_horizon", 40)))
        length = float(getattr(self.scalars, "mpc_path_length", 20.0))

        distances = np.linspace(0, length, N, endpoint=False)[:, None]
        return pos + dir_vec[None, :] * distances

    def run_path_calculation(self) -> Tuple[np.ndarray, np.ndarray]:
        pts = self._straight_path_points()
        param = self.parameterizer.parameterize(pts)

        self.previous_paths = (self.previous_paths[-9:] if self.previous_paths else []) + [param]
        self.mpc_paths = (self.mpc_paths[-9:] if self.mpc_paths else []) + [param]

        return param, pts


