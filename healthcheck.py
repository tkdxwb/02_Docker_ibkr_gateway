#!/usr/bin/env python3
"""三个 IB Gateway 账户的健康巡检。

对每个账户检查两项：
  1) 容器是否在运行 (docker inspect)
  2) API 是否真正可用 —— 发送 IB API 握手, 期待 Gateway 返回 server version

用法:
  python3 healthcheck.py            # 单次巡检, 全健康退出码 0, 否则 1
  python3 healthcheck.py --watch 30 # 每 30 秒持续巡检, 状态翻转时告警
  python3 healthcheck.py --watch 30 --quiet  # 仅状态变化时输出
"""
import argparse
import socket
import struct
import subprocess
import sys
import time

HOST = "127.0.0.1"
ACCOUNTS = [
    {"name": "账户1", "container": "ib-gateway-1", "api_port": 4001, "vnc": 5900},
    {"name": "账户2", "container": "ib-gateway-2", "api_port": 4011, "vnc": 5901},
    {"name": "账户3", "container": "ib-gateway-3", "api_port": 4021, "vnc": 5902},
]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def container_status(name):
    try:
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", name],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip() if r.returncode == 0 else "absent"
    except Exception:
        return "docker-error"


def api_handshake(port, timeout=4):
    """发送 IB API 握手, 返回 (ok, info)。"""
    try:
        s = socket.create_connection((HOST, port), timeout=timeout)
    except OSError as e:
        return False, type(e).__name__
    try:
        s.sendall(b"API\x00")
        msg = b"v100..187"
        s.sendall(struct.pack(">I", len(msg)) + msg)
        s.settimeout(timeout)
        data = s.recv(4096)
    except OSError as e:
        return False, type(e).__name__
    finally:
        s.close()
    if not data:
        return False, "EOF(无响应)"
    # v100+ 响应: 4字节长度 + "serverVersion\0connectionTime\0"
    parts = data[4:].split(b"\x00") if len(data) > 4 else data.split(b"\x00")
    ver = parts[0].decode("latin1", "replace").strip() if parts else "?"
    return True, f"serverVersion={ver}"


def check_all():
    rows, all_ok = [], True
    for a in ACCOUNTS:
        st = container_status(a["container"])
        if st == "running":
            api_ok, info = api_handshake(a["api_port"])
        else:
            api_ok, info = False, f"容器={st}"
        ok = st == "running" and api_ok
        all_ok = all_ok and ok
        rows.append((a, st, ok, info))
    return all_ok, rows


def render(rows):
    lines = [f"[{now()}] IB Gateway 健康巡检"]
    for a, st, ok, info in rows:
        mark = "✅" if ok else "❌"
        lines.append(
            f"  {mark} {a['name']}  {a['container']:<13} 容器={st:<10} "
            f"API:{a['api_port']:<5} {info}"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="三个 IB Gateway 账户健康巡检")
    ap.add_argument("--watch", type=int, metavar="SEC",
                    help="循环巡检间隔秒数 (省略则只跑一次)")
    ap.add_argument("--quiet", action="store_true",
                    help="配合 --watch: 仅在状态变化时输出")
    args = ap.parse_args()

    if not args.watch:
        ok, rows = check_all()
        print(render(rows))
        sys.exit(0 if ok else 1)

    prev = None
    while True:
        ok, rows = check_all()
        state = tuple(r[2] for r in rows)
        if state != prev or not args.quiet:
            print(render(rows), flush=True)
        if prev is not None and state != prev:
            for (a, st, cur, info), was in zip(rows, prev):
                if cur != was:
                    trans = "✅恢复" if cur else "❌异常"
                    print(f"  ⚠️  [{now()}] {a['name']} ({a['container']}) "
                          f"状态翻转: {trans}  {info}", flush=True)
        prev = state
        time.sleep(args.watch)


if __name__ == "__main__":
    main()
