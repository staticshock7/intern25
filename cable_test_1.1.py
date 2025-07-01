from time import sleep
from os import path
from paramiko import SSHClient, AutoAddPolicy
from socket import gaierror
from concurrent.futures import ThreadPoolExecutor, as_completed
from re import findall
from getpass import getpass, getuser

# Terminal color codes
RED = "\033[31m"
GRN = "\033[32m"
YEL = "\033[33m"
MAG = "\033[35m"
CYN = "\033[36m"
RST = "\033[0m"


class cable:
    def __init__(self):
        self.lb_state = None
        self.fw_state = None
        self.rtr_state = None
        self.lb_port = None
        self.fw_port = None
        self.rtr_port = None

    def store_lb_state(self, updown):
        self.lb_state = updown
    def store_fw_state(self, updown):
        self.fw_state = updown
    def store_rtr_state(self, conn_stat):
        self.rtr_state = conn_stat
        
    def store_lb_port(self, port):
        self.lb_port = port
    def store_fw_port(self, port):
        self.fw_port = port
    def store_rtr_port(self, port):
        self.rtr_port = port

    def get_lb_state(self):
        return self.lb_state
    def get_fw_state(self):
        return self.fw_state
    def get_rtr_state(self):
        return self.rtr_state
    def get_lb_port(self):
        return self.lb_port
    def get_fw_port(self):
        return self.fw_port
    def get_rtr_port(self):
        return self.rtr_port

class devdev:
    def __init__(self):
        self.rtrs = None
        self.fw_list = None
        self.lb_list = None


    def set_rtr_list(self, rtrs):
        self.devlist = rtrs
    def set_fw_list(self, fws):
        self.fw_list = fws
    def set_lb_list(self, lbs):
        self.lb_list = lbs

    def get_rtr_list(self):
        return self.rtrs
    def get_fw_list(self):
        return self.fw_list
    def get_lb_list(self):
        return self.lb_list

# prints the menu for the user
def menu1():
    print(f"\n{MAG}{'='*30}  {'='*30}{RST}")
    print(f"1. Enter the device list for the POD, including routers: \nExample {YEL} LXXXXXXX BXXXXXX FXXXXXX")
    return input(">> ").split()
# sorts then stores the devices in the instance
def devsort():
    dev_inst = devdev()
    raw_devs = menu1()
    LBs = []
    FWs = []
    RTRs = []
    for i in raw_devs:
        if findall(r"LBE|LBC", i):
            LBs.append(i)
        elif findall("FW", i):
            FWs.append(i)
        elif findall(r"B\d{2}", i):
            RTRs.append(i)
        else:
            print("No input provided!")
    dev_inst.set_fw_list(FWs)
    dev_inst.set_lb_list(LBs)
    dev_inst.set_rtr_list(RTRs)

    return dev_inst


def ssh1(dev, key1, user1, cmd):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:       
        ssh.connect(f"{dev}.xxx", username=user1, password=key1)
        shell = ssh.invoke_shell()
        sleep(2)
        recv = ""
        shell.send(f"{cmd}\n")
        sleep(1)
        

        if shell.recv_ready:
            recv = shell.recv(1024).decode()

    except gaierror as e:
        print(f"\n{CYN}Invalid Host:{RST} {dev}. Resolution failed: {e}")
        return f"[ERR] {dev}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {dev}: {e}"
    finally:
        ssh.close()

    return recv

def flipflop(dev, key1, user1, state, int_num):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:       
        ssh.connect(f"{dev}.xxx", username=user1, password=key1)
        shell = ssh.invoke_shell()
        sleep(2)
        recv = ""

        if state == "upup":
            shell.send("config t\n")
            sleep(1)
            shell.send(f"interface ethernet 25\n")
            sleep(0.5)
            shell.send("disable\n")
            sleep(1)
            shell.send("show interface eth 25\n")
            sleep(1)
            if shell.recv_ready:
                recv = shell.recv(2048).decode()
        elif state == "down":
            shell.send("config t\n")
            sleep(1)
            shell.send(f"interface ethern 25\n")
            sleep(0.5)
            shell.send("enable\n")
            sleep(1)
            shell.send("show interface eth 25\n")
            sleep(1)
            if shell.recv_ready:
                recv = shell.recv(2048).decode()
        else:
            print("Unable to change interface")
            recv = "No output received"

        return recv

    except gaierror as e:
        print(f"\n{CYN}Invalid Host:{RST} {dev}. Resolution failed: {e}")
        return f"[ERR] {dev}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {dev}: {e}"
    finally:
        ssh.close()

def rtrShow(dev, key2, user2, cableObj, rtrBase, lb="", fw=""): # will need to include checking for multiple notconnec lines
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:
        ssh.connect(f"{dev}.xxx", username=user2, password=key2)
        shell = ssh.invoke_shell()
        sleep(2)

        # checks if lb place was filled to determine which show cmd
        if lb:
            shell.send(f"show interface ethernet 1/20-23 status\n") # show specific interface range for lb
            sleep(2)
            #if shell.recv_ready:
            recv2 = shell.recv(2048).decode()
            diffs = "".join(set(rtrBase.splitlines()) - set(recv2.splitlines())) # stores the difference on the rtr

            cableObj.store_rtr_port(''.join(findall(r"\d{2}", diffs)[0])) # store disconnected router port string

        elif fw:
            shell.send(f"show interface ethernet 1/{fw} status\n") # show specific interface range for fw
            sleep(2)
            #if shell.recv_ready:
            recv2 = shell.recv(2048).decode()
            diffs = "".join(set(rtrBase.splitlines()) - set(recv2.splitlines()))
            cableObj.store_rtr_port(''.join(findall(r"\d{2}", diffs)[0])) # store disconnected router port string
        else:
            print(f"{RED}rtrShow function error{RST}")
        
    except gaierror as e:
        print(f"\n{CYN}Invalid Host:{RST} {dev}. Resolution failed: {e}")
        return f"[ERR] {dev}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {dev}: {e}"
    finally:
        ssh.close()

def rtrBase(dev, key2, user2, lb, fw=""):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:
        ssh.connect(f"{dev}.xxx", username=user2, password=key2)
        shell = ssh.invoke_shell()
        sleep(2)

        # checks if lb place was filled to determine which show cmd
        if lb:
            shell.send(f"show interface ethernet 1/20-23 status\n") # show specific interface range for lb
            sleep(2)
            #if shell.recv_ready:
            recv1 = shell.recv(2048).decode()
        elif fw:
            shell.send(f"show interface ethernet 1/{fw} status\n") # show specific interface range for fw
            sleep(2)
            #if shell.recv_ready:
            recv1 = shell.recv(2048).decode()
            
        else:
            print(f"{RED}rtrShow function error{RST}")

        return recv1
        
    except gaierror as e:
        print(f"\n{CYN}Invalid Host:{RST} {dev}. Resolution failed: {e}")
        return f"[ERR] {dev}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {dev}: {e}"
    finally:
        ssh.close()


def cable1():

    dev_inst = devsort()

    for i in dev_inst.get_rtr_list():
        if findall(r"01$"):
            odd_r = i
            

    rtr = ""
    devs = [""] # dev_list() # argument devdev instance
    key1 = ""#getpass(f"{CYN}>>>{RST} Enter the SSH pass for the {YEL}LB{RST}: ")
    key2 = ""#getpass(f"{CYN}>>>{RST} Enter the SSH pass for the {YEL}RTR{RST}: ")
    cmd1 = "show interface eth 25"
    with ThreadPoolExecutor(max_workers=8) as exe:
            futures = {exe.submit(ssh1, i, key1, cmd1): i for i in devs}

            for future in as_completed(futures):
                dev = futures[future]
                output = future.result()

                cable1 = cable()

                cable1.store_lb_state("".join(findall(r"\bup|down\b", output))) # stores the LB state
                print(f"LB {dev} state: ", cable1.get_lb_state())
                rtrBase2 = rtrBase(rtr, key2, lb="25", fw = "") # sends the rtr base over to router show for comparison

                cable1.store_lb_port("25")
                print("Stored lb port: ",cable1.get_lb_port())
                # change the lb state by passing it and its port to the flipflop function
                out = flipflop(dev, key1, cable1.get_lb_state(), cable1.get_lb_port()) # check if you stored a value for lb port

                # checks the returned output to from up down to determine if the state flipped
                cable1.store_lb_state("".join(findall(r"\bup|down\b", out)))
                print(f"LB {dev} state: ", cable1.get_lb_state())
                
                rtrShow(rtr, key2, cable1, rtrBase2, "25", fw="") # variable user supplied containing lb/fw range
                flipflop(dev, key1, cable1.get_lb_state(), cable1.get_lb_port()) # restore the port to enable
                print(f">> {dev} Ethernet {cable1.get_lb_port()} is connected to {rtr} Ethernet {cable1.get_rtr_port()}")


def main():
    cable1()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nkey1board Interupt — Exiting")
