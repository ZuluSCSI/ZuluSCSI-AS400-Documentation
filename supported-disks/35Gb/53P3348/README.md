# Disk `53P3348`

<center>
<img width="48%" src="./images/front.png">
<img width="48%" src="./images/back.png">
</center>

## IBM fields

| Field             | Value                                  |
|-------------------|----------------------------------------|
| part number       | `53P3348`                       |
| serial number     | `11S97P3030YL902501A028`       |
| disk type code    | `<e.g. 4326>`                          |
| disk model code   | `<e.g. 050>`                           |
| feature code      | `<e.g. #6717, or N/A>`                 |
| AS/400 models     | `<supported systems / OS levels>`      |

## Manufacturer fields

| Field                       | Value                                            |
|-----------------------------|--------------------------------------------------|
| Manufacturer part number    | `9U9006-026`         |
| Manufacturer serial number  | `3HX29QVG`       |
| Capacity                    | `35.86 GB` (`35,858,276,352 bytes`) |
| Form factor                 | `<3.5" / 2.5" / SFF / LFF>`                     |
| Interface                   | `<e.g. SCA-2 80-pin Ultra320 SCSI (Wide LVD)>`  |
| Rotational speed            | `<e.g. 15,000 rpm>`                             |
| Sector size                 | `522 bytes (AS/400 native)`              |
| Status on ZuluSCSI          | Untested             |

## Identification (from standard INQUIRY)

| Field                  | Value                         |
|------------------------|-------------------------------|
| Vendor identification  | `IBMAS400`             |
| Product identification | `XCPR036`              |
| Product revision level | `1AEB`                 |
| Unit serial number     | `3HX29QVG000074463D4A`     |
| SCSI version           | SPC (version `0x03`) |
| Peripheral device type | disk                          |
| Bus features           | Addr16, WBus16, Sync, Linked, CmdQue, Clocking=DT |

> Note: AS/400 / OS/400 / IBM i requires a specific 8-character vendor string
> (e.g. `IBMAS400`, not `IBM     `) for the disk to be accepted as system DASD.
> Record the exact vendor ID returned and call out any deviation.

## VPD highlights

Pages reported as supported by page `0x00`: `0x03`, `0x80`, `0x81`, `0xC0`, `0xC1`, `0xC2`, `0xC3`, `0xC4`, `0xC7`, `0xC8`, `0xD1`, `0xD2`.

- **Page 0x80 (Unit serial number):** `3HX29QVG000074463D4A`
- **Page 0x83 (Device Identification):**
  - T10 vendor ID: not present
  - NAA: not present
- **Page 0x03 (ASCII information / IBM firmware metadata):** `<readable strings - build tag, build date, source path, etc.>`
- **Page 0xC4 (IBM subsystem identifier / RDAC):** `<decoded values, or note that sg_vpd does not decode it>`
- **Page 0xD1 (IBM Media Disk Definition):** `<readable identifiers>`
- **Page 0xD2 (IBM additional vendor information):** `<readable identifiers>`
- **Page 0xB0 / 0xB1 / 0xB2 (SBC block characteristics):** `<values, or note "not supported by this drive">`
- **Page 0x89 (ATA information):** `<values, or "N/A - SCSI-native drive">`

## ZuluSCSI configuration

See [`zuluscsi.ini`](./zuluscsi.ini) in this folder for an example configuration that emulates this drive on AS/400.

## Notes

- `<IBM type/model mapping, e.g. "4326-050 - 36 GB 15K RPM Ultra320 DASD for iSeries / pSeries">`
- `<vendor-string requirement and any other AS/400-specific quirks>`
- `<which optional VPD pages the drive does NOT implement - important for emulator parity>`
- `<observed AS/400 behavior, low-level format requirements, known incompatibilities, required firmware / patches>`

## Files in this folder

- `images/front.png`, `images/back.png` - photos of the physical drive
- `zuluscsi.ini` - example ZuluSCSI configuration to emulate this drive
- VPD:
  - [`standard_inquiry.bin`](VPD/standard_inquiry.bin)[`standard_inquiry.txt`](VPD/standard_inquiry.txt) - standard SCSI INQUIRY response
  - [`page_00.bin`](VPD/page_00.bin)[`page_00.txt`](VPD/page_00.txt) - supported VPD pages list
  - [`page_03.bin`](VPD/page_03.bin)[`page_03.txt`](VPD/page_03.txt) - IBM firmware/build metadata (hex only)
  - [`page_80.bin`](VPD/page_80.bin)[`page_80.txt`](VPD/page_80.txt) - unit serial number
  - [`page_c4.bin`](VPD/page_c4.bin)[`page_c4.txt`](VPD/page_c4.txt) - IBM subsystem identifier / RDAC (hex only)
  - [`page_d1.bin`](VPD/page_d1.bin)[`page_d1.txt`](VPD/page_d1.txt) - IBM media disk definition (hex only)
  - [`page_d2.bin`](VPD/page_d2.bin)[`page_d2.txt`](VPD/page_d2.txt) - IBM additional vendor information (hex only)
  - [`SUMMARY.txt`](VPD/SUMMARY.txt) - capture metadata (date, host, pages dumped)

> Remove rows for VPD pages that the specific drive does not expose, and add
> rows for any non-standard pages discovered during capture.
