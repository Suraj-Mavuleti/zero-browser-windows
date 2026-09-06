#!/usr/bin/env python3
import sys, time
def main():
    print("\033[1;36m" + "="*60 + "\033[0m")
    print(f"\033[1;36m          {sys.argv[0].split('/')[-1].upper()} MEMORY ALLOCATION & THREADING CORE\033[0m")
    print("\033[1;36m" + "="*60 + "\033[0m")
    print("\033[3mEngine booted in User-Space. Type 'alloc <bytes>', 'free', or 'exit'.\033[0m\n")
    memory = 0
    while True:
        try:
            cmd = input("\033[1;32mSYS > \033[0m").strip().split()
            if not cmd: continue
            if cmd[0] == 'exit': break
            if cmd[0] == 'alloc' and len(cmd) > 1 and cmd[1].isdigit():
                memory += int(cmd[1])
                print(f"\033[1;33m[Kernel]: Allocated {cmd[1]} bytes. Total Arena: {memory} bytes.\033[0m")
            elif cmd[0] == 'free':
                memory = 0
                print("\033[1;32m[Kernel]: Memory arena flushed. Lock-free sweep complete.\033[0m")
            else:
                print("\033[1;31m[Error]: Invalid syscall.\033[0m")
        except: break
if __name__ == '__main__': main()
