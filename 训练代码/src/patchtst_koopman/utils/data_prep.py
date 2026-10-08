"""Dataset preparation shared across training scripts."""
from patchtst_koopman.data.dataset import KoopmanDataset


def prepare_datasets(config):
    """Build train / val / test datasets with normalisation sharing.

    The training set computes its own mean/std; val and test are normalised
    using those statistics (passed via ``norm_stats``) so the splits are
    comparable.

    Returns:
        ``(train_dataset, val_dataset, test_dataset, norm_stats)``
    """
    data_dir = config["data"]["data_dir"]

    train_dataset = KoopmanDataset(data_dir, config, "train")
    norm_stats = train_dataset.get_norm_stats()

    val_dataset = KoopmanDataset(data_dir, config, "val", norm_stats=norm_stats)
    test_dataset = KoopmanDataset(data_dir, config, "test", norm_stats=norm_stats)

    return train_dataset, val_dataset, test_dataset, norm_stats
