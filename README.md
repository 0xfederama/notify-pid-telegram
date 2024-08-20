# Process Monitor Telegram Notifier

This Python script monitors a process by its Process ID (PID) or Job ID and sends a notification via Telegram when the process completes. The notification includes details such as the PID, the command that started the process, its exit status, and resource usage.

## Installation
```bash
git clone https://github.com/0xfederama/notify-pid-telegram.git
cd notify-pid-telegram
python3 -m venv venv
pip install -r requirements.txt
```

## Run
In order to run the script, all it needs is a file `telegram.json` with the credentials of your bot and your telegram chat id:
```json
{
	"TELEGRAM_BOT_TOKEN": "123456",
	"CHAT_ID": "123456"
}
```

Then, all you need to do is run the command you want, get it's pid (when launching the command or using `jobs -l`) or use the job ID (like `%1`), and run the script with `python3 notify.py PID/JID`.

### Tip
When using this command, I assume that you usually run and forget it, appending an `&` at the end. Furthermore, if you use it on a server, you also want to be able to close the remote terminal without stopping the command, therefore with the help of `nohup`.

For this exact reason, I defined this bash function to run the code and put it into `~/.bash_aliases`, to simplify the command for the notifications. I personally redirect the notification script output to `/dev/null` because I don't care about it, but you can use anything you want.
```bash
notify_tg() {
    if [ -z "$1" ]; then
        echo "Error: No PID or JID provided."
        echo "Usage: notify_tg <PID/JID>"
        return 1
    fi
    cd /path/to/repo
    source venv/bin/activate
    nohup python3 notify.py "$1" >/dev/null 2>&1 &
}
```
Now you can simply run `notify_tg PID/JID` to monitor the process and send a notification.