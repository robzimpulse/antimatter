import asyncio
import os
import ptyprocess
import base64
import logging
import signal

logger = logging.getLogger(__name__)

class PtyManager:
    def __init__(self, router):
        self.router = router
        self.sessions = {}  # Map of id to ptyprocess.PtyProcess
        self.read_tasks = {}

    async def start_pty(self, session_id: str, cols: int = 80, rows: int = 24):
        if session_id in self.sessions:
            logger.info(f"PTY session {session_id} already exists, skipping start.")
            # Optionally resize to requested dimensions
            self.sessions[session_id].setwinsize(rows, cols)
            return

        try:
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["LANG"] = "en_US.UTF-8"
            env["PS1"] = "\\[\\e[1;34m\\]\\w\\[\\e[0m\\] \\$ "
            env["PROMPT_COMMAND"] = ""

            # Spawn a raw byte-oriented pty
            pty = ptyprocess.PtyProcess.spawn(['/bin/bash', '--noprofile', '--norc'], dimensions=(rows, cols), env=env)
            self.sessions[session_id] = pty
            logger.info(f"Started PTY session {session_id} with PID {pty.pid}")

            # Make the file descriptor non-blocking
            os.set_blocking(pty.fd, False)

            # Start reading from it
            loop = asyncio.get_running_loop()
            
            async def _read_loop():
                queue = asyncio.Queue(maxsize=1000)
                dropped_frames = 0  # track consecutive drops for PTY_OVERFLOW signal

                def _reader():
                    nonlocal dropped_frames
                    try:
                        data = os.read(pty.fd, 4096)
                        if data:
                            try:
                                queue.put_nowait(data)
                                dropped_frames = 0  # reset on successful enqueue
                            except asyncio.QueueFull:
                                dropped_frames += 1
                                logger.warning(f"PTY backpressure: dropped frame #{dropped_frames} for session {session_id}")
                    except BlockingIOError:
                        pass
                    except OSError as e:
                        logger.error(f"PTY read error for {session_id}: {e}")
                        loop.remove_reader(pty.fd)
                        self._cleanup(session_id)

                loop.add_reader(pty.fd, _reader)

                try:
                    while session_id in self.sessions:
                        try:
                            data = await asyncio.wait_for(queue.get(), timeout=0.5)
                        except asyncio.TimeoutError:
                            # If frames were dropped since last flush, notify the client
                            if dropped_frames > 0:
                                if self.router.clients:
                                    await self.router.broadcast_to_clients_encrypted({
                                        "type": "PTY_OVERFLOW",
                                        "dropped": dropped_frames,
                                        "message": f"[{dropped_frames} frame(s) dropped — terminal output was too fast]"
                                    })
                                dropped_frames = 0
                            continue

                        # If there were pending drops, notify before the next real frame
                        if dropped_frames > 0:
                            if self.router.clients:
                                await self.router.broadcast_to_clients_encrypted({
                                    "type": "PTY_OVERFLOW",
                                    "dropped": dropped_frames,
                                    "message": f"[{dropped_frames} frame(s) dropped — terminal output was too fast]"
                                })
                            dropped_frames = 0

                        b64_data = base64.b64encode(data).decode('utf-8')
                        if self.router.clients:
                            await self.router.broadcast_to_clients_encrypted({
                                "type": "PTY_OUTPUT",
                                "data": b64_data
                            })
                except asyncio.CancelledError:
                    pass
                finally:
                    loop.remove_reader(pty.fd)

            self.read_tasks[session_id] = asyncio.create_task(_read_loop())

        except Exception as e:
            logger.error(f"Failed to start PTY for {session_id}: {e}")

    def write_input(self, session_id: str, data_b64: str):
        if session_id not in self.sessions:
            return
        
        try:
            data = base64.b64decode(data_b64)
            self.sessions[session_id].write(data)
        except Exception as e:
            logger.error(f"Failed to write input to {session_id}: {e}")

    def resize(self, session_id: str, cols: int, rows: int):
        if session_id not in self.sessions:
            return
        try:
            pty_proc = self.sessions[session_id]
            pty_proc.setwinsize(rows, cols)
            if pty_proc.pid:
                os.kill(pty_proc.pid, signal.SIGWINCH)
        except Exception as e:
            logger.error(f"Failed to resize PTY {session_id}: {e}")

    def ping(self, session_id: str):
        if session_id not in self.sessions:
            return
        # Just an acknowledgment or keepalive logic if needed
        logger.debug(f"Received PING for {session_id}")

    def _cleanup(self, session_id: str):
        logger.info(f"Cleaning up PTY session {session_id}")
        if session_id in self.sessions:
            try:
                self.sessions[session_id].terminate(force=True)
            except Exception:
                pass
            del self.sessions[session_id]
        if session_id in self.read_tasks:
            self.read_tasks[session_id].cancel()
            del self.read_tasks[session_id]

