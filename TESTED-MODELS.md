# Tested AS/400 models

One row per machine and test campaign. Add a new row when a test changes the result for a machine (new firmware, new device type, new OS release), rather than editing the old one, so the history stays visible.

**Result** values:
- **Works:** the tested operations completed without errors.
- **Works with settings:** works only with the settings listed in the machine page.
- **Partial:** some operations work, others fail.
- **Fails:** the device cannot be used.

## PowerPC (RISC), PCI

| Machine | OS release | Storage IOA | ZuluSCSI board | Firmware | Devices tested | Operations tested | Result | Date | Details |
|---|---|---|---|---|---|---|---|---|---|
| 9406-810 | V5R4M0 | see machine page | Wide (RP2350) | v2026.11.07 | Disk, profile `53P3239` | LIC install | **Fails**: SRC `A60B0266` at disk initialization | 2026-11-16 | [9406-810](machines/9406-810.md) |
| 9406-810 | V5R4M0 | see machine page | Wide (RP2350) | v2026.11.07 + Skip fix ([#1047](https://github.com/ZuluSCSI/ZuluSCSI-firmware/pull/1047)) | Disk, profile `53P3239` | LIC install, disk initialization | **Works with settings**: `MaxSyncSpeed = 10` | 2026-11-17 | [9406-810](machines/9406-810.md) |
| 9406-810 | V5R4M0 | see machine page | Wide (RP2350) | main 0271e11 + [#1047](https://github.com/ZuluSCSI/ZuluSCSI-firmware/pull/1047) + [#1050](https://github.com/ZuluSCSI/ZuluSCSI-firmware/pull/1050) (same code as v2026.11.17 without [#1048](https://github.com/ZuluSCSI/ZuluSCSI-firmware/pull/1048)) | Disk, profile `53P3239`, serial override | LIC install, disk initialization | **Works with settings**: `MaxSyncSpeed = 10`, blank image | 2026-11-18 | [9406-810](machines/9406-810.md) |
| 9401-150 | V4R4, V5R2 | not recorded | Wide | up to v2026.09.10 | Disk, CD-ROM | Disk use, raw partitions, IPL from CD | **Works** | by 2026-09-10 | upstream `README-as400.md` |
| 9406-270 | not recorded | not recorded | not recorded | not recorded | Disk | not recorded | **Fails**: SRC `A6000244`, contact lost with device | by 2026-09-10 | upstream `README-as400.md` |
| 9406-270 | not recorded | not recorded | not recorded | not recorded | CD-ROM | IPL from emulated CD | **Fails**: medium read error | by 2026-09-10 | upstream `README-as400.md` |

## PowerPC (RISC), SPD

No results recorded yet. The upstream guide lists SPD disk support as "Fails/Lack of feedback".

## CISC (IMPI)

| Machine | OS release | Storage IOA | ZuluSCSI board | Firmware | Devices tested | Operations tested | Result | Date | Details |
|---|---|---|---|---|---|---|---|---|---|
| 9401-P02 | V2R3 | not recorded | Blaster | up to v2026.09.10 | Disk, tape | Disk use, raw partitions | **Works** | by 2026-09-10 | upstream `README-as400.md` |
| 9401-P03 | not recorded | not recorded | Wide | up to v2026.09.10 | Disk, tape | not recorded | **Works** | by 2026-09-10 | upstream `README-as400.md` |

Rows marked "upstream `README-as400.md`" are taken from the "Current state" section of the [firmware's AS/400 guide](https://github.com/ZuluSCSI/ZuluSCSI-firmware/blob/main/README-as400.md) as of v2026.09.10. They have no machine page yet; fields that guide does not state are marked "not recorded".

## Known issues by symptom

| Symptom | Machines | Cause | Status |
|---|---|---|---|
| SRC `A60B0266` during "initialize disk" | 9406-810 | Linked Skip Write ended without a STATUS phase | Fixed in v2026.11.17 ([#1046](https://github.com/ZuluSCSI/ZuluSCSI-firmware/issues/1046)) |
| SRC `43263100` at the first write | 9406-810 | DATA OUT fails parity at 40 MB/s wide sync | Open ([#1058](https://github.com/ZuluSCSI/ZuluSCSI-firmware/issues/1058)); workaround `MaxSyncSpeed = 10` |
| Serial in DST differs from `AS400_DiskSerialNumber` | all | Short values were space-padded and the first digit replaced | Fixed in v2026.11.17 ([#1049](https://github.com/ZuluSCSI/ZuluSCSI-firmware/issues/1049)) |
| LIC install stops with error code 62 after a serial change | 9406-810 | Image still holds the old install; FORMAT UNIT does not erase it | Use a blank image after changing the serial |
| "A disk could not be found to be the load source" | 9406-810 | No SD card in the board | Insert the card |
