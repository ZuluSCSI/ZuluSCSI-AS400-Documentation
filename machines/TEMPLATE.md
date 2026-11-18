# IBM `<type>-<model>`

| Field | Value |
|---|---|
| Machine type-model | `<e.g. 9406-810>` |
| Processor feature | `<from DST, Processor Capacity>` |
| Architecture | `<CISC (IMPI) / PowerPC, SPD I/O / PowerPC, PCI I/O>` |
| Disk sector size | `<520 / 522>` bytes |
| OS release tested | `<e.g. V5R4M0>` |
| ZuluSCSI board | `<Wide / Blaster / RP2040 / ...>`, `<8 / 16>`-bit, termination `<enabled / disabled>` |
| SCSI ID used | `<id>` |
| Disk profile | `<AS400_DiskProfile value>` |
| Status | `<Works / Works with settings / Partial / Fails>` |

## Hardware configuration

From DST or SST, *Packaging Hardware Resources*. List at least the storage IOAs, the disk, optical and tape units, and which IOA and cable the ZuluSCSI is attached to.

| Description | Type-model | Resource | Card or device position |
|---|---|---|---|
| | | | |

## Firmware requirements

The oldest firmware release that works on this machine, and the fixes it depends on.

## Working configuration

```ini
[SCSI]
System = AS400_PPC

[SCSI<id>]
AS400_DiskProfile = "<profile>"
```

Explain every setting that differs from the defaults and why it is needed.

## SCSI behavior of this machine

From `zululog.txt` with debug logging on:

- **Bus negotiation:** WDTR width, SDTR period and offset offered by the host, and what ZuluSCSI answered.
- **Identification:** which INQUIRY allocation lengths and VPD pages the host reads.
- **Commands used**, including vendor commands such as Skip Read (`0xE8`) and Skip Write (`0xEA`).
- Anything unusual: linked commands, FORMAT UNIT, long polling phases.

## Known issues and SRC codes

| Symptom | Cause | What to do |
|---|---|---|
| | | |

## Test history

| Date | Firmware | Settings | Result |
|---|---|---|---|
| | | | |
