
Example of using the new-disk.py script:

```
oot@scsi-station:~# python3 new-disk.py /dev/sg1 --template TEMPLATE.md --dump-script dump-vpd.sh 

=== Disk identification ===
(scan or type each value; press Enter to confirm)

IBM part number: 53P3348
  -> captured: '53P3348'
  Press Enter to accept, or type 'r' + Enter to retry: 
IBM disk serial number: 11S97P3030YL902501A028
  -> captured: '11S97P3030YL902501A028'
  Press Enter to accept, or type 'r' + Enter to retry: 
Manufacturer part number: 9U9006-026
  -> captured: '9U9006-026'
  Press Enter to accept, or type 'r' + Enter to retry: 
Manufacturer serial number: 3HX29QVG
  -> captured: '3HX29QVG'
  Press Enter to accept, or type 'r' + Enter to retry: 

=== Reading capacity ===
  -> 35.86 GB at 522 B/block -> bucket '35Gb'

=== Dumping VPD from /dev/sg1 into /supported-disks/35Gb/53P3348/VPD ===

[*] Dumping VPD pages of /dev/sg1 into /supported-disks/35Gb/53P3348/VPD/
[*] Standard INQUIRY -> standard_inquiry.txt
[*] Reading Supported VPD Pages (0x00)
[*] Device advertises 15 VPD page(s): 0x0d 0x00 0x03 0x80 0x81 0xc0 0xc1 0xc2 0xc3 0xc4 0xc7 0xc8 0xd1 0x10 0xd2
    - 0x0d
    - 0x00
    - 0x03
    - 0x80
    - 0x81
    - 0xc0
    - 0xc1
    - 0xc2
    - 0xc3
    - 0xc4
    - 0xc7
    - 0xc8
    - 0xd1
    - 0x10
    - 0xd2
[+] Done. Files in /supported-disks/35Gb/53P3348/VPD/

============================================================
Created /supported-disks/35Gb/53P3348
============================================================
  IBM part / serial      : 53P3348 / 11S97P3030YL902501A028
  Manufacturer part / sn : 9U9006-026 / 3HX29QVG
  Capacity               : 35.86 GB (35,858,276,352 bytes, 68694016 x 522)
  INQUIRY                : 'IBMAS400' / 'XCPR036' / rev '1AEB'
  VPD pages dumped       : 0x00, 0x03, 0x80, 0x81, 0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc7, 0xc8, 0xd1, 0xd2

Next steps:
  - Drop front.png and back.png into /supported-disks/35Gb/53P3348/images/
  - Fill TODOs in /supported-disks/35Gb/53P3348/README.md
    (form factor, RPM, interface, IBM type/model, feature code,
     AS/400 models, IBM private-page decoding, notes)
  - Adjust /supported-disks/35Gb/53P3348/zuluscsi.ini and verify on real hardware
```