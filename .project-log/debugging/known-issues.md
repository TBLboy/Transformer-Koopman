# Debugging

## Known Issues

### 2026-05-25 — data/ 可能为空

- **Symptom**: `code-projectv2/data/` 目录当前无文件
- **Likely cause**: 之前的复制操作在 Cursor sandbox 中进行，可能未持久化
- **Fix**: 手动从 `code_project/data/` 复制
- **Command**: `Copy-Item "C:\Users\Windows\Desktop\论文4\code_project\data\*" "C:\Users\Windows\Desktop\论文4\code-projectv2\data\" -Recurse`
- **Status**: Open

### 2026-05-25 — conda run 不支持多行脚本

- **Symptom**: `conda run -n koopman python -c "..."` 当参数包含换行时失败
- **Fix**: 改用单行命令或写入 .py 文件执行
- **Workaround used**: 脚本统一写在 `.py` 文件中调用
- **Status**: Workaround applied
