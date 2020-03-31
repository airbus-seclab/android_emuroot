import argparse 
import logging 

# imports for emuroot
import pygdbmi
from pygdbmi.gdbcontroller import GdbController
from pprint import pprint
import threading
import time



try:
    from adb.client import Client as AdbClient
except:
    from ppadb.client import Client as AdbClient
      

##################### ADB functions #############################
'''
This function returns the kernel version

'''
def kernel_version(): 
    client = AdbClient(host="127.0.0.1", port=5037) 
    device = client.device(options.device)       
    if device == None:
        logging.info("Device name %s invalid. Check \"adb devices\" to get valid ones", options.device)
        raise Exception("Device name invalid. Check \"adb devices\" to get valid ones")
    result = device.shell("uname -r")
    #result = result.encode('ascii','ignore')
    logging.info(" kernel_version() : result is %s", result)
    result = result.split(".")
    ver = result[0]+'.'+result[1]
    ver = float(ver)

    offset_selinux = [] 
      # case kernel version is <= 3.10
    if ver <= 3.10 :
        offset_to_comm = 0x288
        offset_to_parent = 0xe0
        offset_selinux.append(0xC0A77548)
        offset_selinux.append(0xC0A7754C)
        offset_selinux.append(0xC0A77550)
        ps_cmd = "ps"

    # case kernel version is > 3.10 et <=3.18
    elif ver > 3.10 and ver <= 3.18 :
        offset_to_comm = 0x444
        offset_to_parent = 0xe0
        offset_selinux.append(0xC0C4F288) 
        offset_selinux.append(0xC0C4F28C)
        offset_selinux.append(0XC0C4F280)
        ps_cmd = "ps -A"
        
    else :
        logging.info("Sorry. Android kernel version %s not supported yet", str(ver))
        raise NotImplementedError("Sorry. Android kernel version not supported yet")
    return ver,offset_to_comm,offset_to_parent,offset_selinux,ps_cmd

'''
This function checks if a given process is running (with  adb shell 'ps' command)
'''
def check_process_is_running(process, pscmd, devicename):
    client = AdbClient(host="127.0.0.1", port=5037)
    device = client.device(devicename)
    if device == None:
        logging.info("Device name %s invalid. Check \"adb devices\" to get valid ones", device)
        raise Exception("Device name invalid. Check \"adb devices\" to get valid ones")
    ps = device.shell(pscmd)
    if process in ps:
        logging.info("[+] OK. %s is running" %(process))
    else:
        logging.info("[+] NOK. It seems like %s is not running..." %(process))
        logging.info("[+] Android_Emuroot stopped")
        exit(1)

'''
This method is in charge to launch load.sh in background 
The script copy /system/bin/sh to /data/local/tmp and attempt to change its owner to root  in a loop
'''
def adb_stager_process(load, devicename):
    '''
    Adb connexion 
    TODO specify the device id
    '''
    logging.info("[+] Launch the stager process")
    client = AdbClient(host="127.0.0.1", port=5037)
    device = client.device(devicename)

    device.shell("echo "+load+" > /data/local/tmp/load.sh")
    device.shell("chmod +x /data/local/tmp/load.sh")
    device.shell("ln -s /system/bin/sh /data/local/tmp/STAGER")

    # Launch STAGER shell

    device.shell("/data/local/tmp/STAGER /data/local/tmp/load.sh")

'''
This function cleans the file system by removing the stager binaries created in adb_stager_process
'''
def stager_clean(devicename):
    logging.info("[+] Clean the stager process")
    client = AdbClient(host="127.0.0.1", port=5037)
    device = client.device(devicename)

    device.shell("rm /data/local/tmp/load.sh /data/local/tmp/STAGER")


##################### GDB functions #############################


class GDB_stub_controller(object):
    def __init__(self, options):
        self.options = options
        logging.info(" [+] Start the GDB controller and attach it to the remote target")
        logging.info(" [+] GDB additional timeout value is %d" % int(options.timeout) )
        self.gdb = GdbController(time_to_check_for_additional_output_sec=int(options.timeout))
        response = self.gdb.write("target remote :1234")
        isrunning = 0
        for f in response:
            if ("payload" in f) and (f["payload"] !=None) and ("Remote debugging" in f["payload"]):	                
                logging.info(" [+] GDB server reached. Continue")
                isrunning = 1
                break
        if isrunning == 0:
            logging.info("GDB server not reachable. Did you start it?")
            self.stop()
            raise Exception("GDB server not reachable. Did you start it?")

    def stop(self):
        logging.info(" [+] Detach and stop GDB controller")
        self.gdb.exit()

    def write(self, addr, val):
        logging.info(" [+] gdb.write addr: %#x value : %#x"%(addr,val))
        self.gdb.write("set *(unsigned int*) (%#x) = %#x" % (addr, val))

    def read(self, addr):
        r = self.gdb.write("x/6xw %#x" % addr)[1].get('payload').split('\\t')[1]
        logging.info(" [+] Gdb.read %s "%(r))
        r = int(r,16)
        return r 
        #int(self.gdb.write("x/6xw %#x" % addr)[1].get('payload').split('\\t')[1],16)

    '''
    This function sets SELinux enforcement to permissive
    '''
    def disable_selinux(self):
        logging.info("[+] Disable SELinux")
        logging.info("[+] Offsets are  %s - %s - %s "%( hex(self.options.offset_selinux[0]),hex(self.options.offset_selinux[0]),hex(self.options.offset_selinux[0])))

        self.write(self.options.offset_selinux[0], 0)
        self.write(self.options.offset_selinux[1], 0)
        self.write(self.options.offset_selinux[2], 0)

    '''
    This function sets all capabilities of a task to 1
    '''
    def set_full_capabilities(self,cred_addr):
        logging.info("[+] Set full capabilities")
        for ofs in [0x30, 0x34, 0x38, 0x3c, 0x40, 0x44]:
            self.write(cred_addr+ofs, 0xffffffff)

    '''
    This function sets all Linux IDs of a task to 0 (root user)
    @effective: if False, effective IDs are not modified 
    '''
    def set_root_ids(self, cred_addr, effective=True):
        logging.info("[+] Set root IDs")
        for ofs in [0x04, 0x08, 0x0c, 0x10, 0x1c, 0x20]: # uid, gid, suid,sgid, fsuid, fsgid
            self.write(cred_addr+ofs, 0x00000000)
        if effective:
            self.write(cred_addr+0x14, 0x00000000) # euid
            self.write(cred_addr+0x18, 0x00000000) # egid
        else:
            logging.info("[+] Note: effective ID have not been changed")

    '''
    This function returns the task_struct addr for a given process name
    '''
    def get_process_task_struct(self, process):
        logging.info(" [+] Get address aligned whose process name is: [%s]" % process)
        logging.info(" [+] This step can take a while (GDB timeout: %dsec). Please wait..." % int(options.timeout) )
        response = self.gdb.write("find 0xc0000000, +0x40000000, \"%s\"" % process,
                                  raise_error_on_timeout=True, read_response=True,
                                  timeout_sec=int(options.timeout))
        # author : m00dy , 15/11/2018
        # response[0] contains the gdb command line
        # I remove the first element before looping in response list
        response.pop(0)
        addresses = []
        for m in response:
            # check if the payload starts with 0x because a response could be an error
            if m.get('payload') != None and m.get('payload')[:-2].startswith('0x'):
                #print (" payload is %s "%(m.get('payload')[:-2]))
                val = int(m.get('payload')[:-2],16)
                if val%16 == self.options.offset_to_comm%16:
                    addresses.append(val)


        for a in addresses:
            response = self.gdb.write("x/6xw %#x" % (a - 8))
            magic_cred_ptr = response[1].get('payload').split('\\t')
            magic_addr = ""
            if ( magic_cred_ptr[1] !=0 and (magic_cred_ptr[1]) == (magic_cred_ptr[2]) ):
                magic_addr = a
                return magic_addr - self.options.offset_to_comm
        return 0

    '''
    This function returns the cred_struct address of adbd process from a given stager process
    '''
    def get_adbd_cred_struct(self, stager_addr):
        logging.info("[+] Search adbd task struct in the process hierarchy")
        adbd_cred_ptr = ""
        cur = stager_addr
        while True:
            parent_struct_addr = int(self.gdb.write("x/6xw %#x" % (cur + self.options.offset_to_comm - self.options.offset_to_parent))[1].get('payload').split('\\t')[1],16)
            print(parent_struct_addr)
            parent_struct_name = self.gdb.write("x/s %#x" % (parent_struct_addr + self.options.offset_to_comm))[1].get('payload').split('\\t')[1]
            if (str(parent_struct_name) == r'\"adbd\"'):
                adbd_cred_ptr = int(self.gdb.write("x/6xw %#x" % (parent_struct_addr + self.options.offset_to_comm - 4))[1].get('payload').split('\\t')[1],16)
                break
            cur = parent_struct_addr
        return adbd_cred_ptr

##################### Emuroot options ###########################
'''
This function looks for the task struct and cred structure
for a given process and patch its cred ID and capabilities
@options: argparse namespace. Uses options.magic_name.
'''
def single_mode(options):
    logging.info("[+] Entering single function process name is %s " %(options.magic_name))
    logging.info("[+] Check if %s is running " %(options.magic_name))

    # Check if the process is running
    check_process_is_running(options.magic_name, options.ps_cmd, options.device)

    # Get task struct address
    gdbsc = GDB_stub_controller(options)
    magic = gdbsc.get_process_task_struct(options.magic_name)
    logging.info("[+] singel_mode(): process task struct of magic is %s "%(magic))

     # Replace the shell creds with id 0x0, keys 0x0, capabilities 0xffffffff
    logging.info("[+] single_mode(): Replace the process creds with id 0x0, keys 0x0, capabilities 0xffffffff")
    print ("magic is %s " %(hex(magic)))
    print (" magic cred is at %s "%hex(magic+options.offset_to_comm-8) )
    magic_cred_ptr = gdbsc.read(magic+options.offset_to_comm-8)
    logging.info("[+] single_mode(): magic_cred_ptr is %s "%hex(magic_cred_ptr))
    gdbsc.set_root_ids(magic_cred_ptr)
    gdbsc.set_full_capabilities(magic_cred_ptr)

    gdbsc.disable_selinux()
    gdbsc.stop()

'''
This function install a sh with suid root on the file system
@options: argparse namespace. Uses options.path.
'''
def setuid_mode(options):
    logging.info("[+] Rooting with Android Emuroot via a setuid binary...")

    script = """'#!/bin/bash
cp /system/bin/sh /data/local/tmp/{0}
while :; do
  sleep 5
  if chown root:root /data/local/tmp/{0}; then break; fi
done
mount -o suid,remount /data
chmod 4755 /data/local/tmp/{0}'""".format(options.path)

    thread = threading.Thread(name='adb_stager',target=adb_stager_process, args=(script,options.device))
    thread.start()
    time.sleep(5) # to be sure STAGER has been started

    check_process_is_running("STAGER", options.ps_cmd, options.device)
    gdbsc = GDB_stub_controller(options)
    magic = gdbsc.get_process_task_struct("STAGER")

    adbd_cred_ptr = gdbsc.get_adbd_cred_struct(magic)
    gdbsc.set_full_capabilities(adbd_cred_ptr)

    gdbsc.disable_selinux()

    magic_cred_ptr = gdbsc.read(magic + options.offset_to_comm - 8)
    gdbsc.set_root_ids(magic_cred_ptr)
    gdbsc.set_full_capabilities(magic_cred_ptr)

    gdbsc.stop()
    stager_clean(options.device)


'''
This function elevates the privileges of adbd process
@options: argparse namespace. Uses options.stealth.
'''
def adbd_mode(options):
    logging.info("adbd mode is chosen")
    logging.info("[+] Rooting with Android Emuroot via adbd...")

    script = """'#!/bin/bash
cp /system/bin/sh /data/local/tmp/probe
isRoot=0
while :; do
  sleep 5
  if chown root:root /data/local/tmp/probe; then break; fi
done
sleep 5
rm rm /data/local/tmp/probe'"""

    thread = threading.Thread(name='adb_stager',target=adb_stager_process, args=(script,options.device))
    thread.start()
    time.sleep(5) # to be sure STAGER has been started

    check_process_is_running("STAGER", options.ps_cmd, options.device)
    gdbsc = GDB_stub_controller(options)
    magic = gdbsc.get_process_task_struct("STAGER")

    adbd_cred_ptr = gdbsc.get_adbd_cred_struct(magic)
    gdbsc.set_full_capabilities(adbd_cred_ptr)
    gdbsc.set_root_ids(adbd_cred_ptr, effective = not options.stealth)

    gdbsc.disable_selinux()

    magic_cred_ptr = gdbsc.read(magic + options.offset_to_comm - 8)
    gdbsc.set_root_ids(magic_cred_ptr)
    gdbsc.set_full_capabilities(magic_cred_ptr)

    gdbsc.stop()
    stager_clean(options.device)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Usage:")

    parser.add_argument("-v", "--version", action="version", version='%(prog)s version is 1.0')
    parser.add_argument("-V", "--verbose", action="count", default=0, help="increase verbosity")
    parser.add_argument("-t", "--timeout", help="set the GDB timeout value (in seconds)", default=60)
    parser.add_argument("-d", "--device", help="specify the device name (as printed by \"adb device\", example: emulator-5554)", default="emulator-5554")

    subparsers = parser.add_subparsers(title="modes")

    parser_single = subparsers.add_parser("single", help="elevates privileges of a given process")
    parser_single.add_argument("--magic-name", required=True,
                               help="name of the process, that will be looked for in memory")
    parser_single.set_defaults(mode_function = single_mode)

    parser_adbd = subparsers.add_parser("adbd", help="elevates adbd privileges")
    parser_adbd.add_argument("--stealth", action="store_true",
                             help="try to make it less obvious that adbd has new privileges")
    parser_adbd.set_defaults(mode_function = adbd_mode)

    parser_setuid = subparsers.add_parser("setuid", help="creates a setuid shell launcher")
    parser_setuid.add_argument("--path", required=True, help="path to setuid shell to create")
    parser_setuid.set_defaults(mode_function = setuid_mode)

    # parse the arguments
    options = parser.parse_args()
    if not hasattr(options, "mode_function"):
        parser.error("Too few arguments")

    # set logging params
    loglevel = 50 - (10*options.verbose) if options.verbose > 0 else logging.INFO
    logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

    # pin down android kernel version
    options.version, options.offset_to_comm, options.offset_to_parent , options.offset_selinux, options.ps_cmd = kernel_version()

    # run the selected mode
    options.mode_function(options)
