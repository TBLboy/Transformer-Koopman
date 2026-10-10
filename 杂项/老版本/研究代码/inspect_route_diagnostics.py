import torch, numpy as np
p=r"D:\Project\Transformer-Koopman\Transformer-Koopman\训练代码\deploy\algorithms\tk_assets\model_assets\platform2_full_model.pth"
o=torch.load(p,map_location='cpu',weights_only=False)
for k,v in o.items(): print(k,type(v), getattr(v,'shape',None))
A=o['koopman_A']; B=o['koopman_B']
if hasattr(A,'detach'): A=A.detach().numpy()
if hasattr(B,'detach'): B=B.detach().numpy()
print('A shape',A.shape,'B shape',B.shape)
n=A.shape[0]; C=np.concatenate([np.linalg.matrix_power(A,i)@B for i in range(n)],axis=1)
print('rho',max(abs(np.linalg.eigvals(A))))
print('norms',np.linalg.norm(A,2),np.linalg.norm(B,2))
print('B rank',np.linalg.matrix_rank(B),'ctr rank',np.linalg.matrix_rank(C,tol=1e-8),'shape',C.shape)
print('ctr sv',np.linalg.svd(C,compute_uv=False))
print('eig',np.linalg.eigvals(A))
