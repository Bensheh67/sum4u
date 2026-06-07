content = open('desktop/hotkey.py').read()

old_restart = '''    def _restart(self) -> None:
        self.stop()          # stop + clear before re-creating
        _KeyState.clear()
        self._started = True
        t = threading.Thread(target=self._run, daemon=True, name="hotkey-listener")
        t.start()

    def _run(self) -> None:
        with self._listener_lock:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False,
            )
        self._listener.join()'''

new_restart = '''    def _restart(self) -> None:
        self.stop()
        _KeyState.clear()
        # _started is set inside _run() after listener creation,
        # not here — this prevents a race where stop() is called before
        # the thread has even started, causing "cannot join" errors.
        t = threading.Thread(target=self._run, daemon=True, name="hotkey-listener")
        t.start()

    def _run(self) -> None:
        with self._listener_lock:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False,
            )
        # Mark as started only after the listener is fully constructed
        # (not when the thread is created, which can race with GC).
        self._started = True
        self._listener.join()'''

if old_restart not in content:
    print("OLD NOT FOUND")
    import sys; sys.exit(1)

new_content = content.replace(old_restart, new_restart, 1)
open('desktop/hotkey.py', 'w').write(new_content)
print("done")
