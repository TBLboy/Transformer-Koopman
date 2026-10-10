import numpy as np, torch
from pathlib import Path
from scipy.linalg import solve_discrete_are
o=torch.load(Path(r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth"),map_location="cpu",weights_only=False)
A=np.asarray(o["koopman_A"],float); B=np.asarray(o["koopman_B"],float)
n,m=B.shape
print("B.shape",B.shape,"n",n,"m",m,"A.shape",A.shape)
Q=np.diag(np.r_[np.ones(2),np.ones(n-2)*1.0]); R=np.eye(m)
P=solve_discrete_are(A,B,Q,R)
K=np.linalg.solve(R+B.T@P@B,B.T@P@A)
print("K.shape",K.shape,"P.shape",P.shape)
z=np.zeros(n); zr=np.random.default_rng(0).standard_normal((500,n))
print("z",z.shape,"zr",zr.shape,"zr[0]",zr[0].shape)
u=-K@(z-zr[0]); print("u",u.shape,"B@u",(B@u).shape)
