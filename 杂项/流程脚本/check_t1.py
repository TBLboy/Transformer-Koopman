import numpy as np

# Physical output is the first lifted coordinate. Input acts only on the
# second coordinate, so not every physical next-state increment is feasible.
A = np.eye(2)
B = np.array([[0.0], [1.0]])
C = np.array([[1.0, 0.0]])
z_ref = np.array([0.0, 0.0])
next_refs = [np.array([0.0, 1.0]), np.array([1.0, 0.0])]
Bdag = np.linalg.pinv(B)
Pi = B @ Bdag

print("B=", B.tolist())
print("range_projection=", Pi.tolist())
for nxt in next_refs:
    d = nxt - A @ z_ref
    defect = (np.eye(2) - Pi) @ d
    print("next_ref=", nxt.tolist(), "d=", d.tolist(), "projection_defect=", defect.tolist(), "norm=", float(np.linalg.norm(defect)))
