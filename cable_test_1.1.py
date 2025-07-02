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
        self.fw_state1 = None
        self.fw_state2 = None
        self.rtr_state = None
        self.lb_port = None
        self.fw_port = None
        self.rtr_port = None

    def store_lb_state(self, updown):
        self.lb_state = updown
    def store_fw_state1(self, updown):
        self.fw_state1 = updown
    def store_fw_state2(self, updown):
        self.fw_state2 = updown
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
    def get_fw_state1(self):
        return self.fw_state1
    def get_fw_state2(self):
        return self.fw_state2
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
        self.rtr_list = None
        self.fw_list = None
        self.lb_list = None


    def set_rtr_list(self, rtrs):
        self.rtr_list = rtrs
    def set_fw_list(self, fws):
        self.fw_list = fws
    def set_lb_list(self, lbs):
        self.lb_list = lbs

    def get_rtr_list(self):
        return self.rtr_list
    def get_fw_list(self):
        return self.fw_list
    def get_lb_list(self):
        return self.lb_list

# prints the menu for the user
def menu1():
    print(f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n{MAG}{'='*30}{RST} Cable Validations {MAG}{'='*30}{RST}")
    print(f"1. Enter the device list for the POD, including routers: \nExample {YEL} LXXXXXXX BXXXXXX FXXXXXX")
    return input(">> ").split()

def menu2():
    print(f"{MAG}{"="*30}{RST} Select the port configuration! {MAG}{"="*30}{RST}")
    print(f"\n1. Standard port configuration — LBs: eth XX; RTR-Side-LB: 1/XX-XX; RTR-Side-FW: 1/XX-XX")
    print(f"2. Manual batch entry")
    return input(f"{YEL}>>> ")

def menu3():
    while True:
        val1 = menu2()
        if val1 == "1":
            return "XX", "1/XX-XX", "1/XXX-XX"
        elif val1 == "2":
            lb = input(f"{RST}1. Enter the LB port [Example: {GRN}XX{RST}]: ")
            rtr_lb = input(f"2. Enter the Router-Side {YEL}LB{RST} ports [Example: {GRN}1/XX-XX{RST}]: ")
            rtr_fw = input(f"3. Enter the Router-Side {YEL}FW{RST} ports [Example: {GRN}1/XX-XX{RST}]: ")
            return lb, rtr_lb, rtr_fw
        else:
            print(f"Please select 1 or 2.")
            sleep(1)

# sorts then stores the devices in the instance
def devsort():
    dev_inst = devdev()
    raw_devs = menu1()
    LBs = []
    FWs = []
    RTRs = []
    for i in raw_devs:
        if findall(r"^LB.*(\d{4})$", i):
            LBs.append(i)
        elif findall(r"FW.*(\d{4})$", i):
            FWs.append(i)
        elif findall(r"^B(\d{2}).*$", i):
            RTRs.append(i)
        else:
            print("No input provided!")
    dev_inst.set_fw_list(FWs)
    dev_inst.set_lb_list(LBs)
    dev_inst.set_rtr_list(RTRs)

    return dev_inst


def ssh1(dev, key1, user1, cmd1, cmd2=""):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:       
        ssh.connect(f"{dev}.XXXX", username=user1, password=key1, banner_timeout=20)
        shell = ssh.invoke_shell()
        sleep(2)
        recv = ""
        shell.send(f"{cmd1}\n")
        sleep(1)
        shell.send(f"{cmd2}\n")
        sleep(1)
    
        if shell.recv_ready:
            recv = shell.recv(2048).decode()

    except gaierror as e:
        print(f"\n{CYN}Invalid Host:{RST} {dev}. Resolution failed: {e}")
        return f"[ERR] {dev}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {dev}: {e}"
    finally:
        ssh.close()

    return recv

# lb flipflop
def flipflop_lb(dev, key1, user1, state, eth_int=""):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:       
        ssh.connect(f"{dev}.XXXX", username=user1, password=key1, banner_timeout=20)
        shell = ssh.invoke_shell()
        sleep(2)
        recv = ""


        if state == "up":
            shell.send("config t\n")
            sleep(1)
            shell.send(f"interface ethernet {eth_int}\n")
            sleep(0.5)
            shell.send("disable\n")
            sleep(1)
            shell.send(f"show interface eth {eth_int}\n")
            sleep(1)
            if shell.recv_ready:
                recv = shell.recv(2048).decode()
            ssh.close()
        elif state == "down":
            shell.send("config t\n")
            sleep(1)
            shell.send(f"interface ethern {eth_int}\n")
            sleep(0.5)
            shell.send("enable\n")
            sleep(4) # longer time for interface to come up, and report correctly
            shell.send(f"show interface eth {eth_int}\n")
            sleep(1)
            if shell.recv_ready:
                recv = shell.recv(2048).decode()
            ssh.close()
        else:
            print(f"Unable to change interface — {YEL}Please manually verify state{RST}")
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

# firewall flipflop
def flipflop_fw(dev, key1, user1, state1, state2, eth_int=""):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:       
        ssh.connect(f"{dev}.XXXX", username=user1, password=key1, banner_timeout=20)
        shell = ssh.invoke_shell()
        sleep(2)
        recv = ""
        if state1 == "on" and state2 == "up":
            shell.send("xxxx\n")
            sleep(0.5)
            shell.send("xxxx\n")
            sleep(0.5)
            shell.send(f"set interface eth1-xx state off\n")
            sleep(1)
            shell.send("show interface eth1-xx\n")
            sleep(1)

            if shell.recv_ready:
                recv = shell.recv(2048).decode()
            ssh.close()
        elif state1 == "off" and state2 == "down":
            shell.send("clish\n")
            sleep(0.5)
            shell.send("lock database override\n")
            sleep(0.5)
            shell.send(f"set interface eth1-01 state on\n")
            sleep(5) # longer time for the interface to go back up
            shell.send("show interface eth1-01\n")
            sleep(1)

            if shell.recv_ready:
                recv = shell.recv(2048).decode()
            ssh.close()
        else:
            print(f"Unable to change interface — {YEL}Please manually verify state{RST}")
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

# compares the output from rtrBase with its own output for differences
def rtrShow(dev, key2, user2, cableObj, lb_eth_int="", fw_eth_int=""): # will need to include checking for multiple notconnec lines
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    try:
        ssh.connect(f"{dev}.XXXX", username=user2, password=key2, banner_timeout=20)
        shell = ssh.invoke_shell()
        sleep(2)

        # checks if lb place was filled to determine which show cmd
        if lb_eth_int:
            shell.send(f"show interface ethernet {lb_eth_int} status\n") # show specific interface range for lb
            sleep(2)
            #if shell.recv_ready:
            recv2 = shell.recv(2048).decode()

            cableObj.store_rtr_port(''.join(findall(r"\bEth1/(\d{2}).*notconnected.*\b", recv2))) # store disconnected router port string

        elif fw_eth_int:
            shell.send(f"show interface ethernet {fw_eth_int} status\n") # show specific interface range for fw
            sleep(2)
            #if shell.recv_ready:
            recv2 = shell.recv(2048).decode()

            cableObj.store_rtr_port(''.join(findall(r"\bEth1/(\d{2}).*notconnected.*\b", recv2))) # store disconnected router port string
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


def cable1():
    # gathering all the odd devices
    dev_inst = devsort()
    lbs = []
    fws = []
    odd_rtr = ""
    # sorts the odd RTRs into the lbs list
    for i in dev_inst.get_rtr_list():
        if findall(r"^B.*(01$)",i):
            odd_rtr = i
        else:
            print("No odd router provided!")
            return # exits the function if no odd RTRs are provided
    # sorts the odd LBs into the lbs list
    print("RTR", odd_rtr)
    for i in dev_inst.get_lb_list():
        if findall(r"^LB.*(01$|03$|05$)",i):
            lbs.append(i)
        else:
            print("No LBs entered.")
    print(f"LBS: {lbs}")
    # sorts the odd FWs into the lbs list
    for i in dev_inst.get_fw_list():
        if findall(r"^FW.*(01$|03$)",i):
            fws.append(i)
        else:
            print("No FWs entered.")
    print(f"FWs: {fws}")
    # exits the function if no odd FWs our LBs are provided
    if not lbs and not fws:
        return

    lb, rtr_lb, rtr_fw = menu3()

    key1 = getpass(f"{CYN}>>>{RST} Enter the SSH pass for the {YEL}LB{RST}: ")
    key2 = getpass(f"{CYN}>>>{RST} Enter the SSH pass for the {YEL}RTR{RST}: ")
    user = "XXX"
    
    # checks LBs # please put an if statement here for the condition of FWs provided but not LBs
    for dev in lbs:
        output11 = ssh1(dev, key1, user, cmd1=f"show interface eth {lb}")
        cable1 = cable()
        cable1.store_lb_port(lb) # may just use the variable directly to pass to the flipflop function

        cable1.store_lb_state("".join(findall(r"protocol is (up|down)", output11))) # stores the LB state
        print(f"\n1. Initial LB {CYN}{dev}{RST} state: {RED}{cable1.get_lb_state()}{RST}")

        # change the lb state by passing it and its port to the flipflop function
        output22 = flipflop_lb(dev, key1, user, cable1.get_lb_state(), lb) # check if you stored a value for lb port

        # checks the returned output to from up down to determine if the state flipped
        cable1.store_lb_state("".join(findall(r"protocol is (up|down)", output22)))
        print(f"2. Automated LB {CYN}{dev}{RST} state: {RED}{cable1.get_lb_state()}{RST}")
        sleep(5)
        rtrShow(odd_rtr, key2, user, cable1, lb_eth_int=rtr_lb) # variable user supplied containing lb/fw range

        output33 = flipflop_lb(dev, key1, user, cable1.get_lb_state(), lb) # restore the port to enable
        cable1.store_lb_state("".join(findall(r"line protocol is (up|down)", output33)))
        print(f"3. Restored LB {CYN}{dev}{RST} state: {RED}{cable1.get_lb_state()}{RST}")

        print(f"{YEL}>> {dev}{RST} Ethernet {GRN}{cable1.get_lb_port()}{RST} is connected to {YEL}{odd_rtr}{RST} Ethernet {GRN}{cable1.get_rtr_port()}{RST}")

    for dev in fws:

        cmd1 = "XX"
        cmd2 = "show interface ethXX"
        output1 = ssh1(dev, key1, user, cmd1, cmd2)
        cable2 = cable()

        cable2.store_fw_state1("".join(findall(r"state (on|off)", output1))) # stores the LB state
        cable2.store_fw_state2("".join(findall(r"link-state link (up|down)", output1))) # stores the LB link state
        print(f"\n1. Initial FW {CYN}{dev}{RST} state: {RED}{cable2.get_fw_state1()}{RST} and link-state: {RED}{cable2.get_fw_state2()}{RST}")

        # change the lb state by passing it and its port to the flipflop function
        output2 = flipflop_fw(dev, key1, user, cable2.get_fw_state1(), cable2.get_fw_state2()) # check if you stored a value for lb port

        # checks the returned output to from up down to determine if the state flipped
        cable2.store_fw_state1("".join(findall(r"state (on|off)\r\nmac-addr", output2))) # stores the LB state; including indexing because the output contains state off from the entered command
        cable2.store_fw_state2("".join(findall(r"link-state link (up|down)", output2))) # stores the LB link state
        print(f"2. Automated FW {CYN}{dev}{RST} state: {RED}{cable2.get_fw_state1()}{RST} and link-state: {RED}{cable2.get_fw_state2()}{RST}")
        
        rtrShow(odd_rtr, key2, user, cable2, fw_eth_int=rtr_fw) # variable user supplied containing lb/fw range

        output3 = flipflop_fw(dev, key1, user, cable2.get_fw_state1(), cable2.get_fw_state2()) # restore the port to enable

        cable2.store_fw_state1("".join(findall(r"state (on|off)\r\nmac-addr", output3))) # stores the LB state; including indexing because the output contains state off from the entered command
        cable2.store_fw_state2("".join(findall(r"link-state link (up|down)", output3))) # stores the LB link state
        print(f"3. Final FW {CYN}{dev}{RST} state: {RED}{cable2.get_fw_state1()}{RST} and link-state: {RED}{cable2.get_fw_state2()}{RST}")

        print(f"{YEL}>>{RST} {YEL}{dev}{RST} Ethernet XX is connected to {odd_rtr} Ethernet {cable2.get_rtr_port()}")


def main():
    cable1()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nKeyboard Interupt — Exiting")
