"""
消融实验绘图代码 (IEEE风格)
包含: 模块消融柱状图 + 超参数消融折线图
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
from pathlib import Path

# NOTE: this legacy script references model classes (WoPatchTSTModel, WoKoopmanModel,
# WoSpectralModel) that never existed in the canonical ablation framework. The current
# pipeline lives in scripts/ablation/. To regenerate the paper bar/line charts from a
# fresh ablation run, use scripts/ablation/plot_ablation_results.py (LaTeX table) or
# figures/ablation/generate_ablation_materials.py (PDF charts). This file is kept for
# historical reference only and the placeholder MODULE_VARIANTS classes below need to
# be updated to point at the AblationModel + factory functions in
# patchtst_koopman.ablation.models before this script can be re-run end-to-end.

from patchtst_koopman.data.dataset import KoopmanDataset
from patchtst_koopman.utils.config_loader import load_config
from patchtst_koopman.models.full_model import PatchTSTKoopmanModel
from patchtst_koopman.ablation.models import (
    create_no_patch,
    create_no_attention,
    create_no_positional,
)

# ============================================================================
# Path configuration — edit to point at your local data
# ============================================================================
P1_CONFIG = 'configs/platform1.yaml'
P2_CONFIG = 'configs/platform2.yaml'
ABLATION_BASE = 'results/ablation'
SAVE_DIR = 'figures/ablation/output'
# ============================================================================

# ============================================================================
# Module variant registry — adjust the factories to match your run
# ============================================================================
MODULE_VARIANTS = {
    'full_model': {'label': 'Full Model', 'factory': PatchTSTKoopmanModel},
    'no_patch':   {'label': 'w/o Patch',   'factory': create_no_patch},
    'no_attention': {'label': 'w/o Attention', 'factory': create_no_attention},
    'no_positional': {'label': 'w/o Positional', 'factory': create_no_positional},
}

HYPERPARAM_CONFIGS = {
    'latent_dim': {
        'label': 'Latent Dimension $d$',
        'variants': ['latent_dim_4', 'latent_dim_8', 'latent_dim_16', 'latent_dim_32', 'latent_dim_64'],
        'values': [4, 8, 16, 32, 64],
    },
    'history_length': {
        'label': 'History Length $P$',
        'variants': ['history_4', 'history_8', 'history_16', 'history_32'],
        'values': [4, 8, 16, 32],
    },
    'd_model': {
        'label': 'Model Dimension $d_{model}$',
        'variants': ['dmodel_8', 'dmodel_16', 'dmodel_32', 'dmodel_64'],
        'values': [8, 16, 32, 64],
    },
}

PLATFORM_CONFIGS = {
    'platform1': {
        'config_path': P1_CONFIG,
        'module_dir': 'module_platform1',
        'hyper_dir': 'hyperparameter_platform1',
        'label': 'Platform 1 (3-DOF Manipulator)',
    },
    'platform2': {
        'config_path': P2_CONFIG,
        'module_dir': 'module_platform2',
        'hyper_dir': 'hyperparameter_platform2',
        'label': 'Platform 2 (Soft Robot)',
    },
}

# ============================================================================
# 绘图参数配置（可手动调节）
# ============================================================================
PLOT_CONFIG = {
    # --------------------------------------------------------------------------
    # 图片尺寸
    # --------------------------------------------------------------------------
    'figure_width_bar': 7.0,          # 柱状图宽度 (英寸)
    'figure_height_bar': 4.5,         # 柱状图高度 (英寸)
    'figure_width_line': 7.0,         # 折线图宽度 (英寸)
    'figure_height_line': 4.5,        # 折线图高度 (英寸)
    'dpi': 300,                       # 输出分辨率

    # --------------------------------------------------------------------------
    # 全局缩放
    # --------------------------------------------------------------------------
    'global_font_scale': 1.8,         # 全局字体缩放因子
    'global_linewidth_scale': 1.6,    # 全局线宽缩放因子

    # --------------------------------------------------------------------------
    # 字体设置
    # --------------------------------------------------------------------------
    'font_family': 'Times New Roman', # 字体
    'font_size_label': 11,            # 坐标轴标签字体大小
    'font_size_tick': 10,             # 刻度字体大小
    'font_size_legend': 9,            # 图例字体大小
    'font_size_title': 12,            # 标题字体大小
    'ylabel_horizontal_pad': 10,      # Y轴标签水平距离

    # --------------------------------------------------------------------------
    # 柱状图参数
    # --------------------------------------------------------------------------
    'bar_width': 0.25,                # 每根柱子的宽度
    'bar_colors': ['#000000', '#FF7F0E', '#2CA02C', '#D62728'],  # 各变体颜色
    'bar_edgecolor': 'black',         # 柱子边框颜色
    'bar_linewidth': 0.8,             # 柱子边框线宽
    'bar_hatch_patterns': ['', '//', '\\\\', 'xx'],  # 各变体填充图案

    # --------------------------------------------------------------------------
    # 折线图参数
    # --------------------------------------------------------------------------
    'line_colors': ['#000000', '#D62728'],   # 各平台颜色 (P1黑, P2红)
    'line_styles': ['-', '-'],               # 各平台线型
    'line_markers': ['o', 's'],              # 各平台标记形状
    'line_markersize': 8,                    # 标记大小
    'line_marker_edgecolor': 'white',        # 标记边缘颜色
    'line_marker_edgewidth': 1.5,            # 标记边缘线宽
    'line_linewidth': 2.0,                   # 折线线宽

    # --------------------------------------------------------------------------
    # 网格设置
    # --------------------------------------------------------------------------
    'grid_alpha': 0.3,                # 网格透明度
    'grid_linestyle': '--',           # 网格线型
    'grid_linewidth': 0.8,            # 网格线宽
    'grid_color': '#CCCCCC',          # 网格颜色

    # --------------------------------------------------------------------------
    # 图例参数（重点调节区域）
    # --------------------------------------------------------------------------
    'legend_framealpha': 0.95,        # 图例背景透明度
    'legend_frameon': False,          # 是否显示图例边框
    'legend_loc': 'upper right',      # 图例锚点位置
    'legend_bbox_x': 1.0,            # 图例水平位置
    'legend_bbox_y': 1.0,            # 图例垂直位置
    'legend_handlelength': 1.5,       # 图例中线段的长度
    'legend_columnspacing': 1.0,      # 图例列之间的间距
    'legend_handletextpad': 0.5,      # 线段与文字之间的间距
    'legend_borderpad': 0.4,          # 图例边框内边距
    'legend_ncol': 1,                 # 图例列数

    # --------------------------------------------------------------------------
    # 子图布局
    # --------------------------------------------------------------------------
    'subplot_top': 0.92,              # 子图区域上边界
    'subplot_bottom': 0.15,           # 子图区域下边界
    'subplot_left': 0.15,             # 子图区域左边界
    'subplot_right': 0.95,            # 子图区域右边界

    # --------------------------------------------------------------------------
    # Y轴边距
    # --------------------------------------------------------------------------
    'ylim_margin_ratio': 0.1,         # Y轴上下边距比例
}


def setup_plot_style():
    """配置Matplotlib全局绘图样式"""
    scale = PLOT_CONFIG['global_font_scale']
    rcParams['font.family'] = PLOT_CONFIG['font_family']
    rcParams['font.size'] = PLOT_CONFIG['font_size_tick'] * scale
    rcParams['axes.labelsize'] = PLOT_CONFIG['font_size_label'] * scale
    rcParams['axes.titlesize'] = PLOT_CONFIG['font_size_title'] * scale
    rcParams['xtick.labelsize'] = PLOT_CONFIG['font_size_tick'] * scale
    rcParams['ytick.labelsize'] = PLOT_CONFIG['font_size_tick'] * scale
    rcParams['legend.fontsize'] = PLOT_CONFIG['font_size_legend'] * scale
    rcParams['figure.dpi'] = 100
    rcParams['savefig.dpi'] = PLOT_CONFIG['dpi']
    rcParams['axes.linewidth'] = 1.0
    rcParams['mathtext.fontset'] = 'stix'


# ============================================================================
# 预测函数
# ============================================================================
def predict_model(model_path, config_path, model_class):
    """通用模型预测函数"""
    ext_config = load_config(config_path)
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    model_config = checkpoint['config']
    precision = model_config['experiment'].get('precision', 'float32')
    if precision == 'float64':
        torch.set_default_dtype(torch.float64)
    model = model_class(model_config)
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

    P = model_config['encoder']['history_length']
    dtype = torch.float64 if precision == 'float64' else torch.float32
    device = model_config['experiment']['device']
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

    rmse = np.sqrt(np.mean((x_pred - x_true) ** 2))
    mae = np.mean(np.abs(x_pred - x_true))
    return rmse, mae


# ============================================================================
# 计算所有消融结果
# ============================================================================
def compute_module_ablation():
    """计算模块消融的RMSE"""
    results = {}
    for platform_key, platform_cfg in PLATFORM_CONFIGS.items():
        config_path = platform_cfg['config_path']
        module_dir = os.path.join(ABLATION_BASE, platform_cfg['module_dir'])
        results[platform_key] = {}

        print(f"\n{'='*60}")
        print(f"  模块消融 - {platform_cfg['label']}")
        print(f"{'='*60}")

        for variant_key, variant_cfg in MODULE_VARIANTS.items():
            model_path = os.path.join(module_dir, variant_key, 'model.pth')
            if not os.path.exists(model_path):
                print(f"  {variant_cfg['label']}: 模型文件不存在，跳过")
                results[platform_key][variant_key] = None
                continue

            print(f"  {variant_cfg['label']}...", end=' ', flush=True)
            rmse, mae = predict_model(model_path, config_path, variant_cfg['model_class'])
            results[platform_key][variant_key] = {'rmse': rmse, 'mae': mae}
            print(f"RMSE={rmse:.6f}, MAE={mae:.6f}")

    return results


def compute_hyperparameter_ablation():
    """计算超参数消融的RMSE"""
    results = {}
    for hyper_key, hyper_cfg in HYPERPARAM_CONFIGS.items():
        results[hyper_key] = {}

        print(f"\n{'='*60}")
        print(f"  超参数消融 - {hyper_cfg['label']}")
        print(f"{'='*60}")

        for platform_key, platform_cfg in PLATFORM_CONFIGS.items():
            config_path = platform_cfg['config_path']
            hyper_dir = os.path.join(ABLATION_BASE, platform_cfg['hyper_dir'])
            results[hyper_key][platform_key] = []

            print(f"\n  {platform_cfg['label']}:")
            for variant_name, value in zip(hyper_cfg['variants'], hyper_cfg['values']):
                model_path = os.path.join(hyper_dir, variant_name, 'model.pth')
                if not os.path.exists(model_path):
                    print(f"    {variant_name}: 模型文件不存在，跳过")
                    results[hyper_key][platform_key].append(None)
                    continue

                print(f"    {variant_name} (value={value})...", end=' ', flush=True)
                rmse, mae = predict_model(model_path, config_path, PatchTSTKoopmanModel)
                results[hyper_key][platform_key].append({'rmse': rmse, 'mae': mae, 'value': value})
                print(f"RMSE={rmse:.6f}")

    return results


# ============================================================================
# 绘图函数
# ============================================================================
def plot_module_ablation(module_results):
    """绘制模块消融柱状图"""
    setup_plot_style()
    scale = PLOT_CONFIG['global_font_scale']

    fig, ax = plt.subplots(figsize=(PLOT_CONFIG['figure_width_bar'],
                                     PLOT_CONFIG['figure_height_bar']))

    variant_keys = list(MODULE_VARIANTS.keys())
    variant_labels = [MODULE_VARIANTS[k]['label'] for k in variant_keys]
    n_variants = len(variant_keys)
    n_platforms = len(PLATFORM_CONFIGS)
    platform_keys = list(PLATFORM_CONFIGS.keys())
    platform_labels = [PLATFORM_CONFIGS[k]['label'] for k in platform_keys]

    bar_width = PLOT_CONFIG['bar_width']
    x = np.arange(n_variants)

    for i, pkey in enumerate(platform_keys):
        offset = (i - (n_platforms - 1) / 2) * bar_width
        rmses = []
        for vkey in variant_keys:
            if module_results.get(pkey, {}).get(vkey) is not None:
                rmses.append(module_results[pkey][vkey]['rmse'])
            else:
                rmses.append(0)

        bars = ax.bar(x + offset, rmses, bar_width,
                      label=platform_labels[i],
                      color=PLOT_CONFIG['bar_colors'][i],
                      edgecolor=PLOT_CONFIG['bar_edgecolor'],
                      linewidth=PLOT_CONFIG['bar_linewidth'],
                      hatch=PLOT_CONFIG['bar_hatch_patterns'][i])

        for bar, val in zip(bars, rmses):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom',
                        fontsize=PLOT_CONFIG['font_size_tick'] * scale * 0.7)

    ax.set_ylabel('RMSE', fontsize=PLOT_CONFIG['font_size_label'] * scale,
                  labelpad=PLOT_CONFIG['ylabel_horizontal_pad'])
    ax.set_xticks(x)
    ax.set_xticklabels(variant_labels, fontsize=PLOT_CONFIG['font_size_tick'] * scale)
    ax.tick_params(axis='y', labelsize=PLOT_CONFIG['font_size_tick'] * scale, direction='in')

    ax.grid(True, axis='y', alpha=PLOT_CONFIG['grid_alpha'],
            linestyle=PLOT_CONFIG['grid_linestyle'],
            linewidth=PLOT_CONFIG['grid_linewidth'],
            color=PLOT_CONFIG['grid_color'])
    ax.set_axisbelow(True)

    ymin, ymax = ax.get_ylim()
    margin = (ymax - ymin) * PLOT_CONFIG['ylim_margin_ratio']
    ax.set_ylim(0, ymax + margin)

    ax.legend(loc=PLOT_CONFIG['legend_loc'],
              bbox_to_anchor=(PLOT_CONFIG['legend_bbox_x'], PLOT_CONFIG['legend_bbox_y']),
              ncol=PLOT_CONFIG['legend_ncol'],
              fontsize=PLOT_CONFIG['font_size_legend'] * scale,
              framealpha=PLOT_CONFIG['legend_framealpha'],
              frameon=PLOT_CONFIG['legend_frameon'],
              handlelength=PLOT_CONFIG['legend_handlelength'],
              columnspacing=PLOT_CONFIG['legend_columnspacing'],
              handletextpad=PLOT_CONFIG['legend_handletextpad'],
              borderpad=PLOT_CONFIG['legend_borderpad'])

    plt.subplots_adjust(top=PLOT_CONFIG['subplot_top'],
                        bottom=PLOT_CONFIG['subplot_bottom'],
                        left=PLOT_CONFIG['subplot_left'],
                        right=PLOT_CONFIG['subplot_right'])

    Path(SAVE_DIR).mkdir(parents=True, exist_ok=True)
    for fmt in ('png', 'pdf'):
        plt.savefig(os.path.join(SAVE_DIR, f'module_ablation.{fmt}'),
                    dpi=PLOT_CONFIG['dpi'], bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print(f'\n[模块消融图] 已保存到 {SAVE_DIR}')


def plot_hyperparameter_ablation(hyper_results):
    """绘制超参数消融折线图"""
    setup_plot_style()
    scale = PLOT_CONFIG['global_font_scale']

    n_hyper = len(HYPERPARAM_CONFIGS)
    fig, axes = plt.subplots(1, n_hyper,
                              figsize=(PLOT_CONFIG['figure_width_line'] * n_hyper / 2,
                                       PLOT_CONFIG['figure_height_line']))
    if n_hyper == 1:
        axes = [axes]

    platform_keys = list(PLATFORM_CONFIGS.keys())
    platform_labels = [PLATFORM_CONFIGS[k]['label'] for k in platform_keys]

    for ax_idx, (hyper_key, hyper_cfg) in enumerate(HYPERPARAM_CONFIGS.items()):
        ax = axes[ax_idx]

        for p_idx, pkey in enumerate(platform_keys):
            data = hyper_results.get(hyper_key, {}).get(pkey, [])
            values = [d['value'] for d in data if d is not None]
            rmses = [d['rmse'] for d in data if d is not None]

            if len(values) == 0:
                continue

            ax.plot(values, rmses,
                    color=PLOT_CONFIG['line_colors'][p_idx],
                    linestyle=PLOT_CONFIG['line_styles'][p_idx],
                    linewidth=PLOT_CONFIG['line_linewidth'] * PLOT_CONFIG['global_linewidth_scale'],
                    marker=PLOT_CONFIG['line_markers'][p_idx],
                    markersize=PLOT_CONFIG['line_markersize'] * PLOT_CONFIG['global_font_scale'] / 1.8,
                    markeredgecolor=PLOT_CONFIG['line_marker_edgecolor'],
                    markeredgewidth=PLOT_CONFIG['line_marker_edgewidth'],
                    label=platform_labels[p_idx])

        ax.set_xlabel(hyper_cfg['label'],
                      fontsize=PLOT_CONFIG['font_size_label'] * scale)
        ax.set_ylabel('RMSE',
                      fontsize=PLOT_CONFIG['font_size_label'] * scale,
                      labelpad=PLOT_CONFIG['ylabel_horizontal_pad'])
        ax.tick_params(labelsize=PLOT_CONFIG['font_size_tick'] * scale, direction='in')

        ax.grid(True, alpha=PLOT_CONFIG['grid_alpha'],
                linestyle=PLOT_CONFIG['grid_linestyle'],
                linewidth=PLOT_CONFIG['grid_linewidth'],
                color=PLOT_CONFIG['grid_color'])
        ax.set_axisbelow(True)

        ax.legend(loc=PLOT_CONFIG['legend_loc'],
                  bbox_to_anchor=(PLOT_CONFIG['legend_bbox_x'], PLOT_CONFIG['legend_bbox_y']),
                  ncol=PLOT_CONFIG['legend_ncol'],
                  fontsize=PLOT_CONFIG['font_size_legend'] * scale,
                  framealpha=PLOT_CONFIG['legend_framealpha'],
                  frameon=PLOT_CONFIG['legend_frameon'],
                  handlelength=PLOT_CONFIG['legend_handlelength'],
                  columnspacing=PLOT_CONFIG['legend_columnspacing'],
                  handletextpad=PLOT_CONFIG['legend_handletextpad'],
                  borderpad=PLOT_CONFIG['legend_borderpad'])

    plt.subplots_adjust(top=PLOT_CONFIG['subplot_top'],
                        bottom=PLOT_CONFIG['subplot_bottom'],
                        left=0.08,
                        right=PLOT_CONFIG['subplot_right'],
                        wspace=0.35)

    Path(SAVE_DIR).mkdir(parents=True, exist_ok=True)
    for fmt in ('png', 'pdf'):
        plt.savefig(os.path.join(SAVE_DIR, f'hyperparameter_ablation.{fmt}'),
                    dpi=PLOT_CONFIG['dpi'], bbox_inches='tight', pad_inches=0.05)
    plt.close()
    print(f'[超参数消融图] 已保存到 {SAVE_DIR}')


# ============================================================================
# 主程序
# ============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("  消融实验绘图")
    print("=" * 70)

    # 1. 模块消融
    print("\n[1/2] 计算模块消融结果...")
    module_results = compute_module_ablation()

    # 2. 超参数消融
    print("\n[2/2] 计算超参数消融结果...")
    hyper_results = compute_hyperparameter_ablation()

    # 3. 绘图
    print("\n" + "=" * 70)
    print("  绘图")
    print("=" * 70)
    plot_module_ablation(module_results)
    plot_hyperparameter_ablation(hyper_results)

    # 4. 保存数值结果
    print("\n保存数值结果...")
    import json

    save_data = {
        'module_ablation': {},
        'hyperparameter_ablation': {},
    }
    for pkey in PLATFORM_CONFIGS:
        save_data['module_ablation'][pkey] = {}
        for vkey in MODULE_VARIANTS:
            r = module_results.get(pkey, {}).get(vkey)
            if r is not None:
                save_data['module_ablation'][pkey][vkey] = {
                    'rmse': float(r['rmse']),
                    'mae': float(r['mae']),
                }

    for hkey in HYPERPARAM_CONFIGS:
        save_data['hyperparameter_ablation'][hkey] = {}
        for pkey in PLATFORM_CONFIGS:
            data = hyper_results.get(hkey, {}).get(pkey, [])
            save_data['hyperparameter_ablation'][hkey][pkey] = [
                {'value': d['value'], 'rmse': float(d['rmse']), 'mae': float(d['mae'])}
                for d in data if d is not None
            ]

    result_path = os.path.join(SAVE_DIR, 'ablation_results.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print(f"数值结果已保存: {result_path}")

    print("\n完成!")
