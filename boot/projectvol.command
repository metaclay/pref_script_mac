#!/usr/bin/env python3
"""
Converted from macOS shell script to Python.

Usage examples:
  python3 projectvol.py           # run in non-confirm mode (same as SKIP_CONFIRM="")
  python3 projectvol.py -c        # enable confirmation prompts (SKIP_CONFIRM="x")
  python3 projectvol.py -r        # print last mounted folder structure
  python3 projectvol.py -d        # print config data

Notes:
- This script mimics the original shell behavior as closely as possible.
- Uses subprocess to call macOS tools: security, sudo, diskutil, mount_smbfs, ping, mysides, df, ls, etc.
- You will likely be prompted for passwords; they are fetched from macOS Keychain when possible.

Test carefully before using in production; destructive operations (rm -r, sudo) are present.
"""

import os
import sys
import time
import getpass
import subprocess
from pathlib import Path

# ======= DEFAULT SETUP =======
VER = 2.5
LAN_CLAYNET = 0   # 1-USE CLANET ON SERVER , 0-LOCAL
LAN_PROJECT = 2   # 1-PROJECT LINK TO SERVER (LIVE) , 0-LOCAL, 2-AUTO-CHECK IN LAN_USER LIST
EXT = 1           # 1-USE EXTERNAL DRIVE, 0-USE SYSTEM(DESKTOP FOLDER)
LAN_PROJECT_ORIG = LAN_PROJECT

LAN_USER_LIST = ["andi"]

# SKIP_CONFIRM
# "" or 'y' or 'Y' TO SKIP SKIP_CONFIRMING (OR ANYTHING TO USE SKIP_CONFIRMING) - IT WILL NOT ASK TO SET THE VARS
SKIP_CONFIRM = ""   
# 1-ASK : IT WILL ASK EVERY VAR TO BE SETUP AT THE BEGINNING, 
ASK = 0          

# DEBUG
DEBUG = 0         # 1-SHOW MORE INFO, 0-HIDE INFO

# LOOP MAIN PROC WHEN FAILED TO MOUNT
MAX_RETRIES_MAIN_PROC = 10   # MAX RETRY for the WHOLE PROC LOOP
INTERVAL_MAIN_PROC = 1       # Delay for the WHOLE PROC LOOP (in second)

# LOOP PING
PING_TIMEOUT = 30            # Max total wait time in seconds (ping to server)
MAX_CONNECTION_CHECK = 3     # Max Connection retry (ping and mount to server)

# SERVER LIST
IPADDR_ARR = ["192.168.1.20"]

# KEYCHAIN ID
claynet_keychain_id = "c_claynet"
workstation_keychain_id = "c_workstation"

# ENV / PATHS
USER = os.environ.get("USER", "user")
EXT_DRIVE = "CLAY_EXT"
PROJECTVOL = "/Volumes/PROJECTVOL"
CLAY = ".__CLAY__"
USERSDIR = ".__USERS__"
HOME_LOCAL = f"/Users/{USER}"
HOME_EXT = f"/Volumes/{EXT_DRIVE}/{USERSDIR}/{USER}"
SHARED = "Shared"
HOME_LOCAL_PUB = f"/Users/{SHARED}"
HOME_EXT_PUB = f"/Volumes/{EXT_DRIVE}/{USERSDIR}/{SHARED}"
TEMPDIR = f"/Users/{USER}/{CLAY}/__TEMPDIR__"
RESULTFILE = f"/Users/{USER}/{CLAY}/folderlist.txt"

TITLE = \
f"""
=======================
PROJECTVOL SETUP v.{VER}
=======================
"""

# Globals for passwords (so we can reuse for sudo)
PASSWORD_SV = ""
PASSWORD_WK = ""


# ========================= UTILS =========================

def clear_screen():
    os.system("clear")


def run_cmd(cmd, check=True, capture_output=False, input_text=None):
    """Run a shell command via subprocess."""
    if capture_output:
        result = subprocess.run(
            cmd,
            text=True,
            input=input_text,
            capture_output=True
        )
    else:
        result = subprocess.run(
            cmd,
            text=True,
            input=input_text
        )

    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr if capture_output else ''}")
    return result


def run_sudo(cmd, password, check=True):
    """Run a sudo command, feeding password via stdin."""
    full_cmd = ["sudo", "-S"] + cmd
    result = subprocess.run(
        full_cmd,
        text=True,
        input=password + "\n",
        capture_output=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"sudo command failed: {' '.join(full_cmd)}\n{result.stderr}")
    return result


def ensure_dir(path: str, sudo_password=None):
    """Ensure directory exists, printing similar messages."""
    path_str = str(path)
    if not os.path.isdir(path_str):
        print(f"> create folder -> {path_str}", end="")
        try:
            os.makedirs(path_str, exist_ok=True)
        except PermissionError:
            if sudo_password:
                run_sudo(["mkdir", "-p", path_str], sudo_password)
            else:
                raise
        print("... OK")
    else:
        print(f"{path_str} ... OK")


def is_dir_effectively_empty(path: str, ignore=("._", ".DS_Store", "CLAYNET_SRC", "PROJECTS_SRC")) -> bool:
    """Check if folder is empty except for allowed patterns."""
    if not os.path.isdir(path):
        return True
    items = os.listdir(path)
    for name in items:
        # ignore matching exact names (.DS_Store, CLAYNET_SRC, PROJECTS_SRC)
        if name in ignore:
            continue
        return False
    return True


# ========================= PASSWORD SETUP =========================

def get_password_from_keychain(label: str) -> str:
    try:
        res = run_cmd(
            ["/usr/bin/security", "find-generic-password", "-l", label, "-w"],
            check=False,
            capture_output=True
        )
        if res.returncode == 0:
            pwd = res.stdout.strip()
            return pwd
        return ""
    except Exception:
        return ""


def password_setup():
    global PASSWORD_SV, PASSWORD_WK

    # PASS SERVER
    PASSWORD_SV = get_password_from_keychain(claynet_keychain_id)
    if not PASSWORD_SV:
        PASSWORD_SV = getpass.getpass("Enter your password for Claynet : ")

    # PASS WORKSTATION
    PASSWORD_WK = get_password_from_keychain(workstation_keychain_id)
    if not PASSWORD_WK:
        PASSWORD_WK = getpass.getpass("Enter your password for workstation : ")

    # random cmd to initialize/trigger sudo pwd
    print("Initializing sudo with workstation password...")
    run_sudo(["ls"], PASSWORD_WK, check=False)


# ========================= LAN_USER_LIST LOGIC =========================

def auto_set_lan_project():
    global LAN_PROJECT
    if LAN_PROJECT == 2:
        LAN_PROJECT = 0
        for u in LAN_USER_LIST:
            if u == USER:
                LAN_PROJECT = 1
                break


# ========================= ARGUMENTS =========================

def handle_args():
    global SKIP_CONFIRM

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "-c":
            SKIP_CONFIRM = "x"  # turn on confirmation

        if arg == "-r":
            print("RESULT :")
            print("----------")
            try:
                with open(RESULTFILE, "r") as f:
                    print(f.read(), end="")
            except FileNotFoundError:
                print("(No result file found)")
            print()
            sys.exit(1)

        if arg == "-d":
            print("DATA :")
            print("----------")
            print(f"LAN CLAYNET : {LAN_CLAYNET}")
            print(f"LAN PROJECT : {LAN_PROJECT}")
            print(f"EXT : {EXT}")
            print()
            sys.exit(1)

        if arg == "--help":
            programname = sys.argv[0]

            def usage():
                print(f"usage: {programname} [-crd]")
                print("  -c      Turn on confirmation")
                print("  -r      Show last mounted folder structure")
                print("  -d      Show data")
                print("  --help  Display help")
                print()
                sys.exit(1)

            usage()


# ========================= askme() =========================

def askme():
    global LAN_CLAYNET, LAN_PROJECT, EXT, ASK, SKIP_CONFIRM

    # PUSH DATA
    LAN_CLAYNET0 = LAN_CLAYNET
    LAN_PROJECT0 = LAN_PROJECT
    EXT0 = EXT

    # while [ -n "$SKIP_CONFIRM" ] && [ "$SKIP_CONFIRM" != "y" ] && [ "$SKIP_CONFIRM" != "Y" ]
    while SKIP_CONFIRM != "" and SKIP_CONFIRM not in ("y", "Y"):
        clear_screen()
        print(TITLE)
        print()

        if ASK == 1:
            # CLAYNET LAN
            while True:
                inp = input(f"CLAYNET LAN ({LAN_CLAYNET0}) ? ").strip()
                if inp == "":
                    LAN_CLAYNET = LAN_CLAYNET0
                    break
                elif inp in ("0", "1"):
                    LAN_CLAYNET = int(inp)
                    break
                else:
                    print("Please enter 0, 1, or press Enter to accept the default.")

            # PROJECTS LAN
            while True:
                inp = input(f"PROJECTS LAN ({LAN_PROJECT0}) ? ").strip()
                if inp == "":
                    LAN_PROJECT = LAN_PROJECT0
                    break
                elif inp in ("0", "1"):
                    LAN_PROJECT = int(inp)
                    break
                else:
                    print("Please enter 0, 1, or press Enter to accept the default.")

            # EXTERNAL DRIVE
            while True:
                inp = input(f"EXTERNAL DRIVE ({EXT0}) ? ").strip()
                if inp == "":
                    EXT = EXT0
                    break
                elif inp in ("0", "1"):
                    EXT = int(inp)
                    break
                else:
                    print("Please enter 0, 1, or press Enter to accept the default.")
        else:
            print(f"LAN CLAYNET : {LAN_CLAYNET}")
            print(f"LAN PROJECT : {LAN_PROJECT}")
            print(f"EXT : {EXT}")

        print()
        print(f"{LAN_CLAYNET} - {LAN_PROJECT} - {EXT}")
        SKIP_CONFIRM = input("SKIP_CONFIRM ? (Press Enter or type y to confirm): ").strip()

        if SKIP_CONFIRM != "" and SKIP_CONFIRM not in ("y", "Y"):
            ASK = 1
            LAN_CLAYNET = LAN_CLAYNET0
            LAN_PROJECT = LAN_PROJECT0
            EXT = EXT0

    clear_screen()
    print()
    print()


# ========================= unmount() =========================

def unmount():
    print(":::::::::::::::::::::::: INIT START ::::::::::::::::::::::::")
    print()
    print("Temp folder for mounting test ... ")
    print()

    # /Users/<USER>/.__CLAY__
    ensure_dir(os.path.join(HOME_LOCAL, CLAY))
    # /Users/Shared/.__CLAY__
    ensure_dir(os.path.join(HOME_LOCAL_PUB, CLAY))

    print()

    # TEMPDIR
    if not os.path.isdir(TEMPDIR):
        print(f"> mkdir {TEMPDIR}", end="")
        os.makedirs(TEMPDIR, exist_ok=True)
        print("... OK")
    else:
        print(f"{TEMPDIR} ... OK")

    # mounted_folders = df | awk '/CLAYNET/ { print $9 }'
    df_res = run_cmd(["df"], capture_output=True, check=False)
    mounted_folders = []
    for line in df_res.stdout.splitlines():
        if "CLAYNET" in line:
            parts = line.split()
            if parts:
                mounted_folders.append(parts[-1])  # mountpoint

    for mount_point in mounted_folders:
        print()
        print(f"> diskutil unmount {mount_point}")
        run_cmd(["diskutil", "unmount", mount_point], check=False)
        print("... OK")

    print()
    print(":::::::::::::::::::::::: INIT DONE ::::::::::::::::::::::::")
    clear_screen()
    print()
    print()


# ========================= header() =========================

def header():
    global LAN_CLAYNET, LAN_PROJECT, EXT

    LAN = LAN_CLAYNET + LAN_PROJECT
    loop_header = 1
    ipaddr = ""

    while loop_header == 1:
        clear_screen()
        print(TITLE)
        print(f"LAN CLAYNET : {LAN_CLAYNET}")
        print(f"LAN PROJECT : {LAN_PROJECT}")
        print(f"EXT : {EXT}")
        print()

        # Check external drive if needed
        if EXT == 1:
            if not os.path.isdir(f"/Volumes/{EXT_DRIVE}"):
                print()
                print(">>>>>> ERROR - NO EXTERNAL DRIVE !")
                print()
                uselocal = input("SWITCH TO LOCAL ? (Press Enter or type y to switch to local): ").strip()
                if uselocal == "" or uselocal.lower() == "y":
                    EXT = 0
                    print()
                    print()
                    print()
                    continue
                else:
                    print()
                    print(">>>>>> ERROR - NO EXTERNAL DRIVE !")
                    print()
                    sys.exit(1)

        if LAN > 0:
            print()
            print("      CHECKING LAN")
            print("----------------------------------------------------")

            IP_LEN = len(IPADDR_ARR)
            try_counter = 1
            max_check = MAX_CONNECTION_CHECK

            # PRINT LIST OF IP ADDRESS
            print(f"IP LIST ({IP_LEN}): ")
            for i in IPADDR_ARR:
                print(i)
            print()

            # GETTING IP ADDRESS OF ACTIVE/ONLINE SERVER
            tryagain = ""
            ipaddr = ""

            while ipaddr == "" and (tryagain == "" or tryagain.lower() == "y"):
                ip_counter = 1
                print()
                print(f"      CHECKING SERVER CONNECTION - TRY #{try_counter}")
                print("----------------------------------------------------")

                for i in IPADDR_ARR:
                    timeout = PING_TIMEOUT
                    interval = 2
                    start = time.time()
                    ping_ok = False

                    print(f"Server #{ip_counter}")

                    while True:
                        # ping -c1 -W1 -q <ip>
                        res = subprocess.run(
                            ["ping", "-c1", "-W1", "-q", i],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            text=True
                        )
                        if res.returncode == 0:
                            ping_ok = True
                            break

                        elapsed = time.time() - start
                        if elapsed >= timeout:
                            print(f"{i} -> Down")
                            break
                        time.sleep(interval)

                    if ping_ok:
                        ipaddr = i
                        print(f"{i} : PING OK")
                        mount_point = f"//{USER}:{PASSWORD_SV}@{ipaddr}/CLAYNET"
                        mount_point_clean = f"//{ipaddr}/CLAYNET"

                        # Test mount
                        cmd = ["mount_smbfs", mount_point, TEMPDIR]
                        test_res = subprocess.run(cmd, text=True)
                        if test_res.returncode == 0:
                            if DEBUG == 1:
                                mount_point_use = mount_point
                            else:
                                mount_point_use = mount_point_clean
                            print(f"MOUNT POINT {mount_point_use} --- OK")

                            # clean temp
                            if os.path.isdir(TEMPDIR):
                                subprocess.run(["diskutil", "unmount", TEMPDIR],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                text=True)
                            break
                        else:
                            ipaddr = ""
                            if DEBUG == 1:
                                print(f">>>>>> MOUNT POINT {mount_point} --- Fail or not available!")
                            else:
                                print(f">>>>>> MOUNT POINT {mount_point_clean} --- Fail or not available!")

                            if ip_counter == IP_LEN:
                                sys.exit(1)

                    ip_counter += 1
                    print()

                if ipaddr == "":
                    if try_counter < max_check:
                        tryagain = "y"
                    else:
                        tryagain = input("Try again  ? ").strip()

                try_counter += 1

            if ipaddr == "":
                print()
                print(">>>>>> ERROR - NO SERVER !")
                print()
                uselocalext = input("SKIP LAN ? (Press Enter or type y to skip): ").strip()
                if uselocalext == "" or uselocalext.lower() == "y":
                    LAN_CLAYNET = 0
                    LAN_PROJECT = 0
                    LAN = LAN_CLAYNET + LAN_PROJECT
                    print()
                    print()
                    continue
                else:
                    print()
                    print(">>>>>> ERROR - NO SERVER !")
                    print()
                    sys.exit(1)

        loop_header = 0

    return ipaddr


# ========================= CLEANUP HELPERS =========================

def remove_fail_linked_folders():
    print("      PROJECTVOL cleanup")
    print("----------------------------------------------------")

    fail_folder_arr = [
        f"{HOME_EXT}/{CLAY}/CLAYNET_SRC/CLAYNET_SRC",
        f"{HOME_LOCAL}/{CLAY}/CLAYNET_SRC/CLAYNET_SRC",
    ]

    for p in fail_folder_arr:
        if os.path.islink(p):
            print(f"> remove symlink ( FAIL LINKED FOLDER ) -> {p}", end="")
            run_sudo(["rm", p], PASSWORD_WK)
            print("... OK")
        else:
            if os.path.isdir(p):
                if is_dir_effectively_empty(p):
                    print(f"> remove folder ( FAIL LINKED FOLDER ) -> {p}", end="")
                    run_sudo(["rm", "-r", p], PASSWORD_WK)
                    print("... OK")
                else:
                    print(f"> Can't delete folder ( FAIL LINKED FOLDER ) -> {p}. Folder is not empty.")
            else:
                print(f"{p} ... SKIP - ( FAIL LINKED FOLDER ) does not exist.")

    print(f"> rmdir {TEMPDIR}", end="")
    try:
        os.rmdir(TEMPDIR)
        print("... OK")
    except OSError:
        print("... CAN'T REMOVE - SKIP")


def remove_projectvol_tree():
    projectvol_arr = [
        f"{PROJECTVOL}/localized/_Volumes/PROJECTVOL/CLAYNET",
        f"{PROJECTVOL}/localized/_Volumes/PROJECTVOL/CLAYNET/CLAYNET_SRC",
        f"{PROJECTVOL}",
        f"{HOME_LOCAL}/Desktop/PROJECTVOL",
        f"{HOME_EXT}/{CLAY}/PROJECTVOL_SRC/CLAYNET",
        f"{HOME_EXT}/{CLAY}/PROJECTVOL_SRC/CLAYNET/CLAYNET_SRC",
        f"{HOME_EXT}/{CLAY}/PROJECTVOL_SRC/projects",
        f"{HOME_LOCAL}/{CLAY}/PROJECTVOL_SRC/CLAYNET",
        f"{HOME_LOCAL}/{CLAY}/PROJECTVOL_SRC/projects",
        f"{HOME_EXT_PUB}/.__CLAY__/CLAYNET_SRC/CLAYNET_SRC",
        f"{HOME_LOCAL_PUB}/.__CLAY__/CLAYNET_SRC/CLAYNET_SRC",
    ]

    for p in projectvol_arr:
        if os.path.islink(p):
            print(f"> remove symlink -> {p}", end="")
            run_sudo(["rm", p], PASSWORD_WK)
            print("... OK")
        else:
            if os.path.isdir(p):
                if is_dir_effectively_empty(p):
                    print(f"> remove folder -> {p}", end="")
                    run_sudo(["rm", "-r", p], PASSWORD_WK)
                    print("... OK")
                else:
                    print(f"Can't delete folder -> {p}. Folder is not empty.")
            else:
                print(f"{p} ... SKIP - does not exist.")

    print(" ")
    print(" ")


# ========================= SYMLINK + MOUNT SETUP =========================

def setup_folders_and_mounts(ipaddr: str):
    """
    This is the big middle part: folder setup, cleanup, symlinks, mounts, result printing.
    """

    # ---- FOLDER SETUP ----
    print()
    print("      FOLDER SETUP")
    print("----------------------------------------------------")

    if EXT == 1:
        clay_home = f"{HOME_EXT}/{CLAY}"
        clay_home_pub = f"{HOME_EXT_PUB}/{CLAY}"
    else:
        clay_home = f"{HOME_LOCAL}/{CLAY}"
        clay_home_pub = f"{HOME_LOCAL_PUB}/{CLAY}"

    projectvol_src = f"{clay_home}/PROJECTVOL_SRC"

    if LAN_CLAYNET == 1:
        claynet_src = f"//{ipaddr}/CLAYNET"
    else:
        claynet_src = f"{clay_home_pub}/CLAYNET_SRC"

    if LAN_PROJECT == 1:
        projects_src = f"//{ipaddr}/CLAYNET/homes/{USER}/projects"
    else:
        projects_src = f"{clay_home}/PROJECTS_SRC"

    localized_claynet_src = f"{clay_home_pub}/CLAYNET_SRC"

    # /Volumes/EXT/.__USERS__/ & /Volumes/EXT/.__USERS__/<USER>/ & Shared
    if EXT == 1:
        ensure_dir(f"/Volumes/{EXT_DRIVE}/{USERSDIR}")
        ensure_dir(HOME_EXT)
        ensure_dir(HOME_EXT_PUB)

    # /__CLAY__ (home + shared)
    ensure_dir(clay_home)
    ensure_dir(clay_home_pub)

    # PROJECTVOL SRC
    ensure_dir(projectvol_src)

    # ROOT FOLDER (elements, localized, render)
    for folder_name in ("elements", "localized", "render"):
        ensure_dir(f"{projectvol_src}/{folder_name}")

    # CLAYNET_SRC AND PROJECT_SRC
    if LAN_CLAYNET == 0:
        ensure_dir(claynet_src)
    else:
        print(f"{claynet_src} ... OK")

    if LAN_PROJECT == 0:
        ensure_dir(projects_src)
    else:
        print(f"{projects_src} ... OK")

    # LOCALIZED
    ensure_dir(f"{projectvol_src}/localized/_Volumes")
    ensure_dir(f"{projectvol_src}/localized/_Volumes/PROJECTVOL")

    print(" ")
    print(" ")

    # ---- CLEANUP ----
    remove_fail_linked_folders()
    remove_projectvol_tree()

    # ---- SYMLINK TO /VOLUMES/PROJECTVOL ----
    print("      SYMLINK TO /VOLUMES/PROJECTVOL")
    print("----------------------------------------------------")
    print(f"> create symlink -> {projectvol_src} -> {PROJECTVOL}", end="")
    try:
        run_sudo(["ln", "-s", projectvol_src, PROJECTVOL], PASSWORD_WK)
    except RuntimeError:
        # If already exists or fail, raise to retry
        raise
    print("... OK")
    print(" ")
    print(" ")

    # ---- SYMLINK TO /VOLUMES/PROJECTVOL/LOCALIZED ----
    print("      SYMLINK TO /VOLUMES/PROJECTVOL/LOCALIZED")
    print("----------------------------------------------------")
    target_localized = f"{PROJECTVOL}/localized/_Volumes/PROJECTVOL/CLAYNET"
    print(f"> create symlink -> {localized_claynet_src} -> {target_localized}", end="")
    try:
        run_sudo(["ln", "-s", localized_claynet_src, target_localized], PASSWORD_WK)
    except RuntimeError:
        raise
    print("... OK")
    print(" ")
    print(" ")

    # ---- CLAYNET & PROJECTS ----
    print("      SYMLINK (OR MOUNT) TO CLAYNET & PROJECTS ")
    print("----------------------------------------------------")

    # CLAYNET
    claynet_mount_path = f"{projectvol_src}/CLAYNET"
    if LAN_CLAYNET == 1:
        if not os.path.isdir(claynet_mount_path):
            print(f"> create folder -> {claynet_mount_path}", end="")
            os.makedirs(claynet_mount_path, exist_ok=True)
            print("... OK")
        print(f"> mount -> //{USER}:*****@{ipaddr}/CLAYNET {claynet_mount_path}", end="")
        cmd = [
            "mount_smbfs",
            f"//{USER}:{PASSWORD_SV}@{ipaddr}/CLAYNET",
            claynet_mount_path,
        ]
        res = subprocess.run(cmd, text=True)
        if res.returncode != 0:
            raise RuntimeError("mount CLAYNET failed")
        print("... OK")
    else:
        print(f"> create symlink -> {claynet_src} -> {claynet_mount_path}", end="")
        try:
            run_sudo(["ln", "-s", claynet_src, claynet_mount_path], PASSWORD_WK)
        except RuntimeError:
            raise
        print("... OK")

    # PROJECTS
    projects_mount_path = f"{projectvol_src}/projects"
    if LAN_PROJECT == 1:
        if not os.path.isdir(projects_mount_path):
            print(f"> create folder -> {projects_mount_path}", end="")
            os.makedirs(projects_mount_path, exist_ok=True)
            print("... OK")
        print(f"> mount -> //{USER}:*****@{ipaddr}/CLAYNET/homes/{USER}/projects -> {projects_mount_path}", end="")
        cmd = [
            "mount_smbfs",
            f"//{USER}:{PASSWORD_SV}@{ipaddr}/CLAYNET/homes/{USER}/projects",
            projects_mount_path,
        ]
        res = subprocess.run(cmd, text=True)
        if res.returncode != 0:
            raise RuntimeError("mount projects failed")
        print("... OK")
    else:
        print(f"> create symlink -> {projects_src} -> {projects_mount_path} ", end="")
        try:
            run_sudo(["ln", "-s", projects_src, projects_mount_path], PASSWORD_WK)
        except RuntimeError:
            raise
        print("... OK")

    # SYMLINK TO /USER/__USER__/DESKTOP/PROJECTVOL
    desktop_link = f"{HOME_LOCAL}/Desktop/PROJECTVOL"
    print(f"> create symlink -> {PROJECTVOL} -> {desktop_link}", end="")
    res = subprocess.run(["ln", "-s", PROJECTVOL, desktop_link], text=True)
    if res.returncode != 0:
        raise RuntimeError("symlink to Desktop failed")
    print("... OK")
    print()
    print()

    # ---- RESULT ----
    lan = LAN_CLAYNET + LAN_PROJECT
    print(f"      MODE : {LAN_CLAYNET}-{LAN_PROJECT_ORIG}-{EXT}\n", end="")
    if EXT == 1:
        print("      PROJECTVOL : EXT\n", end="")
    else:
        print("      PROJECTVOL : INT\n", end="")
    if lan > 0:
        if LAN_CLAYNET == 1:
            print("      CLAYNET : LAN\n", end="")
        else:
            print("      CLAYNET : LOCAL\n", end="")
        if LAN_PROJECT == 1:
            print("      PROJECT : LAN", "(AUTO)" if LAN_PROJECT_ORIG==2 else "","\n",  end="")
        else:
            print("      PROJECT : LOCAL", "(AUTO)" if LAN_PROJECT_ORIG==2 else "", "\n",  end="")
        print(f"      SERVER/LAN : {ipaddr}")
    else:
        print("      NO SERVER/LAN\n")
    print("--------------------------------------------------------------------------------------")

    # Write RESULTFILE
    Path(RESULTFILE).parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTFILE, "w") as rf:
        # ls -ls /Volumes/PROJECTVOL | awk '{print $10 $11 $12}' | sed ...
        ls_res = subprocess.run(["ls", "-ls", PROJECTVOL], text=True, capture_output=True)
        for line in ls_res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 10:
                tail = "".join(parts[9:])
                tail = tail.replace("->", " -> ")
                rf.write(tail + "\n")
                print(tail)

        if lan > 0:
            if LAN_CLAYNET != 1:
                # ls -ls -d /Volumes/PROJECTVOL/* | grep -v ...
                ls_res = subprocess.run(
                    ["bash", "-lc",
                     f"ls -ls -d {PROJECTVOL}/* | grep -v 'projects\\|localized\\|elements\\|render\\|temp'"],
                    text=True,
                    capture_output=True
                )
                for line in ls_res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 10:
                        tail = "".join(parts[9:])
                        tail = tail.replace("->", " -> ")
                        rf.write(tail + "\n")
                        print(tail)

            # df | awk '/CLAYNET/ { print $9 " -> " $1 }'
            df_res = subprocess.run(["df"], text=True, capture_output=True)
            for line in df_res.stdout.splitlines():
                if "CLAYNET" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        mountpoint = parts[-1]
                        filesystem = parts[0]
                        s = f"{mountpoint} -> {filesystem}"
                        s = s.replace(f"CLAY_EXT/{USERSDIR}/{USER}/{CLAY}/PROJECTVOL_SRC", "PROJECTVOL")
                        s = s.replace(f"Users/{USER}/{CLAY}/PROJECTVOL_SRC", "Volumes/PROJECTVOL")
                        rf.write(s + "\n")
                        print(s)

            if LAN_PROJECT != 1:
                ls_res = subprocess.run(
                    ["bash", "-lc",
                     f"ls -ls -d {PROJECTVOL}/* | grep -v 'CLAYNET\\|localized\\|elements\\|render\\|temp'"],
                    text=True,
                    capture_output=True
                )
                for line in ls_res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 10:
                        tail = "".join(parts[9:])
                        tail = tail.replace("->", " -> ")
                        rf.write(tail + "\n")
                        print(tail)

            ls_res = subprocess.run(
                ["ls", "-ls", "-d", f"{PROJECTVOL}/localized/_Volumes/PROJECTVOL/CLAYNET"],
                text=True,
                capture_output=True
            )
            for line in ls_res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 10:
                    tail = "".join(parts[9:])
                    tail = tail.replace("->", " -> ")
                    rf.write(tail + "\n")
                    print(tail)

            # PARAM="CLAYNET\|projects\|localized"
            ls_res = subprocess.run(
                ["bash", "-lc",
                 f"ls -ls -d {PROJECTVOL}/* | grep -v 'CLAYNET\\|projects\\|localized'"],
                text=True,
                capture_output=True
            )
            for line in ls_res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 10:
                    tail = "".join(parts[9:])
                    rf.write(tail + "\n")
                    print(tail)

        else:
            # NO LAN branch
            ls_res = subprocess.run(
                ["bash", "-lc",
                 f"ls -ls -d {PROJECTVOL}/* | grep 'CLAYNET\\|projects'"],
                text=True,
                capture_output=True
            )
            for line in ls_res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 10:
                    tail = "".join(parts[9:])
                    tail = tail.replace("->", " -> ")
                    rf.write(tail + "\n")
                    print(tail)

            ls_res = subprocess.run(
                ["ls", "-ls", "-d", f"{PROJECTVOL}/localized/_Volumes/PROJECTVOL/CLAYNET"],
                text=True,
                capture_output=True
            )
            for line in ls_res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 10:
                    tail = "".join(parts[9:])
                    tail = tail.replace("->", " -> ")
                    rf.write(tail + "\n")
                    print(tail)

            ls_res = subprocess.run(
                ["bash", "-lc",
                 f"ls -ls -d {PROJECTVOL}/* | grep -v 'CLAYNET\\|projects' | grep -v 'localized'"],
                text=True,
                capture_output=True
            )
            for line in ls_res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 10:
                    tail = "".join(parts[9:])
                    rf.write(tail + "\n")
                    print(tail)

    # mysides updates
    subprocess.run(["mysides", "remove", "PROJECTVOL"],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,
                   text=True)
    subprocess.run(
        ["mysides", "add", "PROJECTVOL", f"file://{HOME_LOCAL}/Desktop/PROJECTVOL"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )

    print(" ")
    print(" ")
    print("----------------------------------------------------")
    print("      CLAYNET SETUP :: DONE ")
    print("----------------------------------------------------")
    print(" ")


# ========================= MAIN =========================

def main():
    global LAN_CLAYNET, LAN_PROJECT, EXT

    auto_set_lan_project()
    handle_args()
    password_setup()
    clear_screen()

    count = 0
    while count < MAX_RETRIES_MAIN_PROC:
        time.sleep(INTERVAL_MAIN_PROC)
        try:
            askme()
            unmount()
            ipaddr = header()
            setup_folders_and_mounts(ipaddr)
            break  # success
        except Exception as e:
            print("ERROR:", e)
            print("Retrying main procedure...")
            count += 1
            continue


if __name__ == "__main__":
    main()
