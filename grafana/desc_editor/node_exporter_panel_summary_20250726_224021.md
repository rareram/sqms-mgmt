# Node Exporter Full (1860) 대시보드 패널 분석 리포트
생성일시: 2025-07-26 22:40:21

## 📊 전체 요약
- 전체 패널 수: 132개
- 시각화 패널 수: 116개
- Row 패널 수: 16개

## 📝 Description 현황
- Description 있음: 28개 (24.1%)
- Description 없음: 88개 (75.9%)

## 📈 패널 타입별 분포
- bargauge: 1개 (0.9%)
- gauge: 5개 (4.3%)
- stat: 5개 (4.3%)
- timeseries: 105개 (90.5%)

## 📋 상세 패널 정보

### 1. Pressure (ID: 323)
- **패널 타입**: bargauge
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Resource pressure via PSI
- **Query 수**: 3개
  - Query 1: `irate(node_pressure_cpu_waiting_seconds_total{instance="$node",job="$job"}[$__ra...`
  - Query 2: `irate(node_pressure_memory_waiting_seconds_total{instance="$node",job="$job"}[$_...`
  - Query 3: `irate(node_pressure_io_waiting_seconds_total{instance="$node",job="$job"}[$__rat...`
- **Threshold**: 3개 설정됨

### 2. CPU Busy (ID: 20)
- **패널 타입**: gauge
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Busy state of all CPU cores together
- **Query 수**: 1개
  - Query 1: `100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle", instance="$node"}[$__rat...`
- **Threshold**: 3개 설정됨

### 3. Sys Load (ID: 155)
- **패널 타입**: gauge
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: System load  over all CPU cores together
- **Query 수**: 1개
  - Query 1: `scalar(node_load1{instance="$node",job="$job"}) * 100 / count(count(node_cpu_sec...`
- **Threshold**: 3개 설정됨

### 4. RAM Used (ID: 16)
- **패널 타입**: gauge
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Non available RAM memory
- **Query 수**: 2개
  - Query 1: `((node_memory_MemTotal_bytes{instance="$node", job="$job"} - node_memory_MemFree...`
  - Query 2: `(1 - (node_memory_MemAvailable_bytes{instance="$node", job="$job"} / node_memory...`
- **Threshold**: 3개 설정됨

### 5. SWAP Used (ID: 21)
- **패널 타입**: gauge
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Used Swap
- **Query 수**: 1개
  - Query 1: `((node_memory_SwapTotal_bytes{instance="$node",job="$job"} - node_memory_SwapFre...`
- **Threshold**: 3개 설정됨

### 6. Root FS Used (ID: 154)
- **패널 타입**: gauge
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Used Root FS
- **Query 수**: 1개
  - Query 1: `100 - ((node_filesystem_avail_bytes{instance="$node",job="$job",mountpoint="/",f...`
- **Threshold**: 3개 설정됨

### 7. CPU Cores (ID: 14)
- **패널 타입**: stat
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Total number of CPU cores
- **Query 수**: 1개
  - Query 1: `count(count(node_cpu_seconds_total{instance="$node",job="$job"}) by (cpu))`
- **Threshold**: 2개 설정됨

### 8. Uptime (ID: 15)
- **패널 타입**: stat
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: System uptime
- **Query 수**: 1개
  - Query 1: `node_time_seconds{instance="$node",job="$job"} - node_boot_time_seconds{instance...`
- **Threshold**: 2개 설정됨

### 9. RootFS Total (ID: 23)
- **패널 타입**: stat
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Total RootFS
- **Query 수**: 1개
  - Query 1: `node_filesystem_size_bytes{instance="$node",job="$job",mountpoint="/",fstype!="r...`
- **Threshold**: 3개 설정됨

### 10. RAM Total (ID: 75)
- **패널 타입**: stat
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Total RAM
- **Query 수**: 1개
  - Query 1: `node_memory_MemTotal_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 11. SWAP Total (ID: 18)
- **패널 타입**: stat
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Total SWAP
- **Query 수**: 1개
  - Query 1: `node_memory_SwapTotal_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 12. CPU Basic (ID: 77)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Basic CPU info
- **Query 수**: 6개
  - Query 1: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="system"}[$__...`
  - Query 2: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="user"}[$__ra...`
  - Query 3: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="iowait"}[$__...`
  - Query 4: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode=~".*irq"}[$__...`
  - Query 5: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job",  mode!='idle',mode...`
  - Query 6: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="idle"}[$__ra...`
- **Threshold**: 2개 설정됨

### 13. Memory Basic (ID: 78)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Basic memory usage
- **Query 수**: 5개
  - Query 1: `node_memory_MemTotal_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_MemTotal_bytes{instance="$node",job="$job"} - node_memory_MemFree_by...`
  - Query 3: `node_memory_Cached_bytes{instance="$node",job="$job"} + node_memory_Buffers_byte...`
  - Query 4: `node_memory_MemFree_bytes{instance="$node",job="$job"}`
  - Query 5: `(node_memory_SwapTotal_bytes{instance="$node",job="$job"} - node_memory_SwapFree...`
- **Threshold**: 2개 설정됨

### 14. Network Traffic Basic (ID: 74)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Basic network info per interface
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_bytes_total{instance="$node",job="$job"}[$__rate_inte...`
  - Query 2: `irate(node_network_transmit_bytes_total{instance="$node",job="$job"}[$__rate_int...`
- **Threshold**: 2개 설정됨

### 15. Disk Space Used Basic (ID: 152)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Disk space used of all filesystems mounted
- **Query 수**: 1개
  - Query 1: `100 - ((node_filesystem_avail_bytes{instance="$node",job="$job",device!~'rootfs'...`
- **Threshold**: 2개 설정됨

### 16. CPU (ID: 3)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 8개
  - Query 1: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="system"}[$__...`
  - Query 2: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="user"}[$__ra...`
  - Query 3: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="nice"}[$__ra...`
  - Query 4: `sum by(instance) (irate(node_cpu_seconds_total{instance="$node",job="$job", mode...`
  - Query 5: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="irq"}[$__rat...`
  - Query 6: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="softirq"}[$_...`
  - Query 7: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="steal"}[$__r...`
  - Query 8: `sum(irate(node_cpu_seconds_total{instance="$node",job="$job", mode="idle"}[$__ra...`
- **Threshold**: 2개 설정됨

### 17. Memory Stack (ID: 24)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 9개
  - Query 1: `node_memory_MemTotal_bytes{instance="$node",job="$job"} - node_memory_MemFree_by...`
  - Query 2: `node_memory_PageTables_bytes{instance="$node",job="$job"}`
  - Query 3: `node_memory_SwapCached_bytes{instance="$node",job="$job"}`
  - Query 4: `node_memory_Slab_bytes{instance="$node",job="$job"}`
  - Query 5: `node_memory_Cached_bytes{instance="$node",job="$job"}`
  - Query 6: `node_memory_Buffers_bytes{instance="$node",job="$job"}`
  - Query 7: `node_memory_MemFree_bytes{instance="$node",job="$job"}`
  - Query 8: `(node_memory_SwapTotal_bytes{instance="$node",job="$job"} - node_memory_SwapFree...`
  - Query 9: `node_memory_HardwareCorrupted_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 18. Network Traffic (ID: 84)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_bytes_total{instance="$node",job="$job"}[$__rate_inte...`
  - Query 2: `irate(node_network_transmit_bytes_total{instance="$node",job="$job"}[$__rate_int...`
- **Threshold**: 2개 설정됨

### 19. Disk Space Used (ID: 156)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_filesystem_size_bytes{instance="$node",job="$job",device!~'rootfs'} - node_...`
- **Threshold**: 2개 설정됨

### 20. Disk IOps (ID: 229)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_disk_reads_completed_total{instance="$node",job="$job",device=~"$disk...`
  - Query 2: `irate(node_disk_writes_completed_total{instance="$node",job="$job",device=~"$dis...`
- **Threshold**: 2개 설정됨

### 21. I/O Usage Read / Write (ID: 42)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_disk_read_bytes_total{instance="$node",job="$job",device=~"$diskdevic...`
  - Query 2: `irate(node_disk_written_bytes_total{instance="$node",job="$job",device=~"$diskde...`
- **Threshold**: 2개 설정됨

### 22. I/O Utilization (ID: 127)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_disk_io_time_seconds_total{instance="$node",job="$job",device=~"$disk...`
- **Threshold**: 2개 설정됨

### 23. CPU spent seconds in guests (VMs) (ID: 319)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `sum by(instance) (irate(node_cpu_guest_seconds_total{instance="$node",job="$job"...`
  - Query 2: `sum by(instance) (irate(node_cpu_guest_seconds_total{instance="$node",job="$job"...`
- **Threshold**: 2개 설정됨

### 24. Memory Active / Inactive (ID: 136)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_Inactive_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_Active_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 25. Memory Committed (ID: 135)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_Committed_AS_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_CommitLimit_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 26. Memory Active / Inactive Detail (ID: 191)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 4개
  - Query 1: `node_memory_Inactive_file_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_Inactive_anon_bytes{instance="$node",job="$job"}`
  - Query 3: `node_memory_Active_file_bytes{instance="$node",job="$job"}`
  - Query 4: `node_memory_Active_anon_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 27. Memory Writeback and Dirty (ID: 130)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_memory_Writeback_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_WritebackTmp_bytes{instance="$node",job="$job"}`
  - Query 3: `node_memory_Dirty_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 28. Memory Shared and Mapped (ID: 138)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 4개
  - Query 1: `node_memory_Mapped_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_Shmem_bytes{instance="$node",job="$job"}`
  - Query 3: `node_memory_ShmemHugePages_bytes{instance="$node",job="$job"}`
  - Query 4: `node_memory_ShmemPmdMapped_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 29. Memory Slab (ID: 131)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_SUnreclaim_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_SReclaimable_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 30. Memory Vmalloc (ID: 70)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_memory_VmallocChunk_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_VmallocTotal_bytes{instance="$node",job="$job"}`
  - Query 3: `node_memory_VmallocUsed_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 31. Memory Bounce (ID: 159)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_memory_Bounce_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 32. Memory Anonymous (ID: 129)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_AnonHugePages_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_AnonPages_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 33. Memory Kernel / CPU (ID: 160)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_KernelStack_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_Percpu_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 34. Memory HugePages Counter (ID: 140)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_memory_HugePages_Free{instance="$node",job="$job"}`
  - Query 2: `node_memory_HugePages_Rsvd{instance="$node",job="$job"}`
  - Query 3: `node_memory_HugePages_Surp{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 35. Memory HugePages Size (ID: 71)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_HugePages_Total{instance="$node",job="$job"}`
  - Query 2: `node_memory_Hugepagesize_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 36. Memory DirectMap (ID: 128)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_memory_DirectMap1G_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_DirectMap2M_bytes{instance="$node",job="$job"}`
  - Query 3: `node_memory_DirectMap4k_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 37. Memory Unevictable and MLocked (ID: 137)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_memory_Unevictable_bytes{instance="$node",job="$job"}`
  - Query 2: `node_memory_Mlocked_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 38. Memory NFS (ID: 132)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_memory_NFS_Unstable_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 39. Memory Pages In / Out (ID: 176)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_vmstat_pgpgin{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_vmstat_pgpgout{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 40. Memory Pages Swap In / Out (ID: 22)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_vmstat_pswpin{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_vmstat_pswpout{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 41. Memory Page Faults (ID: 175)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `irate(node_vmstat_pgfault{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_vmstat_pgmajfault{instance="$node",job="$job"}[$__rate_interval])`
  - Query 3: `irate(node_vmstat_pgfault{instance="$node",job="$job"}[$__rate_interval])  - ira...`
- **Threshold**: 2개 설정됨

### 42. OOM Killer (ID: 307)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_vmstat_oom_kill{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 43. Time Synchronized Drift (ID: 260)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_timex_estimated_error_seconds{instance="$node",job="$job"}`
  - Query 2: `node_timex_offset_seconds{instance="$node",job="$job"}`
  - Query 3: `node_timex_maxerror_seconds{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 44. Time PLL Adjust (ID: 291)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_timex_loop_time_constant{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 45. Time Synchronized Status (ID: 168)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_timex_sync_status{instance="$node",job="$job"}`
  - Query 2: `node_timex_frequency_adjustment_ratio{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 46. Time Misc (ID: 294)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_timex_tick_seconds{instance="$node",job="$job"}`
  - Query 2: `node_timex_tai_offset_seconds{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 47. Processes Status (ID: 62)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_procs_blocked{instance="$node",job="$job"}`
  - Query 2: `node_procs_running{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 48. Processes State (ID: 315)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Enable with --collector.processes argument on node-exporter
- **Query 수**: 1개
  - Query 1: `node_processes_state{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 49. Processes  Forks (ID: 148)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_forks_total{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 50. Processes Memory (ID: 149)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 4개
  - Query 1: `irate(process_virtual_memory_bytes{instance="$node",job="$job"}[$__rate_interval...`
  - Query 2: `process_resident_memory_max_bytes{instance="$node",job="$job"}`
  - Query 3: `irate(process_virtual_memory_bytes{instance="$node",job="$job"}[$__rate_interval...`
  - Query 4: `irate(process_virtual_memory_max_bytes{instance="$node",job="$job"}[$__rate_inte...`
- **Threshold**: 2개 설정됨

### 51. PIDs Number and Limit (ID: 313)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Enable with --collector.processes argument on node-exporter
- **Query 수**: 2개
  - Query 1: `node_processes_pids{instance="$node",job="$job"}`
  - Query 2: `node_processes_max_processes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 52. Process schedule stats Running / Waiting (ID: 305)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_schedstat_running_seconds_total{instance="$node",job="$job"}[$__rate_...`
  - Query 2: `irate(node_schedstat_waiting_seconds_total{instance="$node",job="$job"}[$__rate_...`
- **Threshold**: 2개 설정됨

### 53. Threads Number and Limit (ID: 314)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Enable with --collector.processes argument on node-exporter
- **Query 수**: 2개
  - Query 1: `node_processes_threads{instance="$node",job="$job"}`
  - Query 2: `node_processes_max_threads{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 54. Context Switches / Interrupts (ID: 8)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_context_switches_total{instance="$node",job="$job"}[$__rate_interval]...`
  - Query 2: `irate(node_intr_total{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 55. System Load (ID: 7)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_load1{instance="$node",job="$job"}`
  - Query 2: `node_load5{instance="$node",job="$job"}`
  - Query 3: `node_load15{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 56. CPU Frequency Scaling (ID: 321)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_cpu_scaling_frequency_hertz{instance="$node",job="$job"}`
  - Query 2: `avg(node_cpu_scaling_frequency_max_hertz{instance="$node",job="$job"})`
  - Query 3: `avg(node_cpu_scaling_frequency_min_hertz{instance="$node",job="$job"})`
- **Threshold**: 2개 설정됨

### 57. Pressure Stall Information (ID: 322)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: https://docs.kernel.org/accounting/psi.html
- **Query 수**: 5개
  - Query 1: `rate(node_pressure_cpu_waiting_seconds_total{instance="$node",job="$job"}[$__rat...`
  - Query 2: `rate(node_pressure_memory_waiting_seconds_total{instance="$node",job="$job"}[$__...`
  - Query 3: `rate(node_pressure_memory_stalled_seconds_total{instance="$node",job="$job"}[$__...`
  - Query 4: `rate(node_pressure_io_waiting_seconds_total{instance="$node",job="$job"}[$__rate...`
  - Query 5: `rate(node_pressure_io_stalled_seconds_total{instance="$node",job="$job"}[$__rate...`
- **Threshold**: 2개 설정됨

### 58. Interrupts Detail (ID: 259)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Enable with --collector.interrupts argument on node-exporter
- **Query 수**: 1개
  - Query 1: `irate(node_interrupts_total{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 59. Schedule timeslices executed by each cpu (ID: 306)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_schedstat_timeslices_total{instance="$node",job="$job"}[$__rate_inter...`
- **Threshold**: 2개 설정됨

### 60. Entropy (ID: 151)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_entropy_available_bits{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 61. CPU time spent in user and system contexts (ID: 308)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(process_cpu_seconds_total{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 62. File Descriptors (ID: 64)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `process_max_fds{instance="$node",job="$job"}`
  - Query 2: `process_open_fds{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 63. Hardware temperature monitor (ID: 158)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 5개
  - Query 1: `node_hwmon_temp_celsius{instance="$node",job="$job"} * on(chip) group_left(chip_...`
  - Query 2: `node_hwmon_temp_crit_alarm_celsius{instance="$node",job="$job"} * on(chip) group...`
  - Query 3: `node_hwmon_temp_crit_celsius{instance="$node",job="$job"} * on(chip) group_left(...`
  - Query 4: `node_hwmon_temp_crit_hyst_celsius{instance="$node",job="$job"} * on(chip) group_...`
  - Query 5: `node_hwmon_temp_max_celsius{instance="$node",job="$job"} * on(chip) group_left(c...`
- **Threshold**: 2개 설정됨

### 64. Throttle cooling device (ID: 300)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_cooling_device_cur_state{instance="$node",job="$job"}`
  - Query 2: `node_cooling_device_max_state{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 65. Power supply (ID: 302)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_power_supply_online{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 66. Systemd Sockets (ID: 297)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_systemd_socket_accepted_connections_total{instance="$node",job="$job"...`
- **Threshold**: 2개 설정됨

### 67. Systemd Units State (ID: 298)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 5개
  - Query 1: `node_systemd_units{instance="$node",job="$job",state="activating"}`
  - Query 2: `node_systemd_units{instance="$node",job="$job",state="active"}`
  - Query 3: `node_systemd_units{instance="$node",job="$job",state="deactivating"}`
  - Query 4: `node_systemd_units{instance="$node",job="$job",state="failed"}`
  - Query 5: `node_systemd_units{instance="$node",job="$job",state="inactive"}`
- **Threshold**: 2개 설정됨

### 68. Disk IOps Completed (ID: 9)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: The number (after merges) of I/O requests completed per second for the device
- **Query 수**: 2개
  - Query 1: `irate(node_disk_reads_completed_total{instance="$node",job="$job"}[$__rate_inter...`
  - Query 2: `irate(node_disk_writes_completed_total{instance="$node",job="$job"}[$__rate_inte...`
- **Threshold**: 2개 설정됨

### 69. Disk R/W Data (ID: 33)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: The number of bytes read from or written to the device per second
- **Query 수**: 2개
  - Query 1: `irate(node_disk_read_bytes_total{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_disk_written_bytes_total{instance="$node",job="$job"}[$__rate_interva...`
- **Threshold**: 2개 설정됨

### 70. Disk Average Wait Time (ID: 37)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: The average time for requests issued to the device to be served. This includes the time spent by the...
- **Query 수**: 2개
  - Query 1: `irate(node_disk_read_time_seconds_total{instance="$node",job="$job"}[$__rate_int...`
  - Query 2: `irate(node_disk_write_time_seconds_total{instance="$node",job="$job"}[$__rate_in...`
- **Threshold**: 2개 설정됨

### 71. Average Queue Size (ID: 35)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: The average queue length of the requests that were issued to the device
- **Query 수**: 1개
  - Query 1: `irate(node_disk_io_time_weighted_seconds_total{instance="$node",job="$job"}[$__r...`
- **Threshold**: 2개 설정됨

### 72. Disk R/W Merged (ID: 133)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: The number of read and write requests merged per second that were queued to the device
- **Query 수**: 2개
  - Query 1: `irate(node_disk_reads_merged_total{instance="$node",job="$job"}[$__rate_interval...`
  - Query 2: `irate(node_disk_writes_merged_total{instance="$node",job="$job"}[$__rate_interva...`
- **Threshold**: 2개 설정됨

### 73. Time Spent Doing I/Os (ID: 36)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Percentage of elapsed time during which I/O requests were issued to the device (bandwidth utilizatio...
- **Query 수**: 2개
  - Query 1: `irate(node_disk_io_time_seconds_total{instance="$node",job="$job"}[$__rate_inter...`
  - Query 2: `irate(node_disk_discard_time_seconds_total{instance="$node",job="$job"}[$__rate_...`
- **Threshold**: 2개 설정됨

### 74. Instantaneous Queue Size (ID: 34)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: The number of outstanding requests at the instant the sample was taken. Incremented as requests are ...
- **Query 수**: 1개
  - Query 1: `node_disk_io_now{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 75. Disk IOps Discards completed / merged (ID: 301)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_disk_discards_completed_total{instance="$node",job="$job"}[$__rate_in...`
  - Query 2: `irate(node_disk_discards_merged_total{instance="$node",job="$job"}[$__rate_inter...`
- **Threshold**: 2개 설정됨

### 76. Filesystem space available (ID: 43)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_filesystem_avail_bytes{instance="$node",job="$job",device!~'rootfs'}`
  - Query 2: `node_filesystem_free_bytes{instance="$node",job="$job",device!~'rootfs'}`
  - Query 3: `node_filesystem_size_bytes{instance="$node",job="$job",device!~'rootfs'}`
- **Threshold**: 2개 설정됨

### 77. File Nodes Free (ID: 41)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_filesystem_files_free{instance="$node",job="$job",device!~'rootfs'}`
- **Threshold**: 2개 설정됨

### 78. File Descriptor (ID: 28)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_filefd_maximum{instance="$node",job="$job"}`
  - Query 2: `node_filefd_allocated{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 79. File Nodes Size (ID: 219)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_filesystem_files{instance="$node",job="$job",device!~'rootfs'}`
- **Threshold**: 2개 설정됨

### 80. Filesystem in ReadOnly / Error (ID: 44)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_filesystem_readonly{instance="$node",job="$job",device!~'rootfs'}`
  - Query 2: `node_filesystem_device_error{instance="$node",job="$job",device!~'rootfs',fstype...`
- **Threshold**: 2개 설정됨

### 81. Network Traffic by Packets (ID: 60)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_packets_total{instance="$node",job="$job"}[$__rate_in...`
  - Query 2: `irate(node_network_transmit_packets_total{instance="$node",job="$job"}[$__rate_i...`
- **Threshold**: 2개 설정됨

### 82. Network Traffic Errors (ID: 142)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_errs_total{instance="$node",job="$job"}[$__rate_inter...`
  - Query 2: `irate(node_network_transmit_errs_total{instance="$node",job="$job"}[$__rate_inte...`
- **Threshold**: 2개 설정됨

### 83. Network Traffic Drop (ID: 143)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_drop_total{instance="$node",job="$job"}[$__rate_inter...`
  - Query 2: `irate(node_network_transmit_drop_total{instance="$node",job="$job"}[$__rate_inte...`
- **Threshold**: 2개 설정됨

### 84. Network Traffic Compressed (ID: 141)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_compressed_total{instance="$node",job="$job"}[$__rate...`
  - Query 2: `irate(node_network_transmit_compressed_total{instance="$node",job="$job"}[$__rat...`
- **Threshold**: 2개 설정됨

### 85. Network Traffic Multicast (ID: 146)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_network_receive_multicast_total{instance="$node",job="$job"}[$__rate_...`
- **Threshold**: 2개 설정됨

### 86. Network Traffic Fifo (ID: 144)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_network_receive_fifo_total{instance="$node",job="$job"}[$__rate_inter...`
  - Query 2: `irate(node_network_transmit_fifo_total{instance="$node",job="$job"}[$__rate_inte...`
- **Threshold**: 2개 설정됨

### 87. Network Traffic Frame (ID: 145)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_network_receive_frame_total{instance="$node",job="$job"}[$__rate_inte...`
- **Threshold**: 2개 설정됨

### 88. Network Traffic Carrier (ID: 231)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_network_transmit_carrier_total{instance="$node",job="$job"}[$__rate_i...`
- **Threshold**: 2개 설정됨

### 89. Network Traffic Colls (ID: 232)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_network_transmit_colls_total{instance="$node",job="$job"}[$__rate_int...`
- **Threshold**: 2개 설정됨

### 90. NF Conntrack (ID: 61)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_nf_conntrack_entries{instance="$node",job="$job"}`
  - Query 2: `node_nf_conntrack_entries_limit{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 91. ARP Entries (ID: 230)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_arp_entries{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 92. MTU (ID: 288)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_network_mtu_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 93. Speed (ID: 280)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_network_speed_bytes{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 94. Queue Length (ID: 289)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_network_transmit_queue_length{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 95. Softnet Packets (ID: 290)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_softnet_processed_total{instance="$node",job="$job"}[$__rate_interval...`
  - Query 2: `irate(node_softnet_dropped_total{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 96. Softnet Out of Quota (ID: 310)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_softnet_times_squeezed_total{instance="$node",job="$job"}[$__rate_int...`
- **Threshold**: 2개 설정됨

### 97. Network Operational Status (ID: 309)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_network_up{operstate="up",instance="$node",job="$job"}`
  - Query 2: `node_network_carrier{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 98. Sockstat TCP (ID: 63)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 5개
  - Query 1: `node_sockstat_TCP_alloc{instance="$node",job="$job"}`
  - Query 2: `node_sockstat_TCP_inuse{instance="$node",job="$job"}`
  - Query 3: `node_sockstat_TCP_mem{instance="$node",job="$job"}`
  - Query 4: `node_sockstat_TCP_orphan{instance="$node",job="$job"}`
  - Query 5: `node_sockstat_TCP_tw{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 99. Sockstat UDP (ID: 124)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_sockstat_UDPLITE_inuse{instance="$node",job="$job"}`
  - Query 2: `node_sockstat_UDP_inuse{instance="$node",job="$job"}`
  - Query 3: `node_sockstat_UDP_mem{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 100. Sockstat FRAG / RAW (ID: 125)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_sockstat_FRAG_inuse{instance="$node",job="$job"}`
  - Query 2: `node_sockstat_RAW_inuse{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 101. Sockstat Memory Size (ID: 220)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `node_sockstat_TCP_mem_bytes{instance="$node",job="$job"}`
  - Query 2: `node_sockstat_UDP_mem_bytes{instance="$node",job="$job"}`
  - Query 3: `node_sockstat_FRAG_memory{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 102. Sockstat Used (ID: 126)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_sockstat_sockets_used{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 103. Netstat IP In / Out Octets (ID: 221)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_netstat_IpExt_InOctets{instance="$node",job="$job"}[$__rate_interval]...`
  - Query 2: `irate(node_netstat_IpExt_OutOctets{instance="$node",job="$job"}[$__rate_interval...`
- **Threshold**: 2개 설정됨

### 104. Netstat IP Forwarding (ID: 81)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_netstat_Ip_Forwarding{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 105. ICMP In / Out (ID: 115)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_netstat_Icmp_InMsgs{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_netstat_Icmp_OutMsgs{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 106. ICMP Errors (ID: 50)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `irate(node_netstat_Icmp_InErrors{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 107. UDP In / Out (ID: 55)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_netstat_Udp_InDatagrams{instance="$node",job="$job"}[$__rate_interval...`
  - Query 2: `irate(node_netstat_Udp_OutDatagrams{instance="$node",job="$job"}[$__rate_interva...`
- **Threshold**: 2개 설정됨

### 108. UDP Errors (ID: 109)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 5개
  - Query 1: `irate(node_netstat_Udp_InErrors{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_netstat_Udp_NoPorts{instance="$node",job="$job"}[$__rate_interval])`
  - Query 3: `irate(node_netstat_UdpLite_InErrors{instance="$node",job="$job"}[$__rate_interva...`
  - Query 4: `irate(node_netstat_Udp_RcvbufErrors{instance="$node",job="$job"}[$__rate_interva...`
  - Query 5: `irate(node_netstat_Udp_SndbufErrors{instance="$node",job="$job"}[$__rate_interva...`
- **Threshold**: 2개 설정됨

### 109. TCP In / Out (ID: 299)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_netstat_Tcp_InSegs{instance="$node",job="$job"}[$__rate_interval])`
  - Query 2: `irate(node_netstat_Tcp_OutSegs{instance="$node",job="$job"}[$__rate_interval])`
- **Threshold**: 2개 설정됨

### 110. TCP Errors (ID: 104)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 8개
  - Query 1: `irate(node_netstat_TcpExt_ListenOverflows{instance="$node",job="$job"}[$__rate_i...`
  - Query 2: `irate(node_netstat_TcpExt_ListenDrops{instance="$node",job="$job"}[$__rate_inter...`
  - Query 3: `irate(node_netstat_TcpExt_TCPSynRetrans{instance="$node",job="$job"}[$__rate_int...`
  - Query 4: `irate(node_netstat_Tcp_RetransSegs{instance="$node",job="$job"}[$__rate_interval...`
  - Query 5: `irate(node_netstat_Tcp_InErrs{instance="$node",job="$job"}[$__rate_interval])`
  - Query 6: `irate(node_netstat_Tcp_OutRsts{instance="$node",job="$job"}[$__rate_interval])`
  - Query 7: `irate(node_netstat_TcpExt_TCPRcvQDrop{instance="$node",job="$job"}[$__rate_inter...`
  - Query 8: `irate(node_netstat_TcpExt_TCPOFOQueue{instance="$node",job="$job"}[$__rate_inter...`
- **Threshold**: 2개 설정됨

### 111. TCP Connections (ID: 85)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_netstat_Tcp_CurrEstab{instance="$node",job="$job"}`
  - Query 2: `node_netstat_Tcp_MaxConn{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 112. TCP SynCookie (ID: 91)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 3개
  - Query 1: `irate(node_netstat_TcpExt_SyncookiesFailed{instance="$node",job="$job"}[$__rate_...`
  - Query 2: `irate(node_netstat_TcpExt_SyncookiesRecv{instance="$node",job="$job"}[$__rate_in...`
  - Query 3: `irate(node_netstat_TcpExt_SyncookiesSent{instance="$node",job="$job"}[$__rate_in...`
- **Threshold**: 2개 설정됨

### 113. TCP Direct Transition (ID: 82)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `irate(node_netstat_Tcp_ActiveOpens{instance="$node",job="$job"}[$__rate_interval...`
  - Query 2: `irate(node_netstat_Tcp_PassiveOpens{instance="$node",job="$job"}[$__rate_interva...`
- **Threshold**: 2개 설정됨

### 114. TCP Stat (ID: 320)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ✅ 있음
- **Description**: Enable with --collector.tcpstat argument on node-exporter
- **Query 수**: 4개
  - Query 1: `node_tcp_connection_states{state="established",instance="$node",job="$job"}`
  - Query 2: `node_tcp_connection_states{state="fin_wait2",instance="$node",job="$job"}`
  - Query 3: `node_tcp_connection_states{state="listen",instance="$node",job="$job"}`
  - Query 4: `node_tcp_connection_states{state="time_wait",instance="$node",job="$job"}`
- **Threshold**: 1개 설정됨

### 115. Node Exporter Scrape Time (ID: 40)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 1개
  - Query 1: `node_scrape_collector_duration_seconds{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

### 116. Node Exporter Scrape (ID: 157)
- **패널 타입**: timeseries
- **데이터소스**: prometheus
- **Description 여부**: ❌ 없음
- **Query 수**: 2개
  - Query 1: `node_scrape_collector_success{instance="$node",job="$job"}`
  - Query 2: `node_textfile_scrape_error{instance="$node",job="$job"}`
- **Threshold**: 2개 설정됨

## ⚠️  Description이 없는 패널 목록

- **CPU** (ID: 3, Type: timeseries)
- **Memory Stack** (ID: 24, Type: timeseries)
- **Network Traffic** (ID: 84, Type: timeseries)
- **Disk Space Used** (ID: 156, Type: timeseries)
- **Disk IOps** (ID: 229, Type: timeseries)
- **I/O Usage Read / Write** (ID: 42, Type: timeseries)
- **I/O Utilization** (ID: 127, Type: timeseries)
- **CPU spent seconds in guests (VMs)** (ID: 319, Type: timeseries)
- **Memory Active / Inactive** (ID: 136, Type: timeseries)
- **Memory Committed** (ID: 135, Type: timeseries)
- **Memory Active / Inactive Detail** (ID: 191, Type: timeseries)
- **Memory Writeback and Dirty** (ID: 130, Type: timeseries)
- **Memory Shared and Mapped** (ID: 138, Type: timeseries)
- **Memory Slab** (ID: 131, Type: timeseries)
- **Memory Vmalloc** (ID: 70, Type: timeseries)
- **Memory Bounce** (ID: 159, Type: timeseries)
- **Memory Anonymous** (ID: 129, Type: timeseries)
- **Memory Kernel / CPU** (ID: 160, Type: timeseries)
- **Memory HugePages Counter** (ID: 140, Type: timeseries)
- **Memory HugePages Size** (ID: 71, Type: timeseries)
- **Memory DirectMap** (ID: 128, Type: timeseries)
- **Memory Unevictable and MLocked** (ID: 137, Type: timeseries)
- **Memory NFS** (ID: 132, Type: timeseries)
- **Memory Pages In / Out** (ID: 176, Type: timeseries)
- **Memory Pages Swap In / Out** (ID: 22, Type: timeseries)
- **Memory Page Faults** (ID: 175, Type: timeseries)
- **OOM Killer** (ID: 307, Type: timeseries)
- **Time Synchronized Drift** (ID: 260, Type: timeseries)
- **Time PLL Adjust** (ID: 291, Type: timeseries)
- **Time Synchronized Status** (ID: 168, Type: timeseries)
- **Time Misc** (ID: 294, Type: timeseries)
- **Processes Status** (ID: 62, Type: timeseries)
- **Processes  Forks** (ID: 148, Type: timeseries)
- **Processes Memory** (ID: 149, Type: timeseries)
- **Process schedule stats Running / Waiting** (ID: 305, Type: timeseries)
- **Context Switches / Interrupts** (ID: 8, Type: timeseries)
- **System Load** (ID: 7, Type: timeseries)
- **CPU Frequency Scaling** (ID: 321, Type: timeseries)
- **Schedule timeslices executed by each cpu** (ID: 306, Type: timeseries)
- **Entropy** (ID: 151, Type: timeseries)
- **CPU time spent in user and system contexts** (ID: 308, Type: timeseries)
- **File Descriptors** (ID: 64, Type: timeseries)
- **Hardware temperature monitor** (ID: 158, Type: timeseries)
- **Throttle cooling device** (ID: 300, Type: timeseries)
- **Power supply** (ID: 302, Type: timeseries)
- **Systemd Sockets** (ID: 297, Type: timeseries)
- **Systemd Units State** (ID: 298, Type: timeseries)
- **Disk IOps Discards completed / merged** (ID: 301, Type: timeseries)
- **Filesystem space available** (ID: 43, Type: timeseries)
- **File Nodes Free** (ID: 41, Type: timeseries)
- **File Descriptor** (ID: 28, Type: timeseries)
- **File Nodes Size** (ID: 219, Type: timeseries)
- **Filesystem in ReadOnly / Error** (ID: 44, Type: timeseries)
- **Network Traffic by Packets** (ID: 60, Type: timeseries)
- **Network Traffic Errors** (ID: 142, Type: timeseries)
- **Network Traffic Drop** (ID: 143, Type: timeseries)
- **Network Traffic Compressed** (ID: 141, Type: timeseries)
- **Network Traffic Multicast** (ID: 146, Type: timeseries)
- **Network Traffic Fifo** (ID: 144, Type: timeseries)
- **Network Traffic Frame** (ID: 145, Type: timeseries)
- **Network Traffic Carrier** (ID: 231, Type: timeseries)
- **Network Traffic Colls** (ID: 232, Type: timeseries)
- **NF Conntrack** (ID: 61, Type: timeseries)
- **ARP Entries** (ID: 230, Type: timeseries)
- **MTU** (ID: 288, Type: timeseries)
- **Speed** (ID: 280, Type: timeseries)
- **Queue Length** (ID: 289, Type: timeseries)
- **Softnet Packets** (ID: 290, Type: timeseries)
- **Softnet Out of Quota** (ID: 310, Type: timeseries)
- **Network Operational Status** (ID: 309, Type: timeseries)
- **Sockstat TCP** (ID: 63, Type: timeseries)
- **Sockstat UDP** (ID: 124, Type: timeseries)
- **Sockstat FRAG / RAW** (ID: 125, Type: timeseries)
- **Sockstat Memory Size** (ID: 220, Type: timeseries)
- **Sockstat Used** (ID: 126, Type: timeseries)
- **Netstat IP In / Out Octets** (ID: 221, Type: timeseries)
- **Netstat IP Forwarding** (ID: 81, Type: timeseries)
- **ICMP In / Out** (ID: 115, Type: timeseries)
- **ICMP Errors** (ID: 50, Type: timeseries)
- **UDP In / Out** (ID: 55, Type: timeseries)
- **UDP Errors** (ID: 109, Type: timeseries)
- **TCP In / Out** (ID: 299, Type: timeseries)
- **TCP Errors** (ID: 104, Type: timeseries)
- **TCP Connections** (ID: 85, Type: timeseries)
- **TCP SynCookie** (ID: 91, Type: timeseries)
- **TCP Direct Transition** (ID: 82, Type: timeseries)
- **Node Exporter Scrape Time** (ID: 40, Type: timeseries)
- **Node Exporter Scrape** (ID: 157, Type: timeseries)
