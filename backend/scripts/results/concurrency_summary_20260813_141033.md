# Techonomy Read-Only Concurrency Baseline Test Summary
**Date/Time**: 2026-08-13 14:10:33
**Endpoint**: `http://localhost:8000/api/chat`
**Target Team**: `TEAM-01`
**Uvicorn Process PID**: `18954`

## Concurrency Benchmark Results Table

| Concurrency | Success | Failures | Timeouts | P50 (s) | P95 (s) | P99 (s) | Max (s) | Throughput (req/s) | Avg CPU (%) | Max RAM (MB) |
| ----------: | ------: | -------: | -------: | ------: | ------: | ------: | ------: | ----------------: | ----------: | -----------: |
| 1 | 0 | 1 | 1 | 90.007 | 90.007 | 90.007 | 90.007 | 0.000 | 0.5% | 141.5 MB |
| 5 | 5 | 0 | 0 | 22.189 | 22.197 | 22.197 | 22.197 | 0.225 | 1.9% | 107.8 MB |
| 10 | 10 | 0 | 0 | 1.681 | 1.691 | 1.691 | 1.691 | 5.798 | 4.2% | 117.8 MB |
| 25 | 15 | 10 | 0 | 21.151 | 24.138 | 25.116 | 25.116 | 0.597 | 2.0% | 145.3 MB |
| 50 | 15 | 35 | 0 | 23.173 | 23.285 | 23.296 | 23.296 | 0.642 | 1.3% | 150.6 MB |

## Per-Level Detailed Breakdown

### Concurrency Level: 1
- **Total Requests**: 1
- **Wall-Clock Time**: 90.038s
- **Status Codes**: {'TIMEOUT': 1}
- **PostgreSQL Connections**: Before=-1 | After=-1
- **Uvicorn CPU**: Avg=0.5% | Max=9.2%
- **Uvicorn RAM**: Avg=115.7 MB | Max=141.5 MB

### Concurrency Level: 5
- **Total Requests**: 5
- **Wall-Clock Time**: 22.236s
- **Status Codes**: {'200': 5}
- **PostgreSQL Connections**: Before=-1 | After=-1
- **Uvicorn CPU**: Avg=1.9% | Max=43.2%
- **Uvicorn RAM**: Avg=105.0 MB | Max=107.8 MB

### Concurrency Level: 10
- **Total Requests**: 10
- **Wall-Clock Time**: 1.725s
- **Status Codes**: {'200': 10}
- **PostgreSQL Connections**: Before=26 | After=-1
- **Uvicorn CPU**: Avg=4.2% | Max=6.6%
- **Uvicorn RAM**: Avg=117.6 MB | Max=117.8 MB

### Concurrency Level: 25
- **Total Requests**: 25
- **Wall-Clock Time**: 25.142s
- **Status Codes**: {'200': 15, '500': 10}
- **PostgreSQL Connections**: Before=26 | After=26
- **Uvicorn CPU**: Avg=2.0% | Max=24.2%
- **Uvicorn RAM**: Avg=127.1 MB | Max=145.3 MB

### Concurrency Level: 50
- **Total Requests**: 50
- **Wall-Clock Time**: 23.38s
- **Status Codes**: {'200': 15, '500': 35}
- **PostgreSQL Connections**: Before=25 | After=-1
- **Uvicorn CPU**: Avg=1.3% | Max=3.2%
- **Uvicorn RAM**: Avg=140.9 MB | Max=150.6 MB
