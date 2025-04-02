#! /usr/bin/python3
import time
import os
import requests
import sys
from threading import Thread
from itertools import cycle

DEFAULT_EXTENSIONS = [
    ".xml", ".json", ".sql", ".txt", ".zip", ".tar", ".gz", ".tgz", ".bak", ".7z", ".rar", ".log", ".cache",
    ".secret", ".db", ".backup", ".yml", ".config", ".csv", ".yaml", ".md", ".md5", ".exe", ".dll", ".bin",
    ".ini", ".bat", ".sh", ".deb", ".rpm", ".iso", ".img", ".apk", ".msi", ".dmg", ".tmp", ".crt", ".pem",
    ".key", ".pub", ".asc", ".OLD", ".PHP", ".BAK", ".SAVE", ".ZIP", ".example", ".php", ".asp", ".aspx",
    ".jsp", ".dist", ".conf", ".swp", ".old", ".tar.gz", ".jar", ".bz2", ".php.save", ".php-backup", ".save",
    ".php~", ".aspx~", ".asp~", ".bkp", ".jsp~", ".sql.gz", ".sql.zip", ".sql.tar.gz", ".sql~", ".swp~",
    ".tar.bz2", ".lz", ".xz", ".z", ".Z", ".tar.z", ".sqlite", ".sqlitedb", ".sql.7z", ".sql.bz2", ".sql.lz",
    ".sql.rar", ".sql.xz", ".sql.z", ".sql.tar.z", ".war", ".backup.zip", ".backup.tar", ".backup.tgz",
    ".backup.sql", ".tar.bz", ".tgz.bz", ".tar.lz", ".backup.7z", ".backup.gz"
]

# Анимация загрузки
def loader_animation(message="Processing..."):
    animation = cycle(["|", "/", "-", "\\"])
    while not stop_loader:
        sys.stdout.write(f"\r{message} {next(animation)}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * len(message) + "\r")
    sys.stdout.flush()

# Получение URL из Web Archive
def fetch_urls(target):
    archive_url = f'https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey'
    global stop_loader
    stop_loader = False
    loader_thread = Thread(target=loader_animation, args=("Fetching URLs...",))
    loader_thread.start()

    try:
        response = requests.get(archive_url)
        response.raise_for_status()
        url_list = response.text.splitlines()
    except Exception as e:
        print(f"\nError fetching URLs: {e}")
        return []
    finally:
        stop_loader = True
        loader_thread.join()

    return url_list

# Фильтрация URL по расширениям
def filter_urls(url_list):
    filtered_urls = [url for url in url_list if any(url.lower().endswith(ext.lower()) for ext in DEFAULT_EXTENSIONS)]
    return filtered_urls

# Проверка архивации URL в Web Archive
def check_wayback_snapshot(url, output_file):
    wayback_url = f'https://archive.org/wayback/available?url={url}'
    try:
        response = requests.get(wayback_url)
        response.raise_for_status()
        data = response.json()
        if "archived_snapshots" in data and "closest" in data["archived_snapshots"]:
            snapshot_url = data["archived_snapshots"]["closest"].get("url")
            if snapshot_url:
                log_output(f"[+] {snapshot_url}", output_file)
        else:
            log_output(f"[-] No archive for {url}", output_file)
    except Exception as e:
        log_output(f"[?] Error checking {url}: {e}", output_file)

# Логирование в файл и терминал (как tee -a)
def log_output(message, output_file):
    print(message)
    output_file.write(message + "\n")
    output_file.flush()

# Основной процесс
def process_domain(target, output_file):
    url_list = fetch_urls(target)
    filtered_urls = filter_urls(url_list)

    log_output(f"Found {len(filtered_urls)} relevant URLs.\n", output_file)

    for url in filtered_urls:
        check_wayback_snapshot(url, output_file)

# Запуск скрипта
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wayBackupFinder.py <domain> [-o <output_file>]")
        exit()

    target = sys.argv[1]
    output_file = sys.stdout

    if len(sys.argv) > 3 and sys.argv[2] == "-o":
        output_file = open(sys.argv[3], 'a')

    log_output(f"Processing domain: {target}", output_file)
    process_domain(target, output_file)

    if output_file != sys.stdout:
        output_file.close()

    log_output("\nProcess complete.", sys.stdout)

