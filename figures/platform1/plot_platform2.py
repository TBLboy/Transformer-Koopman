"""
实验1 - 平台2轨迹预测对比绘图 (IEEE风格)
软体机械臂: 2个状态 (x1, x2)
生成一张图: 状态对比图
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import torch
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.ticker import FormatStrFormatter
from pathlib import Path

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.utils.config_loader import load_config

# ============================================================================
# Path configuration — edit these to point at your own checkpoints.
# Defaults assume you run the script from the project root.
# ============================================================================
CONFIG_PATH = 'configs/platform2.yaml'
MLP_MODEL_PATH = 'results/mlp_koopman/platform2/model.pth'
TRANSFORMER_MODEL_PATH = 'results/models/ablation_platform2/<run_id>/full_model/full_model_model.pth'
EDMD_MODEL_PATH = 'results/traditional_edmd/platform2'
SAVE_DIR = 'figures/platform1/output'
# ============================================================================

# ============================================================================
# 绘图参数配置（可手动调节）
# ============================================================================
PLOT_CONFIG = {
    # --------------------------------------------------------------------------
    # 图片尺寸
    # --------------------------------------------------------------------------
    'figure_width': 7.0,              # 图片宽度 (英寸), IEEE双栏标准约7.0
    'figure_height': 5.0,             # 图片高度 (英寸), 2个子图建议5.0
    'dpi': 300,                       # 输出分辨率

    # --------------------------------------------------------------------------
    # 全局缩放
    # --------------------------------------------------------------------------
    'global_font_scale': 1.8,         # 全局字体缩放因子 (建议1.5-2.0)
    'global_linewidth_scale': 1.6,    # 全局线宽缩放因子 (建议1.0-2.0)

    # --------------------------------------------------------------------------
    # 字体设置
    # --------------------------------------------------------------------------
    'font_family': 'Times New Roman', # 字体, IEEE推荐Times New Roman
    'font_size_label': 11,            # 坐标轴标签字体大小
    'font_size_tick': 10,             # 刻度字体大小
    'font_size_legend': 9,            # 图例字体大小
    'ylabel_horizontal_pad': 10,      # Y轴标签水平距离 (点)

    # --------------------------------------------------------------------------
    # 线条设置
    # --------------------------------------------------------------------------
    'linewidth_truth': 1.3,           # 真实值线宽
    'linewidth_prediction': 1.3,      # 预测值线宽

    # --------------------------------------------------------------------------
    # 颜色设置 (十六进制颜色码)
    # --------------------------------------------------------------------------
    'color_truth': '#D62728',         # 红色 - Ground Truth
    'color_transformer': '#000000',   # 黑色 - Proposed Method
    'color_mlp': '#FF7F0E',           # 橙色 - MLP-Koopman
    'color_edmd': '#2CA02C',          # 绿色 - EDMD-Koopman

    # --------------------------------------------------------------------------
    # 线型设置
    # --------------------------------------------------------------------------
    'linestyle_truth': '-',           # 实线 - Ground Truth
    'linestyle_transformer': '-',     # 实线 - Proposed Method
    'linestyle_mlp': '--',            # 虚线 - MLP-Koopman
    'linestyle_edmd': '-.',           # 点划线 - EDMD-Koopman

    # --------------------------------------------------------------------------
    # 透明度设置 (0-1)
    # --------------------------------------------------------------------------
    'alpha_truth': 1.0,               # Ground Truth透明度 (不透明)
    'alpha_prediction': 0.85,         # 预测曲线透明度

    # --------------------------------------------------------------------------
    # 网格设置
    # --------------------------------------------------------------------------
    'grid_alpha': 1,                  # 网格透明度 (0-1)
    'grid_linestyle': '-',            # 网格线型
    'grid_linewidth': 0.8,            # 网格线宽
    'grid_color': '#CCCCCC',          # 网格颜色 (浅灰色)

     # --------------------------------------------------------------------------
    # 图例参数（重点调节区域）
    # --------------------------------------------------------------------------
    'legend_ncol': 4,                 # 图例列数 (4个方法用4列)
    'legend_framealpha': 0.95,        # 图例背景透明度 (0-1)
    'legend_frameon': False,          # 是否显示图例边框
    'legend_loc': 'upper left',       # 图例锚点位置 (upper left/center/right)
    'legend_bbox_x': -0.18,             # 图例水平位置 (0=最左, 0.5=中间, 1=最右)
    'legend_bbox_y': 1.25,            # 图例垂直位置 (1=子图顶部, >1在子图上方)
    'legend_handlelength': 0.5,       # 图例中线段的长度 (建议0.5-2.0)
    'legend_columnspacing': 0.5,      # 图例列之间的间距 (建议0.5-2.0)
    'legend_handletextpad': 0.5,      # 线段与文字之间的间距 (建议0.3-1.0)
    'legend_borderpad': 0.4,          # 图例边框内边距 (建议0.3-1.0)

    # --------------------------------------------------------------------------
    # 子图布局
    # --------------------------------------------------------------------------
    'subplot_hspace': 0.25,           # 子图垂直间距 (建议0.15-0.35)
    'subplot_top': 0.88,              # 子图区域上边界 (0-1, 需为图例留空间)
    'subplot_bottom': 0.08,           # 子图区域下边界 (0-1)
    'subplot_left': 0.12,             # 子图区域左边界 (0-1)
    'subplot_right': 0.98,            # 子图区域右边界 (0-1)

    # --------------------------------------------------------------------------
    # Y轴边距
    # --------------------------------------------------------------------------
    'ylim_margin_ratio': 0.05,        # Y轴上下边距比例 (建议0.05-0.1)
}

# 方法标签名称
LABELS = {
    'truth': 'Ground Truth',
    'transformer': 'Proposed Method',
    'mlp': 'MLP-Koopman',
    'edmd': 'EDMD-Koopman',
}

# 绘制顺序 (底层到顶层)
PLOT_ORDER = ['truth', 'edmd', 'mlp', 'transformer']

# 图例显示顺序
LEGEND_ORDER = ['truth', 'transformer', 'mlp', 'edmd']


def setup_plot_style():
    """配置Matplotlib全局绘图样式"""
    scale = PLOT_CONFIG['global_font_scale']
    linewidth_scale = PLOT_CONFIG['global_linewidth_scale']

    rcParams['font.family'] = PLOT_CONFIG['font_family']
    rcParams['font.size'] = PLOT_CONFIG['font_size_tick'] * scale
    rcParams['axes.labelsize'] = PLOT_CONFIG['font_size_label'] * scale
    rcParams['axes.titlesize'] = PLOT_CONFIG['font_size_label'] * scale
    rcParams['xtick.labelsize'] = PLOT_CONFIG['font_size_tick'] * scale
    rcParams['ytick.labelsize'] = PLOT_CONFIG['font_size_tick'] * scale
    rcParams['legend.fontsize'] = PLOT_CONFIG['font_size_legend'] * scale
    rcParams['legend.columnspacing'] = PLOT_CONFIG['legend_columnspacing']
    rcParams['legend.handlelength'] = PLOT_CONFIG['legend_handlelength']
    rcParams['figure.dpi'] = 100
    rcParams['savefig.dpi'] = PLOT_CONFIG['dpi']
    rcParams['axes.linewidth'] = 1.0
    rcParams['grid.linewidth'] = PLOT_CONFIG['grid_linewidth']
    rcParams['lines.linewidth'] = PLOT_CONFIG['linewidth_prediction'] * linewidth_scale
    rcParams['axes.grid'] = True
    rcParams['grid.alpha'] = PLOT_CONFIG['grid_alpha']
    rcParams['grid.linestyle'] = PLOT_CONFIG['grid_linestyle']
    rcParams['grid.color'] = PLOT_CONFIG['grid_color']
    rcParams['mathtext.fontset'] = 'stix'


def predict_transformer(model_path, config_path):
    """Transformer-Koopman预测"""
    from patchtst_koopman.models.full_model import PatchTSTKoopmanModel

    ext_config = load_config(config_path)
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    model_config = checkpoint['config']
    device = model_config['experiment']['device']
    precision = model_config['experiment'].get('precision', 'float32')
    dtype = torch.float64 if precision == 'float64' else torch.float32
    if precision == 'float64':
        torch.set_default_dtype(torch.float64)
    model = PatchTSTKoopmanModel(model_config)
    if precision == 'float64':
        model = model.double()
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    if 'normalization' in checkpoint:
        norm_stats = checkpoint['normalization']
    else:
        data_dir = ext_config['data']['data_dir']
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(str(Path(__file__).resolve().parents[2]), data_dir)
        train_dataset = KoopmanDataset(data_dir, ext_config, 'train')
        norm_stats = train_dataset.get_norm_stats()

    data_dir = ext_config['data']['data_dir']
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(str(Path(__file__).resolve().parents[2]), data_dir)
    test_dataset = KoopmanDataset(data_dir, ext_config, 'test', norm_stats=norm_stats)

    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    mask = test_dataset.trajectory_id == unique_traj_ids[0]
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    P = model_config['encoder']['history_length']
    x_history = torch.tensor(x_traj[:P], dtype=dtype).to(device)
    u_sequence = torch.tensor(u_traj[P-1:-1], dtype=dtype).to(device)
    x_true_norm = x_traj[P:]

    x_pred_list = []
    with torch.no_grad():
        for h in range(len(u_sequence)):
            z_t = model.encoder(x_history.unsqueeze(0))
            z_next = model.koopman(z_t, u_sequence[h:h+1])
            x_next = model.decoder(z_next)
            x_pred_list.append(x_next.squeeze(0).cpu().numpy())
            x_history = torch.cat([x_history[1:], x_next], dim=0)

    x_pred_norm = np.array(x_pred_list)

    if norm_stats['x_mean'] is not None:
        x_pred = x_pred_norm * norm_stats['x_std'] + norm_stats['x_mean']
        x_true = x_true_norm * norm_stats['x_std'] + norm_stats['x_mean']
    else:
        x_pred = x_pred_norm
        x_true = x_true_norm

    return x_true, x_pred, t_traj[P:]


def predict_mlp(model_path, config_path):
    """MLP-Koopman预测"""
    from patchtst_koopman.models.mlp_koopman_model import MLPKoopmanModel

    ext_config = load_config(config_path)
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    model_config = checkpoint['config']
    precision = model_config['experiment'].get('precision', 'float32')
    if precision == 'float64':
        torch.set_default_dtype(torch.float64)
    model = MLPKoopmanModel(model_config)
    if precision == 'float64':
        model = model.double()
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(model_config['experiment']['device'])
    model.eval()

    if 'normalization' in checkpoint:
        norm_stats = checkpoint['normalization']
    else:
        data_dir = ext_config['data']['data_dir']
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(str(Path(__file__).resolve().parents[2]), data_dir)
        train_dataset = KoopmanDataset(data_dir, ext_config, 'train')
        norm_stats = train_dataset.get_norm_stats()

    data_dir = ext_config['data']['data_dir']
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(str(Path(__file__).resolve().parents[2]), data_dir)
    test_dataset = KoopmanDataset(data_dir, ext_config, 'test', norm_stats=norm_stats)

    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    mask = test_dataset.trajectory_id == unique_traj_ids[0]
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    P = model_config['encoder']['history_length']
    x_history = torch.tensor(x_traj[:P], dtype=torch.float64).to(model_config['experiment']['device'])
    u_sequence = torch.tensor(u_traj[P-1:-1], dtype=torch.float64).to(model_config['experiment']['device'])
    x_true_norm = x_traj[P:]

    x_pred_list = []
    with torch.no_grad():
        for h in range(len(u_sequence)):
            z_t = model.encoder(x_history.unsqueeze(0))
            z_next = model.koopman(z_t, u_sequence[h:h+1])
            x_next = model.decoder(z_next)
            x_pred_list.append(x_next.squeeze(0).cpu().numpy())
            x_history = torch.cat([x_history[1:], x_next], dim=0)

    x_pred_norm = np.array(x_pred_list)

    if norm_stats['x_mean'] is not None:
        x_pred = x_pred_norm * norm_stats['x_std'] + norm_stats['x_mean']
        x_true = x_true_norm * norm_stats['x_std'] + norm_stats['x_mean']
    else:
        x_pred = x_pred_norm
        x_true = x_true_norm

    return x_true, x_pred, t_traj[P:]


def predict_edmd(model_dir, config_path):
    """EDMD-Koopman预测"""
    from patchtst_koopman.training.traditional_edmd_trainer import TraditionalEDMDTrainer
    from patchtst_koopman.lifting.polynomial import PolynomialLifting

    config = load_config(config_path)
    data_dir = config['data']['data_dir']
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(str(Path(__file__).resolve().parents[2]), data_dir)

    train_dataset = KoopmanDataset(data_dir, config, 'train')
    norm_stats = train_dataset.get_norm_stats()
    test_dataset = KoopmanDataset(data_dir, config, 'test', norm_stats=norm_stats)

    trainer = TraditionalEDMDTrainer(config)
    trainer.load_model(model_dir)

    # 修复lifting function
    lifting_meta = np.load(os.path.join(model_dir, 'lifting_meta.npz'), allow_pickle=True)
    lifting_type = str(lifting_meta['lifting_type'])
    if lifting_type == 'polynomial':
        degree = int(lifting_meta['degree'])
        trainer.lifting_fn = PolynomialLifting(degree=degree)

    unique_traj_ids = np.unique(test_dataset.trajectory_id)
    mask = test_dataset.trajectory_id == unique_traj_ids[0]
    x_traj = test_dataset.x[mask]
    u_traj = test_dataset.u[mask]
    t_traj = test_dataset.t[mask]

    P = config['encoder']['history_length']
    x_t = x_traj[P-1]
    u_sequence = u_traj[P-1:-1]
    x_true_norm = x_traj[P:]

    A, B, C = trainer.A, trainer.B, trainer.C
    lifting_fn = trainer.lifting_fn

    x_pred_list = []
    for h in range(len(u_sequence)):
        z_t = lifting_fn.transform(x_t.reshape(1, -1))[0]
        z_next = A @ z_t + B @ u_sequence[h]
        x_next = C @ z_next
        x_pred_list.append(x_next)
        x_t = x_next

    x_pred_norm = np.array(x_pred_list)

    if norm_stats['x_mean'] is not None:
        x_pred = x_pred_norm * norm_stats['x_std'] + norm_stats['x_mean']
        x_true = x_true_norm * norm_stats['x_std'] + norm_stats['x_mean']
    else:
        x_pred = x_pred_norm
        x_true = x_true_norm

    return x_true, x_pred, t_traj[P:]


def compute_metrics(y_true, y_pred):
    """计算RMSE和MAE"""
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mae = np.mean(np.abs(y_true - y_pred))
    return rmse, mae


def _draw_subplot(ax, t, all_data, idx, scale, linewidth_scale):
    """在单个子图上绘制所有曲线"""
    colors = {
        'truth': PLOT_CONFIG['color_truth'],
        'transformer': PLOT_CONFIG['color_transformer'],
        'mlp': PLOT_CONFIG['color_mlp'],
        'edmd': PLOT_CONFIG['color_edmd'],
    }
    linestyles = {
        'truth': PLOT_CONFIG['linestyle_truth'],
        'transformer': PLOT_CONFIG['linestyle_transformer'],
        'mlp': PLOT_CONFIG['linestyle_mlp'],
        'edmd': PLOT_CONFIG['linestyle_edmd'],
    }
    linewidths = {
        'truth': PLOT_CONFIG['linewidth_truth'] * linewidth_scale,
        'transformer': PLOT_CONFIG['linewidth_prediction'] * linewidth_scale,
        'mlp': PLOT_CONFIG['linewidth_prediction'] * linewidth_scale,
        'edmd': PLOT_CONFIG['linewidth_prediction'] * linewidth_scale,
    }
    alphas = {
        'truth': PLOT_CONFIG['alpha_truth'],
        'transformer': PLOT_CONFIG['alpha_prediction'],
        'mlp': PLOT_CONFIG['alpha_prediction'],
        'edmd': PLOT_CONFIG['alpha_prediction'],
    }

    line_handles = {}
    for name in PLOT_ORDER:
        h, = ax.plot(t, all_data[name][:, idx],
                     color=colors[name],
                     linestyle=linestyles[name],
                     linewidth=linewidths[name],
                     label=LABELS[name],
                     alpha=alphas[name])
        line_handles[name] = h
    return line_handles


def _finalize_subplot(ax, i, ylabel_str, is_last, line_handles, n_states):
    """子图公共配置"""
    scale = PLOT_CONFIG['global_font_scale']

    ax.set_ylabel(ylabel_str,
                  fontsize=PLOT_CONFIG['font_size_label'] * scale,
                  fontweight='normal',
                  labelpad=PLOT_CONFIG['ylabel_horizontal_pad'])

    ax.grid(True,
            alpha=PLOT_CONFIG['grid_alpha'],
            linestyle=PLOT_CONFIG['grid_linestyle'],
            linewidth=PLOT_CONFIG['grid_linewidth'],
            color=PLOT_CONFIG['grid_color'])

    ax.tick_params(labelsize=PLOT_CONFIG['font_size_tick'] * scale,
                   direction='in', width=1.0, pad=5)

    ymin, ymax = ax.get_ylim()
    margin = (ymax - ymin) * PLOT_CONFIG['ylim_margin_ratio']
    ax.set_ylim(ymin - margin, ymax + margin)

    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

    if i == 0:
        ordered_handles = [line_handles[k] for k in LEGEND_ORDER]
        ordered_labels = [h.get_label() for h in ordered_handles]
        ax.legend(ordered_handles, ordered_labels,
                  loc=PLOT_CONFIG['legend_loc'],
                  bbox_to_anchor=(PLOT_CONFIG['legend_bbox_x'], PLOT_CONFIG['legend_bbox_y']),
                  ncol=PLOT_CONFIG['legend_ncol'],
                  fontsize=PLOT_CONFIG['font_size_legend'] * scale,
                  framealpha=PLOT_CONFIG['legend_framealpha'],
                  frameon=PLOT_CONFIG['legend_frameon'],
                  columnspacing=PLOT_CONFIG['legend_columnspacing'],
                  handlelength=PLOT_CONFIG['legend_handlelength'],
                  handletextpad=PLOT_CONFIG['legend_handletextpad'],
                  borderpad=PLOT_CONFIG['legend_borderpad'])

    if is_last:
        ax.set_xlabel('Time (s)',
                       fontsize=PLOT_CONFIG['font_size_label'] * scale,
                       fontweight='normal')


def plot_comparison(x_true, predictions, t, save_dir):
    """绘制状态对比图"""
    setup_plot_style()
    scale = PLOT_CONFIG['global_font_scale']
    linewidth_scale = PLOT_CONFIG['global_linewidth_scale']

    min_len = min(v.shape[0] for v in predictions.values())
    x_true = x_true[:min_len]
    predictions = {k: v[:min_len] for k, v in predictions.items()}
    t = t[:min_len]

    all_data = {'truth': x_true}
    all_data.update(predictions)

    n_states = x_true.shape[1]
    state_names = [f'$x_{i+1}$' for i in range(n_states)]
    state_units = ['cm'] * n_states

    fig, axes = plt.subplots(n_states, 1,
                              figsize=(PLOT_CONFIG['figure_width'],
                                       PLOT_CONFIG['figure_height']))
    if n_states == 1:
        axes = [axes]

    for i in range(n_states):
        ax = axes[i]
        handles = _draw_subplot(ax, t, all_data, i, scale, linewidth_scale)
        _finalize_subplot(ax, i, f'{state_names[i]} ({state_units[i]})', i == n_states - 1, handles, n_states)

    plt.subplots_adjust(hspace=PLOT_CONFIG['subplot_hspace'],
                        top=PLOT_CONFIG['subplot_top'],
                        bottom=PLOT_CONFIG['subplot_bottom'],
                        left=PLOT_CONFIG['subplot_left'],
                        right=PLOT_CONFIG['subplot_right'])

    Path(save_dir).mkdir(parents=True, exist_ok=True)
    for fmt in ('png', 'pdf'):
        plt.savefig(os.path.join(save_dir, f'platform2_state_comparison.{fmt}'),
                    dpi=PLOT_CONFIG['dpi'], bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print(f'[状态对比图] 已保存到 {save_dir}')


def print_metrics(x_true, predictions, state_names):
    """打印RMSE指标"""
    print(f"\n{'='*70}")
    print(f"  平台2 (软体机械臂) - RMSE指标")
    print(f"{'='*70}")
    header = f"{'State':<12}"
    for method in ['transformer', 'mlp', 'edmd']:
        header += f"  {LABELS[method]:<18}"
    print(header)
    print('-' * 70)
    for i, name in enumerate(state_names):
        row = f"{name:<12}"
        for method in ['transformer', 'mlp', 'edmd']:
            rmse, _ = compute_metrics(x_true[:, i], predictions[method][:, i])
            row += f"  {rmse:<18.6f}"
        print(row)
    print('-' * 70)
    row = f"{'Overall':<12}"
    for method in ['transformer', 'mlp', 'edmd']:
        rmse, _ = compute_metrics(x_true, predictions[method])
        row += f"  {rmse:<18.6f}"
    print(row)
    print(f"{'='*70}\n")


if __name__ == '__main__':
    print("=" * 70)
    print("  实验1 - 平台2轨迹预测对比 (软体机械臂)")
    print("=" * 70)

    predictions = {}

    print("\n[1/3] Transformer-Koopman 预测...")
    x_true, x_pred, t = predict_transformer(TRANSFORMER_MODEL_PATH, CONFIG_PATH)
    predictions['transformer'] = x_pred
    print(f"  Shape: {x_pred.shape}, Time: [{t[0]:.3f}, {t[-1]:.3f}]s")

    print("\n[2/3] MLP-Koopman 预测...")
    _, x_pred, _ = predict_mlp(MLP_MODEL_PATH, CONFIG_PATH)
    predictions['mlp'] = x_pred
    print(f"  Shape: {x_pred.shape}")

    print("\n[3/3] EDMD-Koopman 预测...")
    _, x_pred, _ = predict_edmd(EDMD_MODEL_PATH, CONFIG_PATH)
    predictions['edmd'] = x_pred
    print(f"  Shape: {x_pred.shape}")

    min_len = min(v.shape[0] for v in predictions.values())
    x_true = x_true[:min_len]
    predictions = {k: v[:min_len] for k, v in predictions.items()}
    t = t[:min_len]

    state_names = ['$x_1$', '$x_2$']
    print_metrics(x_true, predictions, state_names)

    print("绘制图表...")
    plot_comparison(x_true, predictions, t, SAVE_DIR)

    print("\n完成!")
