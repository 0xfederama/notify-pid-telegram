import asyncio
import json
import os
import psutil
import time
import argparse
from telegram import Bot


def is_process_running(pid):
    """Check if a process with the given PID is running."""
    return psutil.pid_exists(pid)


def resolve_job_to_pid(job_str):
    """Resolve a job number (e.g., %1) to its corresponding PID."""
    job_id = int(job_str.strip("%")) - 1  # Convert to zero-based index
    current_shell_pid = (
        os.getppid()
    )  # Get the parent process ID (assuming it’s the shell)

    # Get the list of child processes of the current shell, sorted by start time
    child_procs = sorted(
        (
            p
            for p in psutil.Process(current_shell_pid).children()
            if p.status() == psutil.STATUS_RUNNING
        ),
        key=lambda p: p.create_time(),
    )

    try:
        # Get the PID of the job with the given job number
        return child_procs[job_id].pid
    except IndexError:
        # Job number is out of range
        return None


def get_process_info(pid):
    """Retrieve information about the process with the given PID."""
    try:
        process = psutil.Process(pid)
        with process.oneshot():
            # Gathering process information
            status = process.status()
            cpu_times = process.cpu_times()
            memory_info = process.memory_info()
            create_time = process.create_time()

        return {
            "status": status,
            "cpu_times": cpu_times,
            "memory_info": memory_info,
            "create_time": create_time,
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


async def send_telegram_message(bot_token, chat_id, message):
    """Send a message to a specified chat ID using the provided bot token."""
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message)


async def main(pid_or_job):
    print("main")
    """Monitor the process identified by either a PID or job number and send a message when it exits."""
    # Check if the input is a job number (starts with '%')
    if pid_or_job.startswith("%"):
        pid = resolve_job_to_pid(pid_or_job)
        if pid is None:
            print("NONE")
            return  # Exit if we cannot resolve the job number to a PID
    else:
        pid = int(pid_or_job)

    print(f"Monitoring process {pid}...")
    process_info = get_process_info(pid)
    cmdline = None

    if process_info:
        try:
            p = psutil.Process(pid)
            # Get the command line that started the process
            cmdline = " ".join(p.cmdline())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cmdline = "unknown"

    while is_process_running(pid):
        time.sleep(5)  # Wait for 5 seconds before checking again

    # Initialize the exit_code and status variables
    exit_code = None
    status = "unknown"

    if process_info:
        # Process has exited, gathering final information
        try:
            p = psutil.Process(pid)
            exit_code = p.wait()
            status = "terminated" if exit_code == 0 else "terminated with errors"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            status = "could not determine"

    # Build the message
    message = (
        f"Process {pid} has completed.\n" f"Command: {cmdline}\n" f"Status: {status}\n"
    )
    if exit_code is not None:
        message += f"Exit Code: {exit_code}\n"
    if process_info:
        message += (
            f"CPU Times: {process_info['cpu_times']}\n"
            f"Memory Info: {process_info['memory_info']}\n"
            f"Started at: {time.ctime(process_info['create_time'])}\n"
        )

    print(message)

    await send_telegram_message(TELEGRAM_BOT_TOKEN, CHAT_ID, message)


if __name__ == "__main__":
    # Load Telegram credentials from the JSON file
    with open("telegram.json", "r") as file:
        config = json.load(file)

    global TELEGRAM_BOT_TOKEN
    global CHAT_ID

    TELEGRAM_BOT_TOKEN = config.get("TELEGRAM_BOT_TOKEN")
    CHAT_ID = config.get("CHAT_ID")

    # Argument parser to handle command line arguments
    parser = argparse.ArgumentParser(
        description="Monitor a process and notify via Telegram when it exits."
    )
    parser.add_argument("pid", type=str, help="The process ID (PID) or job ID to monitor")

    args = parser.parse_args()

    asyncio.run(main(args.pid))
