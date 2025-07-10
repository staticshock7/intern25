from time import sleep
from os import path
from paramiko import SSHClient, AutoAddPolicy
from socket import gaierror
from re import findall, search, match
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
        self.even_rtr = None
        self.odd_rtr = None
        self.even_fw_list = None
        self.odd_fw_list = None
        self.even_lb_list = None
        self.odd_lb_list = None

    def set_even_rtr(self, rtrs):
        self.even_rtr = rtrs
    def set_odd_rtr(self, rtrs):
        self.odd_rtr = rtrs
    def set_even_fw_list(self, fws):
        self.even_fw_list = fws
    def set_odd_fw_list(self, fws):
        self.odd_fw_list = fws
    def set_even_lb_list(self, lbs):
        self.even_lb_list = lbs
    def set_odd_lb_list(self, lbs):
        self.odd_lb_list = lbs

    def get_even_rtr(self):
        return self.even_rtr
    def get_odd_rtr(self):
        return self.odd_rtr
    def get_even_fw_list(self):
        return self.even_fw_list
    def get_odd_fw_list(self):
        return self.odd_fw_list
    def get_even_lb_list(self):
        return self.even_lb_list
    def get_odd_lb_list(self):
        return self.odd_lb_list

# open ssh connections, returns cli channel and invoked shell
def open_conn(device, user, pass1):
    cli = SSHClient()
    cli.set_missing_host_key_policy(AutoAddPolicy())
    try:
        cli.connect(f"{device}.XXXX", username=user, password=pass1)
        shell = cli.invoke_shell()
        sleep(1)
        shell.recv(1000)
        sleep(1)
    except gaierror as e:
        print(f"\n{CYN}Invalid Host: {RST}{device}. Resolution failed: {e}")
        return f"[ERR] {device}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {device}: {e}"
    return cli, shell

# returns output
def command(shell, command, output=False):
    shell.send(f"{command}\n")
    sleep(0.5)
    if output == True:
        out = shell.recv(2048).decode()
        return out
    else:
        return "Fin flag not set!"

def menu1():
    print(f"\nEnter devices: ")
    return input(">> ").split()

def routerCheck(dev, username, password, shell1=""):
    # checks if an existing shell is passed back in
    if not shell1:
        #print("not shellllllll")
        cli, shell = open_conn(device=dev, user=username, pass1=password)
        #sleep(4)
        out1 = command(shell, "show interface status | include notconnected", output=True) 
        return out1, shell, cli
    else:
        #sleep(2)
        out1 = command(shell1, "show interface status | include notconnected", output=True) 

        return out1

def devsort(dev_instObj):
    raw_devs = menu1()
    print(raw_devs)
    even_LBs = []
    odd_LBs = []
    even_FWs = []
    odd_FWs = []
    for i in raw_devs:
        if findall(r"^LB.*(00|02|04)$", i):
            even_LBs.append(i)
        elif findall(r"^LB.*(01|03|05)$", i):
            odd_LBs.append(i)
        elif findall(r"FW.*(00|02)$", i):
            even_FWs.append(i)
        elif findall(r"FW.*(01|03)$", i):
            odd_FWs.append(i)
        #elif findall(r"^B(\d{2}).*$", i):
        #    RTRs.append(i)
        else:
            print("No input provided!")
    dev_instObj.set_even_fw_list(even_FWs)
    dev_instObj.set_odd_fw_list(odd_FWs)
    dev_instObj.set_even_lb_list(even_LBs)
    dev_instObj.set_odd_lb_list(odd_LBs)


# get the router(s) using an LB inputed
def get_rtrs_from_lb(cableObj, devObj):
    even_check = False
    odd_check = False
    
    if devObj.get_even_lb_list():
        cli, shell = open_conn(devObj.get_even_lb_list()[0], "devuser", "devuserpassword") # first device in even lb list
        out = command(shell, "show interfaces brief | include Up", output=True)

        for i in out.splitlines():
            if findall(r"B\d{2}.*(00)",i): # finds the line of output containing the LB router connection
                cableObj.store_lb_port(i.split()[0]) # assumes all LBs in a POD uses the same port
                for k in i.split():
                    # find the router
                    if findall(r"B\d{2}.*(00)", k):
                        devObj.set_even_rtr(search(r"B\d{2}.*(00)", k).group()) # stores the even router
        even_check = True  
        cli.close()
    else:
        print("Even LB list empty.")
        
    if devObj.get_odd_lb_list():
        cli, shell = open_conn(devObj.get_odd_lb_list()[0], "devuser", "devuserpassword") # first device in even lb list
        out = command(shell, "show interfaces brief | include Up", output=True)

        for i in out.splitlines():
            if findall(r"B\d{2}.*(01)",i): # finds the line of output containing the LB router connection
                cableObj.store_lb_port(i.split()[0]) # assumes all LBs in a POD uses the same port # may need to work around setting this twice
                for k in i.split():
                    # find the router
                    if findall(r"B\d{2}.*(01)", k):
                        devObj.set_odd_rtr(search(r"B\d{2}.*(01)", k).group()) # stores the odd router
        cli.close()
        odd_check = True
    else:
        print("Odd LB list empty.")
    return even_check, odd_check
# get the router(s) using an FW inputed if no LBs provided
def get_rtrs_from_fw(devObj, even_check, odd_check):

    if devObj.get_even_fw_list() and even_check == False:
        cli, shell = open_conn(devObj.get_even_fw_list()[0], "devuser", "devuserpassword") # first device in even lb list
        command(shell, "firstcommand")
        cmd_out = command(shell, "show interface eth1-01 comments", output=True)

        devObj.set_even_rtr("".join(findall(r"comments (B\d{2}.{3}00)", cmd_out))) # stores the even router

        cli.close()
    else:
        print("Even FW list empty.")
        
    if devObj.get_odd_fw_list() and odd_check == False:
        cli, shell = open_conn(devObj.get_odd_fw_list()[0], "devuser", "devuserpassword") # first device in even lb list
        command(shell, "firstcommand")
        cmd_out = command(shell, "show interface eth1-01 comments", output=True)

        devObj.set_odd_rtr("".join(findall(r"comments (B\d{2}.{3}00)", cmd_out)).replace("00","01")) # stores the odd router <> replaces the even suuffix with 01 | crude fix

        cli.close()
    else:
        print("Odd FW list empty.")


# flip_lb_int turns the interface down if it's up and up if it's down for the LBs
def flip_lb_int(shell, eth_int):
    cmd_output = command(shell, f"show interface ethernet {eth_int}", output=True)
    state = "".join(findall(r"protocol is (up|down)", cmd_output))

    if state == "up":
        command(shell, "config t")
        command(shell, f"interface ethernet {eth_int}")
        command(shell, "disable")

        cmd_output = command(shell, f"show interface ethernet {eth_int}", output=True)
        state = "".join(findall(r"protocol is (up|down)", cmd_output))

    elif state == "down":
        command(shell, "config t")
        command(shell, f"interface ethernet {eth_int}")
        command(shell, "enable")

        #sleep(5) # longer time for interface to come up, and report correctly

        cmd_output = command(shell, f"show interface ethernet {eth_int}", output=True)
        state = "".join(findall(r"protocol is (up|down)", cmd_output))
    else:
        print(f"Unable to change interface — {YEL}Please manually verify state{RST}")
        state = "No output received"
    return state
# flip_lb_int turns the interface down if it's up and up if it's down for the FWs
def flip_fw_int(shell, num):
    cmd_output = command(shell, f"show interface eth{num}", output=True)
    state1 = "".join(findall(r"state (on|off)\r\nmac-addr", cmd_output))
    state2 = "".join(findall(r"link-state link (up|down)", cmd_output))
    
    if state1 == "on" and state2 == "up":
        #command(shell, "firstcommand")
        command(shell, "lock database override")
        command(shell, f"set interface eth{num} state off")

        cmd_output = command(shell, f"show interface eth{num}", output=True)
        state1 = "".join(findall(r"state (on|off)\r\nmac-addr", cmd_output))
        state2 = "".join(findall(r"link-state link (up|down)", cmd_output))

    elif state1 == "off" and state2 == "down":
        #command(shell, "firstcommand")
        command(shell, "lock database override")
        command(shell, f"set interface eth{num} state on")
        sleep(5) # allowing time to come up
        cmd_output = command(shell, f"show interface eth{num}", output=True)
        state1 = "".join(findall(r"state (on|off)\r\nmac-addr", cmd_output))
        state2 = "".join(findall(r"link-state link (up|down)", cmd_output))

    else:
        print(f"Unable to change interface — {YEL}Please manually verify FW state{RST}")
        state1 = "No output received1"
        state2 = "No output received2"
    return state1, state2

def even_rtr_check_lbs(devices, cable1):
    diffs = ""

    for dev in devices.get_even_lb_list():
        cli, shell = open_conn(dev, "devuser", "devuserpassword") # opens connection to sample odd/even LBs or [not prepared script FWs]
        # gets baseline result of rtr "not connected" interfaces
        router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_even_rtr(), username="devuser", password="devuserpassword2")
        flip_lb_int(shell, cable1.get_lb_port()) # intended to flip down
         # passes the opened shell from the first rtrCheck call
        router_result2 = routerCheck(dev=devices.get_even_rtr(), username="devuser", password="devuserpassword2", shell1=rtr_shell)
        flip_lb_int(shell, cable1.get_lb_port()) # intended to flip up
        # store difference between lists of the two outputs from routerCheck calls
        diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
        cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

        print(f"\n\n>> {devices.get_even_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {cable1.get_lb_port()}")
        # close connection
        cli.close()
    return rtr_cli

def odd_rtr_check_lbs(devices, cable1):
    diffs = ""

    for dev in devices.get_odd_lb_list():
        cli, shell = open_conn(dev, "devuser", "devuserpassword") # opens connection to sample odd/even LBs or [not prepared script FWs]
        # gets baseline result of rtr "not connected" interfaces
        router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_odd_rtr(), username="devuser", password="devuserpassword2")
        flip_lb_int(shell, cable1.get_lb_port()) # intended to flip down
         # passes the opened shell from the first rtrCheck call
        router_result2 = routerCheck(dev=devices.get_odd_rtr(), username="devuser", password="devuserpassword2", shell1=rtr_shell)
        flip_lb_int(shell, cable1.get_lb_port()) # intended to flip up
        # store difference between lists of the two outputs from routerCheck calls
        diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
        cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

        print(f"\n\n>> {devices.get_odd_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {cable1.get_lb_port()}")
        # close connection
        cli.close()
    return rtr_cli

# finished
def even_rtr_check_fws(devices, cable1):
    diffs = ""
    fw_port = "1-01"
    for dev in devices.get_even_fw_list():
        cli, shell = open_conn(dev, "devuser", "devuserpassword") # opens connection to sample odd/even LBs or [not prepared script FWs]
        command(shell, "firstcommand")
        # gets baseline result of rtr "not connected" interfaces
        router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_even_rtr(), username="devuser", password="devuserpassword2")
        flip_fw_int(shell, num=f"{fw_port}") # intended to flip down

         # passes the opened shell from the first rtrCheck call
        router_result2 = routerCheck(dev=devices.get_even_rtr(), username="devuser", password="devuserpassword2", shell1=rtr_shell)
        flip_fw_int(shell, num=f"{fw_port}") # intended to flip up
        # store difference between lists of the two outputs from routerCheck calls
        diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
        cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

        print(f"\n\n>> {devices.get_even_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {fw_port}")
        # close connection
        cli.close()
    return rtr_cli
# finished
def odd_rtr_check_fws(devices, cable1):
    diffs = ""
    fw_port = "1-01"
    for dev in devices.get_odd_fw_list():
        cli, shell = open_conn(dev, "devuser", "devuserpassword") # opens connection to sample odd/even LBs or [not prepared script FWs]
        command(shell, "firstcommand")
        # gets baseline result of rtr "not connected" interfaces
        router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_odd_rtr(), username="devuser", password="devuserpassword2")
        flip_fw_int(shell, num=f"{fw_port}") # intended to flip down

         # passes the opened shell from the first rtrCheck call
        router_result2 = routerCheck(dev=devices.get_odd_rtr(), username="devuser", password="devuserpassword2", shell1=rtr_shell)
        flip_fw_int(shell, num=f"{fw_port}") # intended to flip up
        # store difference between lists of the two outputs from routerCheck calls
        diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
        cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

        print(f"\n\n>> {devices.get_odd_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {fw_port}")
        # close connection
        cli.close()
    return rtr_cli

def which_check():
    devices = devdev()
    devsort(devices) # sorting into odd and even list atrributes
    cableObj0 = cable()
     # passes the devices Obj into dev sort for sorting
    even_check1, odd_check1 = get_rtrs_from_lb(cableObj0, devices) # even and odd router store in cable1.get_even/odd_rtr
    # passing these Booleans into this function to check if an even and/or router was stored from the get_rtrs_from_lb()
    get_rtrs_from_fw(devices, even_check1, odd_check1)
    


    if devices.get_even_lb_list():
        rtr_cli = even_rtr_check_lbs(devices, cableObj0)
    if devices.get_odd_lb_list():
        rtr_cli = odd_rtr_check_lbs(devices, cableObj0)
    if devices.get_even_fw_list():
        rtr_cli = even_rtr_check_fws(devices, cableObj0)
    if devices.get_odd_fw_list():
        rtr_cli = odd_rtr_check_fws(devices, cableObj0)

    rtr_cli.close()
which_check()
