from adb_module import ADBManager
import time

if __name__ == "__main__":
    adb = ADBManager()
    adb.restart_adb()
    adb.start()

    try:
        while True:
            time.sleep(1)  # Keeps main thread alive
    except KeyboardInterrupt:
        adb.stop()
