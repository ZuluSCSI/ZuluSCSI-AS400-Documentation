# ZuluSCSI on IBM AS/400, iSeries and System i

This repository collects field results and reference data for running [ZuluSCSI](https://github.com/ZuluSCSI/ZuluSCSI-firmware) boards as disk, optical and tape devices on IBM midrange systems.

The firmware's own AS/400 guide, [`README-as400.md`](https://github.com/ZuluSCSI/ZuluSCSI-firmware/blob/main/README-as400.md), documents every configuration key. This repository adds what that guide does not keep: which machines were tested, with which firmware and settings, what failed, and the identity data captured from real IBM drives.

## Contents

| Path | What it holds |
|---|---|
| [`TESTED-MODELS.md`](TESTED-MODELS.md) | One row per tested machine: OS release, ZuluSCSI board, firmware, devices, result |
| [`machines/`](machines/) | One page per machine type with what is specific to it: storage IOAs, SCSI behavior, required settings, SRC codes seen, working `zuluscsi.ini` |
| [`supported-disks/`](supported-disks/) | Real IBM drives captured for emulation, grouped by capacity: identity fields, VPD dumps, example `zuluscsi.ini` |
| [`tools/`](tools/) | Scripts to dump VPD pages from a real drive and create a new `supported-disks/` entry |

## Getting started

1. **Use a current firmware.** PowerPC machines need at least **v2026.11.17**. Older releases fail the LIC install's disk initialization (SRC `A60B0266`) because they mishandle the linked AS/400 Skip Write command. Check [`TESTED-MODELS.md`](TESTED-MODELS.md) for the release tested on your machine.
2. **Pick the system preset** in `[SCSI]`: `System = AS400_PPC` for PowerPC (RISC) machines with 522-byte sectors, `System = AS400_CISC` for IMPI machines with 520-byte sectors.
3. **Pick a disk profile** per SCSI ID with `AS400_DiskProfile`. The profile carries the INQUIRY, VPD and mode page data of a real drive, so OS/400 accepts the unit. Built-in profiles are listed in `as400_disk_definitions.txt` in the firmware repository.
4. **Give each disk its own serial** with `AS400_DiskSerialNumber` when a profile is used more than once. Use 8 hex digits starting with `0`, for example `01000001`.
5. **Check the machine page** in [`machines/`](machines/) for settings your machine needs, such as a speed limit.

A minimal PowerPC load source configuration:

```ini
[SCSI]
System = AS400_PPC

[SCSI6]
AS400_DiskProfile = "09L4044"
PrefetchBytes = 4160
```

## Things that apply to every machine

- **Changing a disk's serial makes it a new unit.** OS/400 identifies a disk by its serial. If you change `AS400_DiskSerialNumber` on an image that already holds data, the system formats it as a new unit. ZuluSCSI's FORMAT UNIT does not erase the image, so the old contents stay and the install that follows can fail. Start from a blank image whenever the serial changes.
- **The SD card must stay in the board.** Without a card, the board presents no disk, and the AS/400 reports that no disk could be found to be the load source. The board's USB serial console shows `No SD card detected` in that case.
- **Turn on debug logging while testing.** Set the debug DIP switch (or `Debug = Yes`). `zululog.txt` on the card then records every command, status and parity error, which is what a bug report needs. Turn it off for normal use, since it slows the board down.

## Reporting a result

To add a machine:

1. Add a row to [`TESTED-MODELS.md`](TESTED-MODELS.md).
2. Copy [`machines/TEMPLATE.md`](machines/TEMPLATE.md) to `machines/<type>-<model>.md` and fill it in.
3. If a disk was captured from the machine, add it under [`supported-disks/`](supported-disks/) with `tools/new-disk.py`.

Firmware bugs go to the [firmware issue tracker](https://github.com/ZuluSCSI/ZuluSCSI-firmware/issues), with the board, firmware version and git hash, the machine type-model and OS release, the SRC, and the relevant part of `zululog.txt`.
