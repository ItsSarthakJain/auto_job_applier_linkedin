'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    26.01.20.5.08
'''

import re
import subprocess
from time import sleep

from modules.helpers import get_default_temp_profile, make_directories
from config.settings import (
    run_in_background,
    stealth_mode,
    disable_extensions,
    safe_mode,
    file_name,
    failed_file_name,
    logs_folder_path,
    generated_resume_path,
)
from config.questions import default_resume_path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException

from modules.helpers import find_default_profile_directory, critical_error_log, print_lg

try:
    import undetected_chromedriver as uc
except Exception:
    uc = None


def _get_chrome_major_version() -> int | None:
    chrome_commands = [
        ["google-chrome", "--version"],
        ["google-chrome-stable", "--version"],
        ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
    ]
    for cmd in chrome_commands:
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
            match = re.search(r"(\d+)\.", out)
            if match:
                return int(match.group(1))
        except Exception:
            continue
    return None


def _build_options(use_stealth: bool, user_data_dir: str) -> Options:
    options = uc.ChromeOptions() if (use_stealth and uc) else Options()
    if run_in_background:
        options.add_argument("--headless")
    if disable_extensions:
        options.add_argument("--disable-extensions")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    return options


def _create_driver(use_stealth: bool, options):
    if use_stealth:
        if not uc:
            raise RuntimeError("undetected_chromedriver is not available in this environment.")
        major = _get_chrome_major_version()
        print_lg("Downloading Chrome Driver... This may take some time. Undetected mode requires download every run!")
        if major:
            return uc.Chrome(options=options, version_main=major)
        return uc.Chrome(options=options)
    return webdriver.Chrome(options=options)


def createChromeSession() -> tuple[Options, webdriver.Chrome, ActionChains, WebDriverWait]:
    """
    Robust browser bootstrap:
    - Uses isolated profile dirs in safe mode to avoid stale lock conflicts.
    - Tries configured mode first, then deterministic fallback modes.
    - Captures detailed startup diagnostics.
    """
    make_directories([file_name, failed_file_name, logs_folder_path + "/screenshots", default_resume_path, generated_resume_path + "/temp"])
    print_lg("IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!")

    default_profile_dir = find_default_profile_directory()
    attempts: list[tuple[str, bool, bool]] = []

    # (name, use_stealth, use_default_profile)
    attempts.append(("configured-mode", stealth_mode, bool(default_profile_dir and not safe_mode)))
    attempts.append(("isolated-profile", stealth_mode, False))
    if stealth_mode:
        attempts.append(("selenium-fallback", False, bool(default_profile_dir and not safe_mode)))
        attempts.append(("selenium-isolated", False, False))

    startup_errors: list[str] = []
    for idx, (name, use_stealth, use_default_profile) in enumerate(attempts, start=1):
        user_data_dir = default_profile_dir if use_default_profile else get_default_temp_profile()
        if use_default_profile:
            print_lg(f"[Chrome Init] Attempt {idx}/{len(attempts)} using saved profile ({name}, stealth={use_stealth}).")
        else:
            print_lg(f"[Chrome Init] Attempt {idx}/{len(attempts)} using isolated profile ({name}, stealth={use_stealth}).")
        options = _build_options(use_stealth, user_data_dir)
        driver = None
        try:
            driver = _create_driver(use_stealth, options)
            driver.maximize_window()
            wait = WebDriverWait(driver, 5)
            actions = ActionChains(driver)
            print_lg(f"[Chrome Init] Success on attempt {idx} ({name}).")
            return options, driver, actions, wait
        except (SessionNotCreatedException, WebDriverException, TimeoutError, RuntimeError) as e:
            err = f"{name}: {type(e).__name__}: {e}"
            startup_errors.append(err)
            critical_error_log("Chrome startup attempt failed", e)
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
            # Short cool-down before next attempt to avoid immediate port/profile contention.
            sleep(1.0)
            continue

    all_errors = "\n".join(startup_errors[-6:])
    msg = (
        "Failed to start Chrome after multiple deterministic attempts.\n"
        "Please verify Chrome installation/version compatibility and close stale Chrome windows.\n\n"
        f"Startup errors:\n{all_errors}"
    )
    raise RuntimeError(msg)


options, driver, actions, wait = None, None, None, None
try:
    options, driver, actions, wait = createChromeSession()
except Exception as e:
    print_lg(str(e))
    critical_error_log("In Opening Chrome", e)
    from pyautogui import alert
    alert(str(e), "Error in opening chrome")
    try:
        if driver:
            driver.quit()
    except Exception:
        pass
    exit()
