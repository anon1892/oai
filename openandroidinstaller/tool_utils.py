"""This module contains functions to deal with tools like adb, fastboot and heimdall."""

# This file is part of OpenAndroidInstaller.
# OpenAndroidInstaller is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# OpenAndroidInstaller is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with OpenAndroidInstaller.
# If not, see <https://www.gnu.org/licenses/>."""
# Author: Tobias Sterbak

import sys
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, call, check_output, PIPE, run, CompletedProcess
from typing import Optional, List

import regex as re
from loguru import logger


PLATFORM = sys.platform


def run_command(tool: str, command: List[str], bin_path: Path) -> CompletedProcess:
    """Run a command with a tool (adb, fastboot, heimdall)."""
    if tool not in ["adb", "fastboot", "heimdall"]:
        raise Exception(f"Unknown tool {tool}. Use adb, fastboot or heimdall.")
    if PLATFORM == "win32":
        full_command = [str(bin_path + f"{tool}.exe")] + command
    else:
        full_command = [str(bin_path + f"{tool}")] + command

    logger.info(f"Run command: {full_command}")
    result = run(full_command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    # result contains result.returncode, result.stdout, result.stderr
    return result 


def adb_reboot(bin_path: Path) -> bool:
    """Run adb reboot on the device and return success."""
    logger.info("Rebooting device with adb.")
    result = run_command("adb", ["reboot"], bin_path)
    if result.returncode != 0:
        logger.info("Reboot failed.")
        return False
    return True


def adb_reboot_bootloader(bin_path: Path) -> bool:
    """Reboot the device into bootloader and return success."""
    logger.info("Rebooting device into bootloader with adb.")
    result = run_command("adb", ["reboot", "bootloader"], bin_path)
    if result.returncode != 0:
        logger.info("Reboot into bootloader failed.")
        return False
    # check if in fastboot mode
    result = run_command("fastboot", ["devices"], bin_path)
    if result.returncode != 0:
        logger.info("Reboot into bootloader failed.")
        logger.info(result.returncode)
        logger.info(result.stdout)
        logger.info(result.stderr)
        return False
    return True


def adb_reboot_download(bin_path: Path) -> bool:
    """Reboot the device into download mode of samsung devices and return success."""
    logger.info("Rebooting device into download mode with adb.")
    result = run_command("adb", ["reboot", "download"], bin_path)
    if result.returncode != 0:
        logger.info("Reboot into download mode failed.")
        return False
    # check if in download mode with heimdall?
    return True



def adb_sideload(bin_path: Path, target: str) -> bool:
    """Sideload the target to device and return success."""
    logger.info("Rebooting device into bootloader with adb.")
    result = run_command("adb", ["sideload", target], bin_path)
    if result.returncode != 0:
        logger.info(f"Sideloading {target} failed.")
        return False
    return True


def call_tool_with_command(command: str, bin_path: Path) -> bool:
    """Call an executable with a specific command."""
    if PLATFORM == "win32":
        command = re.sub(
            r"^adb", re.escape(str(bin_path.joinpath(Path("adb")))) + ".exe", command
        )
        command = re.sub(
            r"^fastboot",
            re.escape(str(bin_path.joinpath(Path("fastboot.exe")))) + ".exe",
            command,
        )
        command = re.sub(
            r"^heimdall",
            re.escape(str(bin_path.joinpath(Path("heimdall.exe")))) + ".exe",
            command,
        )
    else:
        command = re.sub(
            r"^adb", re.escape(str(bin_path.joinpath(Path("adb")))), command
        )
        command = re.sub(
            r"^fastboot", re.escape(str(bin_path.joinpath(Path("fastboot")))), command
        )
        command = re.sub(
            r"^heimdall", re.escape(str(bin_path.joinpath(Path("heimdall")))), command
        )

    logger.info(f"Run command: {command}")
    res = call(f"{command}", shell=True)
    if res == 0:
        logger.info("Success.")
        return True
    logger.info(f"Command {command} failed.")
    return False


def search_device(platform: str, bin_path: Path) -> Optional[str]:
    """Search for a connected device."""
    logger.info(f"Search devices on {platform} with {bin_path}...")
    try:
        # read device properties
        # TODO: This is not windows ready...
        if platform in ("linux", "darwin"):
            output = check_output(
                [
                    str(bin_path.joinpath(Path("adb"))),
                    "shell",
                    "getprop",
                    "|",
                    "grep",
                    "ro.product.device",
                ],
                stderr=STDOUT,
            ).decode()
        elif platform in ("windows", "win32"):
            output = check_output(
                [
                    str(bin_path.joinpath(Path("adb.exe"))),
                    "shell",
                    "getprop",
                    "|",
                    "findstr",
                    "ro.product.device",
                ],
                stderr=STDOUT,
                shell=True,
            ).decode()
        else:
            raise Exception(f"Unknown platform {platform}.")
        device_code = output.split("[")[-1].strip()[:-1].strip()
        logger.info(device_code)
        return device_code
    except CalledProcessError:
        logger.info(f"Did not detect a device.")
        return None
