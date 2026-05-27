# Business Logic Graph

## Main

```text
RawData(NPZ) -> KoopmanDataset -> [Encoder|Lifting] -> KoopmanDynamics -> Decoder -> Prediction
                                                                              |
                                                                              v
                                                                         LQR Controller
```

## Sub-paths

```text
# 主方法训练
RawData -> KoopmanDataset -> PatchTSTEncoder -> KoopmanDynamics(EDMD) -> LinearDecoder -> TrainLoop -> Checkpoint(.pth)

# 消融实验
RawData -> KoopmanDataset -> AblationEncoder -> KoopmanDynamics(EDMD) -> LinearDecoder -> CompareResults -> Plot/Table

# Traditional EDMD
RawData -> KoopmanDataset -> LiftingFunction(poly/rbf/robot) -> KoopmanDynamics(LeastSquares) -> no_decoder -> Predict

# 部署
Checkpoint(.pth) -> export_assets.py -> model_assets/ -> TransformerKoopmanController -> FlexibleArmControl34
```

## Branches

- None yet.

## Archived

- Original code_project/ (refactored into code-projectv2/)
