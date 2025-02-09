#!/usr/bin/python3
from tkinter import *
from tkinter.messagebox import showinfo
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError
import os
import ssl
import re
from subprocess import Popen
import platform
import argparse, sys

hosttypes = ["C6100", "C6220", "iDRAC6", "iDRAC6-Blade", "IBM-SystemX"]

### Default Values
defaultHost = ""
defaultType = "C6100"
defaultUser = "root"
defaultPass = ""

### Global Vars
debugmsg = 0
ver = "0.9"


class hostInfo:
    def __init__(self, addr, type, username, password):
        self.addr = addr
        self.type = type
        self.username = username
        self.password = password


def connC6100(host):
    params = {"WEBVAR_USERNAME": host.username, "WEBVAR_PASSWORD": host.password}  ## Builds Host creds for POST Method
    data = urllib.parse.urlencode(params).encode()

    print("Attempting to connect to " + host.addr + ', using ' + host.type + ' format with username ' + host.username)

    if debugmsg == 1:
        print(
            "Sending authentication request to 'https://" + host.addr + ":443/rpc/WEBSES/create.asp' using provided credentials, ignoring SSL")
    try:
        ssl._create_default_https_context = ssl._create_unverified_context  ##Disables SSL Checks... EVIL
        req = urllib.request.Request('https://' + host.addr + ':443/rpc/WEBSES/create.asp', data=data)
        with urllib.request.urlopen(req, timeout=4) as f:
            buf = f.read().decode('utf-8')
    except HTTPError as e:
        # do something
        print('Error code: ', e.code)
    except URLError as e:
        # do something (set req to blank)
        print('Reason: ', e.reason)
    cookie = re.search("'SESSION_COOKIE'\s:\s'(\w*)'", buf)  ## GET DAT COOKIE
    cookie = cookie.group(1)
    if debugmsg == 1:
        print("Obtained SessionCookie: " + cookie)
    if (cookie.find('Failure') != -1):
        print("Invalid Username or Password...")
        showinfo("Invalid Username or Password...", "Returned session cookie is invalid")
        return

    if debugmsg == 1:
        print("Sending request to 'https://" + host.addr + ":443/Java/jviewer.jnlp' using the captured 'SessionCookie'")

    sessionCookieString = "SessionCookie=" + cookie  ## Conform SessionCookie to format expected for Header
    req = urllib.request.Request('https://' + host.addr + ':443/Java/jviewer.jnlp',
                                 headers={"Cookie": sessionCookieString})
    with urllib.request.urlopen(req, timeout=4) as f:
        buf = f.read(3000).decode('utf-8')
    returnedArgs = re.findall(r'(\<argument\>(\S*)\<\/argument>)', buf, re.MULTILINE)  ### REGEX to extract Java ARGS
    JNLPhost = returnedArgs[0][1]
    JNLPport = returnedArgs[1][1]
    JNLPtoken = returnedArgs[2][1]

    if debugmsg == 1:
        print("Extracted Java Web Start values from returned JNLP")
        print("  Host: " + JNLPhost)
        print("  Port: " + JNLPport)
        print("  Token: " + JNLPtoken)

    print("Launching Java Applet...")
    scrpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    if opsys == "Windows":
        cmd = '"' + scrpath + '\\win-jre\\bin\\javaw.exe" -cp "' + scrpath + '\\c6100\\JViewer.jar" -Djava.library.path="' + scrpath + '\\c6100\\lib" com.ami.kvm.jviewer.JViewer ' + JNLPhost + " " + JNLPport + " " + JNLPtoken
        Popen(cmd)
    elif opsys == "Linux":
        cmd = '"' + scrpath + '/lin-jre/bin/java" -cp "' + scrpath + '/c6100/JViewer.jar" -Djava.library.path="' + scrpath + '/c6100/lib" com.ami.kvm.jviewer.JViewer ' + JNLPhost + " " + JNLPport + " " + JNLPtoken
        os.system(cmd + " &")
    elif opsys == "Darwin":
        cmd = '"' + scrpath + '/osx-jre/bin/java" -cp "' + scrpath + '/c6100/JViewer.jar" com.ami.kvm.jviewer.JViewer ' + JNLPhost + " " + JNLPport + " " + JNLPtoken
        os.system(cmd + " &")

    if debugmsg == 1:
        print("")
        print("Launched with cmd: " + cmd)
        print("Exiting...")

    return


def connC6220(host):
    print("Attempting to connect to " + host.addr + ', using ' + host.type + ' format with username ' + host.username)

    scrpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    if opsys == "Windows":
        cmd = '"' + scrpath + '\\win-jre\\bin\\javaw.exe" -cp "' + scrpath + '\\c6220\\avctKVM.jar" -Djava.library.path="' + scrpath + '\\c6220\\lib" com.avocent.kvm.client.Main C6220 ip=' + host.addr + ' platform=ast2300 vmprivilege=true user=' + host.username + ' passwd=' + host.password + ' kmport=7578 vport=7578 apcp=1 version=2 platform=ASPEED color=0 softkeys=1 statusbar=ip,un,fr,bw,kp,led power=1'
        Popen(cmd, shell=False)
    elif opsys == "Linux":
        cmd = '"' + scrpath + '/lin-jre/bin/java" -cp "' + scrpath + '/c6220/avctKVM.jar" -Djava.library.path="' + scrpath + '/c6220/lib" com.avocent.kvm.client.Main C6220 ip=' + host.addr + ' platform=ast2300 vmprivilege=true user=' + host.username + ' passwd=' + host.password + ' kmport=7578 vport=7578 apcp=1 version=2 platform=ASPEED color=0 softkeys=1 statusbar=ip,un,fr,bw,kp,led power=1'
        os.system(cmd + " &")
    elif opsys == "Darwin":
        cmd = '"' + scrpath + '/osx-jre/bin/java" -cp "' + scrpath + '/c6220/avctKVM.jar" -Djava.library.path="' + scrpath + '/c6220/lib" com.avocent.kvm.client.Main C6220 ip=' + host.addr + ' platform=ast2300 vmprivilege=true user=' + host.username + ' passwd=' + host.password + ' kmport=7578 vport=7578 apcp=1 version=2 platform=ASPEED color=0 softkeys=1 statusbar=ip,un,fr,bw,kp,led power=1'
        os.system(cmd + " &")

    if debugmsg == 1:
        print(cmd)
        showinfo("CMD", cmd)
    return


def conniDRAC6(host):
    print("Attempting to connect to " + host.addr + ', using ' + host.type + ' format with username ' + host.username)

    scrpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    if opsys == "Windows":
        cmd = '"' + scrpath + '\\win-jre\\bin\\javaw.exe" -cp "' + scrpath + '\\idrac6\\avctKVM.jar" -Djava.library.path="' + scrpath + '\\idrac6\\lib" com.avocent.idrac.kvm.Main ip=' + host.addr + ' kmport=5900 vport=5900 user=' + host.username + ' passwd=' + host.password + ' apcp=1 version=2 vmprivilege=true '
        Popen(cmd, shell=False)
    elif opsys == "Linux":
        cmd = '"' + scrpath + '/lin-jre/bin/java" -cp "' + scrpath + '/idrac6/avctKVM.jar" -Djava.library.path="' + scrpath + '/idrac6/lib" com.avocent.idrac.kvm.Main ip=' + host.addr + ' kmport=5900 vport=5900 user=' + host.username + ' passwd=' + host.password + ' apcp=1 version=2 vmprivilege=true '
        os.system(cmd + " &")
    elif opsys == "Darwin":
        cmd = '"' + scrpath + '/osx-jre/bin/java" -cp "' + scrpath + '/idrac6/avctKVM.jar" -Djava.library.path="' + scrpath + '/idrac6/lib" com.avocent.idrac.kvm.Main ip=' + host.addr + ' kmport=5900 vport=5900 user=' + host.username + ' passwd=' + host.password + ' apcp=1 version=2 vmprivilege=true '
        os.system(cmd + " &")

    if debugmsg == 1:
        print(cmd)
        showinfo("CMD", cmd)
    return


def conniDRAC6_Blade(host):
    params = {"WEBVAR_USERNAME": host.username, "WEBVAR_PASSWORD": host.password,
              "WEBVAR_ISCMCLOGIN": "0"}  ## Builds Host creds for POST Method
    data = urllib.parse.urlencode(params).encode()

    print("Attempting to connect to " + host.addr + ', using ' + host.type + ' format with username ' + host.username)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context  ##Disables SSL Checks... EVIL
        req = urllib.request.Request('https://' + host.addr + ':443/Applications/dellUI/RPC/WEBSES/create.asp',
                                     data=data)
        with urllib.request.urlopen(req, timeout=4) as f:
            buf = f.read().decode('utf-8')
    except HTTPError as e:
        # do something
        print('Error code: ', e.code)
    except URLError as e:
        # do something (set req to blank)
        print('Reason: ', e.reason)
    ##print(buf)
    cookie = re.search("'SESSION_COOKIE'\s:\s'(\w*)',", buf)  ## GET DAT COOKIE
    cookie = cookie.group(1)
    print("Conn Phase 1: SessionCookie: " + cookie)
    if (cookie.find('Failure') != -1):
        print("Invalid Username or Password...")
        showinfo("Invalid Username or Password...", "Returned session cookie is invalid")
        return

    sessionCookieString = "SessionCookie=" + cookie  ## Conform SessionCookie to format expected for Header
    req = urllib.request.Request('https://' + host.addr + ':443/Applications/dellUI/Java/jviewer.jnlp',
                                 headers={"Cookie": sessionCookieString})
    with urllib.request.urlopen(req, timeout=4) as f:
        buf = f.read(3000).decode('utf-8')
    returnedArgs = re.findall(r'(\<argument\>(\S*)\<\/argument>)', buf, re.MULTILINE)  ### REGEX to extract Java ARGS
    args = returnedArgs[1][1], returnedArgs[2][1], returnedArgs[3][1], returnedArgs[4][1], returnedArgs[5][1], \
           returnedArgs[6][1], returnedArgs[7][1], returnedArgs[8][1], returnedArgs[9][1], returnedArgs[10][1]
    fullArgs = str(" ".join(args))

    # fullArgs=returnedArgs[0][1].string, returnedArgs[1][1].string

    scrpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    if opsys == "Windows":
        cmd = '"' + scrpath + '\\win-jre\\bin\\javaw.exe" -cp "' + scrpath + '\\idrac6-blade\\JViewer.jar" -Djava.library.path="' + scrpath + '\\idrac6-blade\\lib" com.ami.kvm.jviewer.JViewer ' + host.addr + " " + fullArgs
        Popen(cmd, shell=False)
    elif opsys == "Linux":
        cmd = '"' + scrpath + '/lin-jre/bin/java" -cp "' + scrpath + '/idrac6-blade/JViewer.jar" -Djava.library.path="' + scrpath + '/idrac6-blade/lib" com.ami.kvm.jviewer.JViewer ' + host.addr + " " + fullArgs
        os.system(cmd + " &")
    elif opsys == "Darwin":
        showinfo("Dell iDRAC6 for Blades SUCK",
                 "They don't provide the correct OSX Native Libraries (In particular the Floppy Library WTF?), and for whatever reason, the keyboard doesn't work without it.   I'll Continue to connect without it, but you won't be able to type. Sorry.    In the event you CAN find the libraries, put them in idrac6-blade/lib/")
        cmd = '"' + scrpath + '/osx-jre/bin/java" -cp "' + scrpath + '/idrac6-blade/JViewer.jar" -Djava.library.path="' + scrpath + '/idrac6-blade/lib" com.ami.kvm.jviewer.JViewer ' + host.addr + " " + fullArgs
        os.system(cmd + " &")

    if debugmsg == 1:
        print(cmd)
        showinfo("CMD", cmd)
    return


def connIBMSystemX(host):
    data = f"USERNAME={host.username},PASSWORD={host.password}".encode()  ## Builds Host creds for POST Method

    print("Attempting to connect to " + host.addr + ', using ' + host.type + ' format with username ' + host.username)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context  ##Disables SSL Checks... EVIL
        req = urllib.request.Request('https://' + host.addr + ':443/session/create', data=data)
        with urllib.request.urlopen(req, timeout=4) as f:
            buf = f.read().decode('utf-8')
    except HTTPError as e:
        # do something
        print('Error code: ', e.code)
    except URLError as e:
        # do something (set req to blank)
        print('Reason: ', e.reason)
    ##print(buf)
    cookie = re.search("\w+(?:-\w+)+", buf)  ## GET DAT COOKIE
    if (cookie == None):
        print("Invalid Username or Password...")
        showinfo("Invalid Username or Password...", "No returned session cookie")
        return

    cookie = cookie.group(0)
    print("Conn Phase 1: session_id: " + cookie)

    sessionCookieString = "session_id=" + cookie  ## Conform SessionCookie to format expected for Header
    try:
        req = urllib.request.Request('https://' + host.addr + ':443/kvm/kvm/jnlp',
                                     headers={"Cookie": sessionCookieString})
        with urllib.request.urlopen(req, timeout=20) as f: ## Generating jnlp file can take a while !
            buf = f.read(3000).decode('utf-8')
    except HTTPError as e:
        # do something
        print('Error code: ', e.code, e.reason, buf)
    except URLError as e:
        # do something (set req to blank)
        print('Reason: ', e.reason)
    returnedArgs = re.findall(r'(\<argument\>(.*)\<\/argument>)', buf, re.MULTILINE)  ### REGEX to extract Java ARGS
    fullArgs = ''
    for arg in returnedArgs:
        arg_parts = arg[1].split('=')
        fullArgs += f' {arg_parts[0]}="{arg_parts[1]}"'

    scrpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    if opsys == "Windows":
        cmd = '"' + scrpath + '\\win-jre\\bin\\javaw.exe" -cp "' + scrpath + '\\ibm-systemx\\avctIBMViewer.jar" -Djava.library.path="' + scrpath + '\\ibm-systemx\\lib" com.avocent.ibmc.kvm.Main ' + host.addr + " " + fullArgs
        Popen(cmd, shell=False)
    elif opsys == "Linux":
        cmd = '"' + scrpath + '/lin-jre/bin/java" -cp "' + scrpath + '/ibm-systemx/avctIBMViewer.jar" -Djava.library.path="' + scrpath + '/ibm-systemx/lib" com.avocent.ibmc.kvm.Main ' + host.addr + " " + fullArgs
        os.system(cmd + " &")
    elif opsys == "Darwin":
        showinfo("IBM Remote Control KVM for System X SUCK",
                 "IBM (Avocent) don't provide the IO OSX Native Libraries, but the keyboard work without it. So I'll continue to connect without it. Sorry. In the event you CAN find the libraries, put them in ibm-systemx/lib/. Note that the Virtual Media app will not work.")
        cmd = '"' + scrpath + '/osx-jre/bin/java" -cp "' + scrpath + '/ibm-systemx/avctIBMViewer.jar" -Djava.library.path="' + scrpath + '/ibm-systemx/lib" com.avocent.ibmc.kvm.Main ' + host.addr + " " + fullArgs
        os.system(cmd + " &")

    if debugmsg == 1:
        print(cmd)
        showinfo("CMD", cmd)
    return


def formconninit(hostforminfo):
    ##Copy user entries from form into hostInfo class
    host = hostInfo(hostforminfo[0].get(), hostforminfo[1].get(), hostforminfo[2].get(), hostforminfo[3].get())

    ## What type of host is this?
    if host.type == "C6100":
        connC6100(host)
    elif host.type == "C6220":
        connC6220(host)
    elif host.type == "iDRAC6":
        conniDRAC6(host)
    elif host.type == "iDRAC6-Blade":
        conniDRAC6_Blade(host)
    elif host.type == "IBM-SystemX":
        connIBMSystemX(host)
    elif host.type == "iDRAC7":
        showinfo("Do you really need this?  If so, contact Nick")


def makeform(root):
    hostinfo = []

    row1 = Frame(root)
    hosttypelabel = Label(row1, width=15, text="DRAC Type", anchor='w')
    ht = StringVar()
    ht.set(defaultType)
    hosttype = OptionMenu(row1, ht, *hosttypes)
    row1.pack(side=TOP, fill=X, padx=5, pady=5)
    hosttypelabel.pack(side=LEFT)
    hosttype.pack(side=RIGHT, expand=YES, fill=X)

    row2 = Frame(root)
    hostnamelabel = Label(row2, width=15, text="Hostname", anchor='w')
    hostname = Entry(row2)
    hostname.insert(0, defaultHost)
    row2.pack(side=TOP, fill=X, padx=5, pady=5)
    hostnamelabel.pack(side=LEFT)
    hostname.pack(side=RIGHT, expand=YES, fill=X)

    row3 = Frame(root)
    usernamelabel = Label(row3, width=15, text="Username", anchor='w')
    username = Entry(row3)
    username.insert(0, defaultUser)
    row3.pack(side=TOP, fill=X, padx=5, pady=5)
    usernamelabel.pack(side=LEFT)
    username.pack(side=RIGHT, expand=YES, fill=X)

    row4 = Frame(root)
    passwordlabel = Label(row4, width=15, text="Password", anchor='w')
    password = Entry(row4, show='*')
    password.insert(0, defaultPass)
    row4.pack(side=TOP, fill=X, padx=5, pady=5)
    passwordlabel.pack(side=LEFT)
    password.pack(side=RIGHT, expand=YES, fill=X)

    hostinfo = [hostname, ht, username, password]
    return hostinfo


def cliconninit(hostname, hosttype, username, password):
    ##Copy user entries from variables into class
    host = hostInfo(hostname, hosttype, username, password)

    ## What type of host is this?
    if host.type == "C6100":
        connC6100(host)
    elif host.type == "C6220":
        connC6220(host)
    elif host.type == "iDRAC6":
        conniDRAC6(host)
    elif host.type == "iDRAC6-Blade":
        conniDRAC6_Blade(host)
    elif host.type == "IBM-SystemX":
        connIBMSystemX(host)
    elif host.type == "iDRAC7":
        showinfo("Do you really need this?  If so, contact Nick")


if __name__ == '__main__':
    opsys = platform.system()

    print("== μDRAC " + ver + " Multiplatform Edition")
    print("== OS Detected as " + opsys)

    if len(sys.argv) > 1:
        print("== CLI Mode")
        hostname = ""
        hosttype = ""
        username = ""
        password = ""

        parser = argparse.ArgumentParser()

        parser.add_argument("-a", "--hostname", "--host", "--address", help="IP or Hostname of the OOB server",
                            required=True)
        parser.add_argument("-t", "--type", help="the Dell iDRAC type",
                            choices=["C6100", "C6220", "iDRAC6", "iDRAC6-Blade", "IBM-SystemX"], required=True)
        parser.add_argument("-u", "--username", help="Username", required=True)
        parser.add_argument("-p", "--password", help="Password, Please use quotes for anything special", required=True)
        parser.add_argument("-d", "--debug", help="Increase debug messages", action="store_true")
        args = parser.parse_args()

        if args.debug:
            debugmsg = 1

        cliconninit(args.hostname, args.type, args.username, args.password)

    else:
        print("== GUI Mode")
        root = Tk()
        form = makeform(root)
        root.title("μDRAC " + ver)
        root.bind('<Return>', (lambda event, e=form: formconninit(e)))

        btnconn = Button(root, text='Connect', command=(lambda e=form: formconninit(e)))
        btnconn.pack(side=LEFT, padx=5, pady=5)
        btnquit = Button(root, text='Quit', command=root.quit)
        btnquit.pack(side=LEFT, padx=5, pady=5)

        root.mainloop()
