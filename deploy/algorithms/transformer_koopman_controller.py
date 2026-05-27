"""Transformer-Koopman hierarchical LQR controller for Platform 2.

Deployment layout on the upper computer::

    FlexibleArmControl34/algorithms/transformer_koopman_controller.py
    FlexibleArmControl34/algorithms/tk_assets/
    FlexibleArmControl34/algorithms/configs/transformer_koopman_controller.json

The dependency subpackage used to be called ``aabb``. It has been renamed
to ``tk_assets`` for clarity; the imports and runtime path lookup below
match the new name. If you must roll back, search-replace ``tk_assets``
back to ``aabb`` in this file and rename the directory accordingly.
"""
from __future__ import annotations

import os

import numpy as np
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

try:
    import control as ct
except Exception:  # pragma: no cover - optional dependency
    ct = None

from numpy.linalg import solve as np_solve

from core.base_algorithm import BaseAlgorithm
from algorithms.tk_assets.transformer_koopman_lifter import TransformerKoopmanLifter


class TransformerKoopmanController(BaseAlgorithm):
    """Transformer-Koopman + LQR controller wired into the FlexibleArm GUI."""

    def __init__(self, config_path):
        super().__init__(config_path)
        if not self.config:
            self.config = self.default_config()
            self.save_config()

        self.lifter = None
        self.A = None
        self.B = None
        self.B_pinv = None
        self.K = None
        self.load_model_and_design_lqr()

    @staticmethod
    def default_config() -> dict:
        return {
            "Q_x1": 800.0,
            "Q_x2": 700.0,
            "alpha": 0.0,
            "R_control": 1.0,
            "ff_gain": 1.0,
            "u_limit": 100.0,
            "device": "cuda",
            "output_sign_x": -1.0,
            "output_sign_y": 1.0,
        }

    def get_name(self) -> str:
        return "Transformer-Koopman LQR"

    def reset(self):
        if self.lifter is not None:
            self.lifter.reset()
        print("[Transformer-Koopman LQR] state reset")

    def load_model_and_design_lqr(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        asset_dir = os.path.join(base_dir, "tk_assets", "model_assets")
        try:
            self.lifter = TransformerKoopmanLifter(asset_dir, device=self.config.get("device", "cuda"))
            self.A = self.lifter.A
            self.B = self.lifter.B
            self.B_pinv = np.linalg.pinv(self.B)
            print(
                f"[Transformer-Koopman LQR] model loaded A:{self.A.shape} B:{self.B.shape} "
                f"device:{self.lifter.device}"
            )
            self.design_lqr()
        except Exception as exc:
            print(f"[Transformer-Koopman LQR] model load failed: {exc}")
            self.lifter = None
            self.K = None

    def design_lqr(self) -> None:
        if self.A is None or self.B is None or self.lifter is None:
            self.K = None
            return

        d = self.lifter.d
        n = self.lifter.n
        m = self.lifter.m

        q_diag = np.zeros(d, dtype=np.float64)
        q_diag[0] = float(self.config.get("Q_x1", 800.0))
        q_diag[1] = float(self.config.get("Q_x2", 700.0))
        alpha = float(self.config.get("alpha", 0.0))
        if d > n:
            q_diag[n:] = alpha

        Q = np.diag(q_diag)
        R = float(self.config.get("R_control", 1.0)) * np.eye(m)

        try:
            A = self.A.astype(np.float64)
            B = self.B.astype(np.float64)
            if ct is not None:
                self.K, _, _ = ct.dlqr(A, B, Q, R)
                self.K = np.asarray(self.K, dtype=np.float32)
            else:
                # Iterative discrete Riccati fallback
                P = Q.copy()
                for _ in range(2000):
                    P_next = (
                        A.T @ P @ A
                        - A.T @ P @ B @ np_solve(R + B.T @ P @ B, B.T @ P @ A)
                        + Q
                    )
                    if np.max(np.abs(P_next - P)) < 1e-9:
                        P = P_next
                        break
                    P = P_next
                self.K = np_solve(R + B.T @ P @ B, B.T @ P @ A).astype(np.float32)
            eig_radius = max(abs(np.linalg.eigvals(A - B @ self.K)))
            print(
                f"[Transformer-Koopman LQR] LQR ready K:{self.K.shape}, closed-loop rho={eig_radius:.4f}"
            )
        except Exception as exc:
            print(f"[Transformer-Koopman LQR] LQR design failed: {exc}")
            self.K = np.zeros((m, d), dtype=np.float32)

    def calculate_control(self, current_pos, current_step, trajectory_sequence):
        if self.lifter is None or self.K is None or self.B_pinv is None:
            return (0.0, 0.0)

        try:
            z_curr = self.lifter.lift_current(current_pos)
            z_ref = self.lifter.lift_reference(trajectory_sequence, current_step, shift=0)
            z_ref_next = self.lifter.lift_reference(trajectory_sequence, current_step, shift=1)

            e_z = z_curr - z_ref
            u_fb = -self.K @ e_z

            ff_gain = float(self.config.get("ff_gain", 1.0))
            u_ff = self.B_pinv @ (z_ref_next - self.A @ z_ref)
            u_norm = u_fb + ff_gain * u_ff

            u_out = self.lifter.denormalize_control(u_norm)
            u_limit = float(self.config.get("u_limit", 100.0))
            u_out = np.clip(u_out, -u_limit, u_limit)

            sx = float(self.config.get("output_sign_x", -1.0))
            sy = float(self.config.get("output_sign_y", 1.0))
            return (sx * float(u_out[0]), sy * float(u_out[1]))
        except Exception as exc:
            print(f"[Transformer-Koopman LQR] control failed: {exc}")
            return (0.0, 0.0)

    def get_settings_widget(self) -> QWidget:
        return TransformerKoopmanSettingsWidget(self)


class TransformerKoopmanSettingsWidget(QWidget):
    """Qt widget that lets operators tune Q/R/alpha/ff_gain/u_limit at runtime."""

    def __init__(self, algorithm: TransformerKoopmanController):
        super().__init__()
        self.algo = algorithm
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        layout.addRow(QLabel("Platform 2 Transformer-Koopman LQR"))

        self.spin_qx1 = QDoubleSpinBox()
        self.spin_qx1.setRange(0.0, 100000.0)
        self.spin_qx1.setSingleStep(50.0)
        self.spin_qx1.setValue(float(self.algo.config.get("Q_x1", 800.0)))

        self.spin_qx2 = QDoubleSpinBox()
        self.spin_qx2.setRange(0.0, 100000.0)
        self.spin_qx2.setSingleStep(50.0)
        self.spin_qx2.setValue(float(self.algo.config.get("Q_x2", 700.0)))

        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0.0, 0.999)
        self.spin_alpha.setDecimals(4)
        self.spin_alpha.setSingleStep(0.01)
        self.spin_alpha.setValue(float(self.algo.config.get("alpha", 0.0)))

        self.spin_r = QDoubleSpinBox()
        self.spin_r.setRange(0.001, 1000.0)
        self.spin_r.setDecimals(4)
        self.spin_r.setSingleStep(0.1)
        self.spin_r.setValue(float(self.algo.config.get("R_control", 1.0)))

        self.spin_ff = QDoubleSpinBox()
        self.spin_ff.setRange(0.0, 5.0)
        self.spin_ff.setDecimals(3)
        self.spin_ff.setSingleStep(0.1)
        self.spin_ff.setValue(float(self.algo.config.get("ff_gain", 1.0)))

        self.spin_ulimit = QDoubleSpinBox()
        self.spin_ulimit.setRange(0.1, 1000.0)
        self.spin_ulimit.setSingleStep(5.0)
        self.spin_ulimit.setValue(float(self.algo.config.get("u_limit", 100.0)))

        layout.addRow("State weight Q_x1:", self.spin_qx1)
        layout.addRow("State weight Q_x2:", self.spin_qx2)
        layout.addRow("Latent weight alpha:", self.spin_alpha)
        layout.addRow("Control weight R:", self.spin_r)
        layout.addRow("Feedforward gain:", self.spin_ff)
        layout.addRow("Control limit:", self.spin_ulimit)

        btn_save = QPushButton("Save parameters and rebuild LQR")
        btn_save.clicked.connect(self.save_params)
        layout.addRow(btn_save)

    def save_params(self):
        self.algo.config["Q_x1"] = self.spin_qx1.value()
        self.algo.config["Q_x2"] = self.spin_qx2.value()
        self.algo.config["alpha"] = self.spin_alpha.value()
        self.algo.config["R_control"] = self.spin_r.value()
        self.algo.config["ff_gain"] = self.spin_ff.value()
        self.algo.config["u_limit"] = self.spin_ulimit.value()
        self.algo.save_config()
        self.algo.design_lqr()
        QMessageBox.information(self, "Saved", "Parameters saved, LQR redesigned.")
