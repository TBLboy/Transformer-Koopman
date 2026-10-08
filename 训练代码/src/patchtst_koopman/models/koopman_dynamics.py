"""Linear Koopman dynamics: ``z_{k+1} = A z_k + B u_k``."""
import torch
import torch.nn as nn


class KoopmanDynamics(nn.Module):
    """Linear Koopman propagator with learnable ``A`` and ``B``.

    ``A`` is initialised near identity to preserve information at step 0,
    ``B`` is initialised small. Optional SVD spectral-radius clipping is
    available via :meth:`ensure_stability`; EDMD trainers typically overwrite
    ``A`` and ``B`` with a closed-form least-squares solution.
    """

    def __init__(self, config):
        super().__init__()
        self.d = config["encoder"]["latent_dim"]
        self.m = config["data"]["control_dim"]
        self.rho_max = config["koopman"]["rho_max"]

        self.A = nn.Parameter(torch.eye(self.d) + torch.randn(self.d, self.d) * 0.01)
        self.B = nn.Parameter(torch.randn(self.d, self.m) * 0.1)

    def forward(self, z_t, u_t):
        return torch.matmul(z_t, self.A.T) + torch.matmul(u_t, self.B.T)

    def ensure_stability(self):
        """Project A onto ``{A | rho(A) <= rho_max}`` via SVD clipping."""
        with torch.no_grad():
            U, S, Vt = torch.linalg.svd(self.A)
            S_clipped = torch.clamp(S, max=self.rho_max)
            self.A.data = U @ torch.diag(S_clipped) @ Vt

    def get_spectral_radius(self):
        with torch.no_grad():
            eigenvalues = torch.linalg.eigvals(self.A)
            return torch.max(torch.abs(eigenvalues)).item()

    def get_eigenvalues(self):
        with torch.no_grad():
            return torch.linalg.eigvals(self.A).cpu().numpy()
