# SD 卡 CSV → 桌面端导入链路（阶段一收尾）

## 1. 为什么需要这条链路

田间节点把原始 1 s 数据写入 microSD（`seq,unix_ms,p0_centi,...`）。回实验室后，需要把 CSV 导入桌面端（Web/本地 SQLite），才能：
- 与回放数据对比；
- 查看诊断事件；
- 给导师演示离线数据。

**2026-10-17 状态**：后端导入已打通（CLI + HTTP API），前端尚未做专门的文件选择按钮，但可通过 CLI 导入后刷新桌面端查看。

## 2. 固件 CSV 格式（唯一真源）

表头：

```
seq,unix_ms,p0_centi,p1_centi,dp_centi,q_milli,count10,quality,zq_milli,zr_milli,sq_milli,alarm
```

| 字段 | 单位 | 说明 |
|---|---|---|
| seq | — | 1 s 样本序号 |
| unix_ms | ms | 节点 wall clock（合成回放里从 1000 起） |
| p0_centi | 0.01 kPa | 干管表压 |
| p1_centi | 0.01 kPa | 下游表压 |
| dp_centi | 0.01 kPa | 差压 |
| q_milli | 0.001 L/min | 10 s 平均流量 |
| count10 | pulses | 最近 10 s 累计脉冲数 |
| quality | enum | 0=OK, 1=open_loop, 2=saturated, 3=timing, 4=not_ready |
| zq_milli / zr_milli | 0.001 | 标准化残差（节点端诊断） |
| sq_milli / sr_milli | 0.001 | CUSUM 累积状态 |
| alarm | enum | 0=无，1=泄漏，2=受限 |

固件生成函数：`firmware/core/sampler.c` 中 `sampler_row_csv()`。

## 3. 命令行导入（已验证）

```bash
python scripts/import_sdcard_csv.py firmware/build/out_leak.csv --db tmp/desktop_runtime/operations.sqlite --label "田间 1# 节点 2027-04-15"
```

参数：
- `csv`：SD 卡 CSV 文件路径。
- `--db`：桌面端 SQLite 路径。默认与 `scripts/run_platform.py` / 桌面端一致。
- `--label`：会话标签，用于历史列表区分。

导入后启动桌面端即可在历史会话中查看：

```bash
python scripts/run_platform.py
# 或双击桌面版滴智卫_V1.3.exe
```

## 4. HTTP API 导入（供前端接入）

POST `/api/sdcard/import`

```json
{
  "csv": "seq,unix_ms,...\n0,1000,11650,...",
  "label": "田间 1# 节点"
}
```

返回：当前会话 state（含 `run.session`、`imported_rows`、`processed_samples`、`events_count`）。

请求体上限已放宽到 **2 MB**（专门用于此接口），足够覆盖数小时 1 s 数据。

## 5. 实现要点与限制

- **健康参照**：导入使用默认合成参照作为候选（`approved=0`）。这意味着平台会显示“健康参照未确认”，不是 bug。真正用于结题的诊断必须在台架/田间用独立健康段重新标定后，再替换 profile。
- **累计脉冲**：CSV 只给出 10 s 平均流量 `q_milli`，没有每秒累计脉冲。导入器按 540 pulses/L 从 `q_milli` 反推每秒脉冲并累加，足以让 C 桥重新计算流量与诊断；但与真实计数值存在量化误差。
- **质量位**：`quality != 0` 的行以 NaN 压力喂入平台，被标记为测量异常。
- **前端**：当前 `deliverables/index.html` 没有文件选择按钮。下一步可在“历史/导入”页增加 `<input type="file">` 调用 `/api/sdcard/import`。

## 6. 验证脚本

```bash
# 单元/直接导入测试
C:/Users/Lenovo/.workbuddy/binaries/python/envs/default/Scripts/python.exe scripts/test_sdcard_import.py

# HTTP API 端到端测试
C:/Users/Lenovo/.workbuddy/binaries/python/envs/default/Scripts/python.exe scripts/test_sdcard_api.py
```

两个脚本均使用 `firmware/build/out_normal.csv`（固件 host 回放产物）作为输入，导入后断言样本数 600、事件可查询。

## 7. 相关文件

- 后端：`prototype/platform_service.py` 中 `Platform.import_sdcard()`
- 路由：`scripts/run_platform.py` 中 `/api/sdcard/import`
- CLI：`scripts/import_sdcard_csv.py`
- 测试：`scripts/test_sdcard_import.py`、`scripts/test_sdcard_api.py`
