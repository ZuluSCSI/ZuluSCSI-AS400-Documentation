#!/usr/bin/env python3
"""new-disk.py - bootstrap a supported-disks/<bucket>/<part>/ entry for an IBM AS/400 disk.

Workflow:
  1. Prompt for IBM part / IBM serial / manufacturer part / manufacturer serial
     (one prompt at a time, with explicit confirmation - barcode-scanner friendly).
  2. Read capacity via sg_readcap and pick the matching capacity bucket.
  3. Refuse if <root>/<bucket>/<ibm_part>/ already exists (unless --force).
  4. Create images/ and VPD/ skeletons and run tools/dump-vpd.sh into VPD/.
  5. Parse standard INQUIRY + VPD pages 0x80 / 0x83.
  6. Render README.md from supported-disks/TEMPLATE.md with parsed values
     substituted in and the file-list pruned to pages actually dumped.
  7. Write a zuluscsi.ini stub seeded from INQUIRY and capacity data.

Usage:
  sudo ./tools/new-disk.py /dev/sgX [--root supported-disks] [--bucket 35Gb] [--force]

Compatible with Python 3.2+ (Debian 7 ships python3.2).
"""

import argparse
import glob
import os
import re
import subprocess
import sys

REQUIRED_TOOLS = ["sg_inq", "sg_vpd", "sg_readcap"]

CAPACITY_BUCKETS_GB = [
    (1.0,   "1Gb"),
    (2.0,   "2Gb"),
    (4.0,   "4Gb"),
    (8.0,   "8Gb"),
    (17.0,  "17Gb"),
    (35.0,  "35Gb"),
    (70.0,  "70Gb"),
    (141.0, "141Gb"),
    (282.0, "282Gb"),
    (571.0, "571Gb"),
]

VPD_PAGE_DESCRIPTIONS = {
    "00": "supported VPD pages list",
    "03": "IBM firmware/build metadata (hex only)",
    "07": "block limits (legacy)",
    "80": "unit serial number",
    "83": "device identification (NAA / T10 vendor ID)",
    "89": "ATA information (if applicable)",
    "b0": "block limits (SBC)",
    "b1": "block device characteristics",
    "b2": "logical block provisioning",
    "c4": "IBM subsystem identifier / RDAC (hex only)",
    "d1": "IBM media disk definition (hex only)",
    "d2": "IBM additional vendor information (hex only)",
}


def die(msg, code=1):
    sys.stderr.write("error: {0}\n".format(msg))
    sys.exit(code)


def which(cmd):
    """Minimal shutil.which() replacement - shutil.which was added in Python 3.3."""
    if os.path.dirname(cmd):
        return cmd if os.access(cmd, os.X_OK) and os.path.isfile(cmd) else None
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, cmd)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def read_text(path):
    f = open(path, "r")
    try:
        return f.read()
    finally:
        f.close()


def write_text(path, content):
    f = open(path, "w")
    try:
        f.write(content)
    finally:
        f.close()


# ---------- args & prereqs ----------

def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(here)
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("device", help="SCSI device path, e.g. /dev/sg1 or /dev/sdb")
    p.add_argument("--root", default=os.path.join(project_root, "supported-disks"),
                   help="supported-disks root directory (default: %(default)s)")
    p.add_argument("--bucket", help="override auto-computed capacity bucket (e.g. 35Gb)")
    p.add_argument("--force", action="store_true",
                   help="overwrite destination if it already exists")
    p.add_argument("--template", default=os.path.join(project_root, "supported-disks", "TEMPLATE.md"),
                   help="path to TEMPLATE.md (default: %(default)s)")
    p.add_argument("--dump-script", default=os.path.join(here, "dump-vpd.sh"),
                   help="path to dump-vpd.sh (default: %(default)s)")
    return p.parse_args()


def check_prereqs(args):
    missing = [t for t in REQUIRED_TOOLS if not which(t)]
    if missing:
        die("missing tool(s) in PATH: {0} (install sg3_utils)".format(", ".join(missing)))
    if not os.path.exists(args.dump_script):
        die("dump script not found: {0}".format(args.dump_script))
    if not os.path.exists(args.template):
        die("template not found: {0}".format(args.template))


def check_device(device):
    if not os.path.exists(device):
        die("device '{0}' does not exist".format(device))
    if not os.access(device, os.R_OK):
        sys.stderr.write(
            "warning: '{0}' is not readable by current user; you probably need root\n".format(device))


# ---------- prompts ----------

def prompt_with_confirm(label):
    while True:
        try:
            value = input("{0}: ".format(label)).strip()
        except EOFError:
            die("input closed")
        if not value:
            print("  (empty - try again)")
            continue
        print("  -> captured: {0!r}".format(value))
        ans = input("  Press Enter to accept, or type 'r' + Enter to retry: ").strip().lower()
        if ans in ("", "y", "yes"):
            return value


def prompt_fields():
    print("")
    print("=== Disk identification ===")
    print("(scan or type each value; press Enter to confirm)")
    print("")
    return {
        "ibm_part":   prompt_with_confirm("IBM part number"),
        "ibm_serial": prompt_with_confirm("IBM disk serial number"),
        "mfr_part":   prompt_with_confirm("Manufacturer part number"),
        "mfr_serial": prompt_with_confirm("Manufacturer serial number"),
    }


# ---------- capacity ----------

def run_capture(cmd):
    """Run a command, return (returncode, stdout_text, stderr_text)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate()
    return proc.returncode, out or "", err or ""


def read_capacity(device):
    rc, out, err = run_capture(["sg_readcap", "--brief", device])
    if rc != 0:
        die("sg_readcap failed: {0}".format((err or out).strip()))
    parts = out.split()
    # sg_readcap --brief prints "<blocks> <block_size>" (hex, 0x-prefixed).
    # Some versions emit a 3-field variant; take blocks from the first field
    # and block_size from the last so both layouts work.
    if len(parts) < 2:
        die("unexpected sg_readcap --brief output: {0!r}".format(out))
    try:
        blocks = int(parts[0], 0)
        block_size = int(parts[-1], 0)
    except ValueError:
        die("could not parse sg_readcap --brief output: {0!r}".format(out))
    total_bytes = blocks * block_size
    return {
        "blocks":     blocks,
        "block_size": block_size,
        "bytes":      total_bytes,
        "gb":         total_bytes / 1e9,
        "gib":        total_bytes / (1 << 30),
    }


def pick_bucket(gb):
    return min(CAPACITY_BUCKETS_GB, key=lambda b: abs(b[0] - gb))[1]


# ---------- VPD dump ----------

def dump_vpd(device, vpd_dir, dump_script):
    print("\n=== Dumping VPD from {0} into {1} ===\n".format(device, vpd_dir))
    rc = subprocess.call(["bash", dump_script, device, vpd_dir])
    if rc != 0:
        die("dump-vpd.sh failed (exit {0})".format(rc))


# ---------- VPD parsers ----------

def _first(pat, text, flags=re.MULTILINE):
    m = re.search(pat, text, flags)
    return m.group(1).strip() if m else ""


def parse_inquiry(path):
    text = read_text(path) if os.path.exists(path) else ""

    info = {
        "vendor":      _first(r"^\s*Vendor identification:\s*(.+?)\s*$", text),
        "product":     _first(r"^\s*Product identification:\s*(.+?)\s*$", text),
        "revision":    _first(r"^\s*Product revision level:\s*(.+?)\s*$", text),
        "unit_serial": _first(r"^\s*Unit serial number:\s*(.+?)\s*$", text),
    }

    m = re.search(r"version=(0x[0-9a-fA-F]+)\s*\[([\w\-]+)\]", text)
    info["scsi_version_hex"]  = m.group(1) if m else ""
    info["scsi_version_name"] = m.group(2) if m else ""

    inquiry_block = re.split(r"length=", text, maxsplit=1)[0]
    features = []
    for key in ("Addr16", "WBus16", "Sync", "Linked", "CmdQue", "QAS", "IUS"):
        m = re.search(r"(?<!\w){0}=(\w+)".format(key), inquiry_block)
        if m and m.group(1) not in ("0", "0x0"):
            features.append(key)
    m = re.search(r"Clocking=(0x[0-9a-fA-F]+)", inquiry_block)
    if m:
        clk_label = {"0x0": "ST", "0x1": "ST", "0x2": "DT", "0x3": "DT"}.get(m.group(1), m.group(1))
        if m.group(1) != "0x0":
            features.append("Clocking={0}".format(clk_label))

    info["bus_features"] = features
    return info


def parse_page_80(path):
    if not os.path.exists(path):
        return ""
    return _first(r"Unit serial number:\s*(.+?)\s*$", read_text(path))


def parse_page_83(path):
    if not os.path.exists(path):
        return {"naa": "", "t10_vendor_id": ""}
    text = read_text(path)
    naa = ""
    m = re.search(r"designator type:\s*NAA[^\n]*\n\s*(0x[0-9a-fA-F]+)", text)
    if m:
        naa = m.group(1)
    t10 = ""
    m = re.search(
        r"designator type:\s*T10[^\n]*\n(?:[^\n]*\n)*?\s*vendor id:\s*(.+?)\s*$",
        text, re.MULTILINE,
    )
    if m:
        t10 = m.group(1).strip()
    return {"naa": naa, "t10_vendor_id": t10}


def list_dumped_pages(vpd_dir):
    pages = set()
    for f in glob.glob(os.path.join(vpd_dir, "page_*.bin")):
        stem = os.path.splitext(os.path.basename(f))[0]
        if stem == "page_00_supported":
            continue
        m = re.match(r"page_([0-9a-fA-F]+)$", stem)
        if m and os.path.getsize(f) > 0:
            pages.add(m.group(1).lower())
    return sorted(pages, key=lambda h: int(h, 16))


# ---------- README rendering ----------

def render_readme(template, ctx):
    out = template
    inq = ctx["inquiry"]

    # Title
    out = out.replace("# Disk `<PART_NUMBER>`", "# Disk `{0}`".format(ctx["ibm_part"]))

    # IBM fields
    out = re.sub(r"`<e\.g\. 39J3695>`",                       "`{0}`".format(ctx["ibm_part"]),   out)
    out = re.sub(r"`<11S\.\.\. full IBM serial label>`",      "`{0}`".format(ctx["ibm_serial"]), out)

    # Manufacturer fields
    out = re.sub(r"`<manufacturer part number from label>`",   "`{0}`".format(ctx["mfr_part"]),   out)
    out = re.sub(r"`<manufacturer serial number from label>`", "`{0}`".format(ctx["mfr_serial"]), out)
    cap_cell = "`{0:.2f} GB` (`{1:,} bytes`)".format(ctx["capacity_gb"], ctx["capacity_bytes"])
    out = re.sub(
        r"`<e\.g\. 35\.16 GB>`\s*\(`<raw bytes from READ CAPACITY>`\)",
        cap_cell.replace("\\", r"\\"),
        out,
    )
    sector_note = " (AS/400 native)" if ctx["block_size"] in (520, 522, 524) else ""
    out = re.sub(
        r"`<e\.g\. 522 bytes \(AS/400 native\)>`",
        "`{0} bytes{1}`".format(ctx["block_size"], sector_note),
        out,
    )
    out = re.sub(r"`<Working / Partial / Not working>`", "Untested", out)

    # Identification table
    out = re.sub(r"`<e\.g\. IBMAS400>`",         "`{0}`".format(inq["vendor"]),      out)
    out = re.sub(r"`<e\.g\. XCPR036>`",          "`{0}`".format(inq["product"]),     out)
    out = re.sub(r"`<e\.g\. S430>`",             "`{0}`".format(inq["revision"]),    out)
    out = re.sub(r"`<e\.g\. 00000000J3YRK5SK>`", "`{0}`".format(inq["unit_serial"]), out)
    if inq["scsi_version_hex"]:
        scsi_cell = "{0} (version `{1}`)".format(inq["scsi_version_name"], inq["scsi_version_hex"])
    else:
        scsi_cell = "TODO"
    out = re.sub(r"`<e\.g\. SPC-2 \(version 0x04\)>`", scsi_cell, out)
    bus_cell = ", ".join(inq["bus_features"]) if inq["bus_features"] else "TODO"
    out = re.sub(
        r"`<WBus16, Sync, CmdQue, Clocking=DT, QAS, IUS - describe what INQUIRY reports>`",
        bus_cell, out,
    )

    # VPD highlights - supported-pages line (omit 0x00, it's implicit; upper-case hex)
    advertised = [p for p in ctx["pages"] if p != "00"]
    if advertised:
        page_list_str = ", ".join("`0x{0}`".format(p.upper()) for p in advertised)
    else:
        page_list_str = "(none reported)"
    out = re.sub(
        r"Pages reported as supported by page `0x00`:\s*`<list>`\.",
        "Pages reported as supported by page `0x00`: {0}.".format(page_list_str),
        out,
    )

    # 0x80 serial bullet
    if ctx["page_80_serial"]:
        out = re.sub(
            r"\*\*Page 0x80 \(Unit serial number\):\*\*\s*`<value>`",
            "**Page 0x80 (Unit serial number):** `{0}`".format(ctx["page_80_serial"]),
            out,
        )

    # 0x83 NAA + T10 sub-bullets
    p83 = ctx["page_83"]
    naa_repl = "NAA: `{0}`".format(p83["naa"]) if p83["naa"] else "NAA: not present"
    out = re.sub(r'NAA:\s*`<\.\.\. or "not present">`', naa_repl, out)
    t10_repl = ("T10 vendor ID: `{0}`".format(p83["t10_vendor_id"])
                if p83["t10_vendor_id"] else "T10 vendor ID: not present")
    out = re.sub(r'T10 vendor ID:\s*`<\.\.\. or "not present">`', t10_repl, out)

    # Files in this folder - prune VPD bullets for pages we did not dump
    out = _prune_files_section(out, ctx["pages"])

    return out


def _prune_files_section(text, present_pages):
    present = set(present_pages)
    lines = text.split("\n")
    kept = []
    for line in lines:
        m = re.match(r"^\s*-\s*\[`page_([0-9a-fA-F]+)\.bin`\]", line)
        if m and m.group(1).lower() not in present:
            continue
        kept.append(line)
    return "\n".join(kept)


# ---------- zuluscsi.ini stub ----------

def write_zuluscsi_ini(path, ctx):
    inq = ctx["inquiry"]
    sector_note = "  ; AS/400 native" if ctx["block_size"] in (520, 522, 524) else ""
    content = (
        "# ZuluSCSI configuration stub for IBM AS/400 disk {ibm_part}\n"
        "# Generated by tools/new-disk.py - fill in TODOs and verify on hardware.\n"
        "\n"
        "[SCSI<id>]                ; replace <id> with the target SCSI ID (0..7 / 0..15)\n"
        "Vendor    = \"{vendor}\"\n"
        "Product   = \"{product}\"\n"
        "Version   = \"{revision}\"\n"
        "Serial    = \"{unit_serial}\"\n"
        "SectorSize = {block_size}{sector_note}\n"
        "# TODO: any additional ZuluSCSI options needed to emulate this drive on AS/400\n"
    ).format(
        ibm_part=ctx["ibm_part"],
        vendor=inq["vendor"],
        product=inq["product"],
        revision=inq["revision"],
        unit_serial=inq["unit_serial"],
        block_size=ctx["block_size"],
        sector_note=sector_note,
    )
    write_text(path, content)


# ---------- summary ----------

def print_summary(dest, fields, capacity, inq, pages):
    bar = "=" * 60
    print("")
    print(bar)
    print("Created {0}".format(dest))
    print(bar)
    print("  IBM part / serial      : {0} / {1}".format(fields["ibm_part"], fields["ibm_serial"]))
    print("  Manufacturer part / sn : {0} / {1}".format(fields["mfr_part"], fields["mfr_serial"]))
    print("  Capacity               : {0:.2f} GB ({1:,} bytes, {2} x {3})".format(
        capacity["gb"], capacity["bytes"], capacity["blocks"], capacity["block_size"]))
    print("  INQUIRY                : {0!r} / {1!r} / rev {2!r}".format(
        inq["vendor"], inq["product"], inq["revision"]))
    print("  VPD pages dumped       : {0}".format(
        ", ".join("0x" + p for p in pages) or "(none)"))
    print("")
    print("Next steps:")
    print("  - Drop front.png and back.png into {0}/images/".format(dest))
    print("  - Fill TODOs in {0}/README.md".format(dest))
    print("    (form factor, RPM, interface, IBM type/model, feature code,")
    print("     AS/400 models, IBM private-page decoding, notes)")
    print("  - Adjust {0}/zuluscsi.ini and verify on real hardware".format(dest))


# ---------- main ----------

def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def main():
    args = parse_args()
    check_prereqs(args)
    check_device(args.device)

    fields = prompt_fields()

    print("\n=== Reading capacity ===")
    capacity = read_capacity(args.device)
    bucket = args.bucket or pick_bucket(capacity["gb"])
    print("  -> {0:.2f} GB at {1} B/block -> bucket {2!r}".format(
        capacity["gb"], capacity["block_size"], bucket))

    dest = os.path.join(args.root, bucket, fields["ibm_part"])
    if os.path.exists(dest) and not args.force:
        die("destination already exists: {0} (use --force to overwrite)".format(dest))

    images_dir = os.path.join(dest, "images")
    vpd_dir = os.path.join(dest, "VPD")
    _ensure_dir(images_dir)
    _ensure_dir(vpd_dir)

    dump_vpd(args.device, vpd_dir, args.dump_script)

    inq = parse_inquiry(os.path.join(vpd_dir, "standard_inquiry.txt"))
    p83 = parse_page_83(os.path.join(vpd_dir, "page_83.txt"))
    p80_serial = parse_page_80(os.path.join(vpd_dir, "page_80.txt"))
    pages = list_dumped_pages(vpd_dir)

    ctx = dict(fields)
    ctx.update({
        "capacity_bytes": capacity["bytes"],
        "capacity_gb":    capacity["gb"],
        "block_size":     capacity["block_size"],
        "inquiry":        inq,
        "page_83":        p83,
        "page_80_serial": p80_serial,
        "pages":          pages,
    })

    template = read_text(args.template)
    write_text(os.path.join(dest, "README.md"), render_readme(template, ctx))

    write_zuluscsi_ini(os.path.join(dest, "zuluscsi.ini"), ctx)

    print_summary(dest, fields, capacity, inq, pages)


if __name__ == "__main__":
    main()
