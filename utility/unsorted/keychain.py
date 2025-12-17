import os
import getpass
import subprocess
import sys

def get_current_username():
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USERNAME") or os.environ.get("USER")

def key_exists(service, account):
    if os.name == "posix":  # macOS / Linux
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    elif os.name == "nt":  # Windows
        result = subprocess.run(
            ["cmdkey", "/list:" + service],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        return service.lower() in result.stdout.decode().lower()
    return False

def add_to_keychain(service):
    account = get_current_username()

    print("🔐 Adding keychain for user : " + account )
    # Check if entry already exists
    if key_exists(service, account):
        choice = input(f"⚠️ Keychain entry for {account}@{service} already exists. Replace? (y/N): ").strip().lower()
        if choice != "y":
            print(f"⏭️ Skipping {service}")
            return

    # Ask user for password
    password = getpass.getpass(prompt=f"Enter password for {account}@{service}: ")

    if os.name == "posix":  # macOS / Linux
        subprocess.run([
            "security", "add-generic-password",
            "-a", account,
            "-s", service,
            "-w", password,
            "-U"  # update if exists
        ], check=True)
    elif os.name == "nt":  # Windows
        subprocess.run([
            "cmdkey", "/add:" + service, "/user:" + account, "/pass:" + password
        ], check=True)

    print(f"✅ Password stored in keychain/credential manager for {account}@{service}")

# Example usage
add_to_keychain("c_workstation")
add_to_keychain("c_claynet")
