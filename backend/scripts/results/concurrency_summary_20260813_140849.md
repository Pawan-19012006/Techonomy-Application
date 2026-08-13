# Techonomy Read-Only Concurrency Baseline Test Summary
**Date/Time**: 2026-08-13 14:08:49
**Endpoint**: `http://localhost:8000/api/chat`
**Target Team**: `TEAM-01`
**Uvicorn Process PID**: `18954`

## Concurrency Benchmark Results Table

| Concurrency | Success | Failures | Timeouts | P50 (s) | P95 (s) | P99 (s) | Max (s) | Throughput (req/s) | Avg CPU (%) | Max RAM (MB) |
| ----------: | ------: | -------: | -------: | ------: | ------: | ------: | ------: | ----------------: | ----------: | -----------: |
| 1 | 1 | 0 | 0 | 2.048 | 2.048 | 2.048 | 2.048 | 0.480 | 8.4% | 183.3 MB |
| 5 | 5 | 0 | 0 | 5.708 | 11.264 | 11.264 | 11.264 | 0.442 | 2.8% | 183.8 MB |
| 10 | 10 | 0 | 0 | 9.065 | 15.319 | 15.319 | 15.319 | 0.652 | 3.0% | 149.8 MB |
| 25 | 3 | 22 | 22 | 90.026 | 90.028 | 90.029 | 90.029 | 0.033 | 0.7% | 144.9 MB |
| 50 | 0 | 50 | 50 | 90.030 | 90.033 | 90.033 | 90.033 | 0.000 | 0.5% | 141.5 MB |

## Per-Level Detailed Breakdown

### Concurrency Level: 1
- **Total Requests**: 1
- **Wall-Clock Time**: 2.084s
- **Status Codes**: {'200': 1}
- **PostgreSQL Connections**: Before=13 | After=14
- **Uvicorn CPU**: Avg=8.4% | Max=24.4%
- **Uvicorn RAM**: Avg=159.3 MB | Max=183.3 MB

### Concurrency Level: 5
- **Total Requests**: 5
- **Wall-Clock Time**: 11.302s
- **Status Codes**: {'200': 5}
- **PostgreSQL Connections**: Before=14 | After=19
- **Uvicorn CPU**: Avg=2.8% | Max=19.8%
- **Uvicorn RAM**: Avg=151.7 MB | Max=183.8 MB

### Concurrency Level: 10
- **Total Requests**: 10
- **Wall-Clock Time**: 15.344s
- **Status Codes**: {'200': 10}
- **PostgreSQL Connections**: Before=19 | After=-1
- **Uvicorn CPU**: Avg=3.0% | Max=15.5%
- **Uvicorn RAM**: Avg=139.3 MB | Max=149.8 MB

### Concurrency Level: 25
- **Total Requests**: 25
- **Wall-Clock Time**: 90.06s
- **Status Codes**: {'TIMEOUT': 22, '200': 3}
- **PostgreSQL Connections**: Before=-1 | After=-1
- **Uvicorn CPU**: Avg=0.7% | Max=35.6%
- **Uvicorn RAM**: Avg=110.9 MB | Max=144.9 MB

### Concurrency Level: 50
- **Total Requests**: 50
- **Wall-Clock Time**: 90.072s
- **Status Codes**: {'TIMEOUT': 50}
- **PostgreSQL Connections**: Before=-1 | After=-1
- **Uvicorn CPU**: Avg=0.5% | Max=25.0%
- **Uvicorn RAM**: Avg=118.6 MB | Max=141.5 MB
