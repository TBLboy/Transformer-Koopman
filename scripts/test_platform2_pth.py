"""
测试 平台2.pth (code_project 旧模型) 在 code-projectv2 框架上的精度。
读取模型自带的 config 构建网络，加载当前 test.npz 数据，输出 RMSE/MAE + 预测图。

用法:
    python scripts/test_platform2_pth.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 添加项目根目录
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.utils.config_loader import load_config


CHECKPOINT_PATH = str(PROJECT_DIR / "results" / "platform2" / "Models" / "patchtst_koopman" / "平台2.pth")
SAVE_DIR = str(PROJECT_DIR / "results" / "platform2" / "Models" / "patchtst_koopman" / "test_output")


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print("=" * 60)
    print("  测试平台2.pth 模型精度")
    print("=" * 60)
    print(f"  设备: {device}")
    print(f"  模型: {CHECKPOINT_PATH}")
    print(f"  保存: {SAVE_DIR}")
    print()

    # 1. 加载 checkpoint
    ckpt = torch.load(CHECKPOINT_PATH, map_location='cpu', weights_only=False)
    cfg = ckpt['config']
    print("=== 模型配置 ===")
    print(f"  latent_dim={cfg['encoder']['latent_dim']}, n_layers={cfg['encoder']['n_layers']}, "
          f"P={cfg['encoder']['history_length']}, p={cfg['encoder']['patch_length']}")
    print(f"  precision={cfg['experiment']['precision']}")

    # 2. 准备精度
    precision = cfg['experiment'].get('precision', 'float32')
    dtype = torch.float64 if precision == 'float64' else torch.float32
    torch.set_default_dtype(dtype)

    # 3. 更新数据路径（确保指向当前项目 data）
    cfg['data']['data_dir'] = str(PROJECT_DIR / cfg['data']['data_dir'])

    # 4. 加载测试集（使用 checkpoint 自带的归一化参数，保持 numpy 格式）
    norm_stats = ckpt.get('normalization')

    test_dataset = KoopmanDataset(cfg['data']['data_dir'], cfg, 'test', norm_stats=norm_stats)
    print(f"\n  测试集样本: {len(test_dataset)}")

    # 5. 构建模型 & 加载权重
    model = PatchTSTKoopmanModel(cfg)
    model = model.double() if precision == 'float64' else model.float()
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 6. 测试预测
    print("\n=== 轨迹预测 ===")
    P = cfg['encoder']['history_length']
    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    target_id = unique_traj_ids[0]
    mask = test_dataset.trajectory_id == target_id
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    T = len(x_traj)
    print(f"  轨迹 {target_id}: {T} 个时刻, 预测 {T-P} 步")

    x_history = torch.tensor(x_traj[:P], dtype=dtype).to(device)
    u_seq = torch.tensor(u_traj[P-1:-1], dtype=dtype).to(device)
    x_true_norm = x_traj[P:]

    preds = []
    with torch.no_grad():
        for h in range(len(u_seq)):
            z_t = model.encoder(x_history.unsqueeze(0))
            z_next = model.koopman(z_t, u_seq[h:h+1])
            x_next = model.decoder(z_next)
            preds.append(x_next.squeeze(0).cpu().numpy())
            x_history = torch.cat([x_history[1:], x_next], dim=0)

    x_pred_norm = np.array(preds)

    # 反归一化
    if norm_stats and norm_stats.get('x_mean') is not None:
        xm = norm_stats['x_mean']
        xs = norm_stats['x_std']
        x_pred = x_pred_norm * xs + xm
        x_true = x_true_norm * xs + xm
    else:
        x_pred = x_pred_norm
        x_true = x_true_norm

    # 计算指标
    rmse = float(np.sqrt(np.mean((x_pred - x_true) ** 2)))
    mae = float(np.mean(np.abs(x_pred - x_true)))
    per_dim_rmse = [float(np.sqrt(np.mean((x_pred[:, d] - x_true[:, d]) ** 2))) for d in range(x_true.shape[1])]

    print(f"\n  Overall RMSE: {rmse:.6f}")
    print(f"  Overall MAE:  {mae:.6f}")
    for d, r in enumerate(per_dim_rmse):
        print(f"  Dim {d} RMSE: {r:.6f}")

    # 7. 绘制预测对比图
    print("\n=== 生成预测图 ===")
    n = x_true.shape[1]
    fig, axes = plt.subplots(n, 1, figsize=(12, 3 * n), sharex=True)
    if n == 1:
        axes = [axes]
    t = t_traj[P:]

    for i in range(n):
        ax = axes[i]
        ax.plot(t, x_true[:, i], 'b-', label='True', linewidth=1.5, alpha=0.8)
        ax.plot(t, x_pred[:, i], 'r--', label='Predicted', linewidth=1.5, alpha=0.8)
        ax.fill_between(t, x_true[:, i], x_pred[:, i],
                        color='red', alpha=0.15, label='Error')
        ax.set_ylabel(f'$x_{{{i+1}}}$')
        ax.set_title(f'Dim {i+1}  RMSE={per_dim_rmse[i]:.6f}')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel('Time (s)')
    fig.suptitle(f'Platform2 - 平台2.pth 预测 (Overall RMSE={rmse:.6f})', fontsize=14)
    plt.tight_layout()

    png_path = os.path.join(SAVE_DIR, 'test_prediction.png')
    pdf_path = os.path.join(SAVE_DIR, 'test_prediction.pdf')
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  预测图已保存: {png_path}")
    print(f"                  {pdf_path}")

    # 8. 保存指标
    results = {
        'rmse': rmse,
        'mae': mae,
        'per_dim_rmse': per_dim_rmse,
        'params': sum(p.numel() for p in model.parameters()),
        'config': {
            'latent_dim': cfg['encoder']['latent_dim'],
            'n_layers': cfg['encoder']['n_layers'],
            'history_length': cfg['encoder']['history_length'],
            'patch_length': cfg['encoder']['patch_length'],
            'precision': precision,
        },
    }
    import json
    res_path = os.path.join(SAVE_DIR, 'test_results.json')
    with open(res_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"  指标已保存: {res_path}")
    print("\n完成!")


if __name__ == '__main__':
    main()
