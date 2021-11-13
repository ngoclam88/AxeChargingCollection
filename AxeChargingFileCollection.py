import os, csv, ipaddress, logging, time, datetime, sched, telnetlib
import concurrent.futures
from logging.handlers import RotatingFileHandler
from ftplib import FTP
import threading
lock = threading.Lock()
from dotenv import load_dotenv
load_dotenv()

def grabFile(ftp, filename):
    localfile = open(filename, 'wb')
    try:
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
    except:
        print ("Error")
    # ftp.quit()
    print(f"Download {filename} OK")
    localfile.close()
    print(os.path.getsize(filename))

def validate_ip_address(address):
    try:
        ip = ipaddress.ip_address(address)
        return address
    except ValueError:
        return False

def axe_logger(nodename):
    path = "./log/" + nodename
    os.makedirs(path, exist_ok=True)
    debug_logger = logging.getLogger(f'DebugLogger_{nodename}')
    debug_logger.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter('%(asctime)s %(name)s %(message)s')
    debug_handler = RotatingFileHandler(filename=f'{path}/debug_{nodename}.log', maxBytes=10000, backupCount=9) #9 file backup log
    debug_handler.setFormatter(debug_formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)
    debug_logger.addHandler(stream_handler)
    return debug_logger

def doGetChargingFile(ne_dict, list_logger):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        index = 0
        for ne_name in ne_dict:
            executor.submit(getChargingFile, ne_list=ne_dict[ne_name], logger=list_logger[index])
            index += 1 

def getChargingFile(ne_list, logger):
    with lock:
        logger.debug(f"Connecting to {ne_list[0]}")
    ftp_ip = ne_list[0]
    ftp_usr = ne_list[1]
    ftp_pwd = ne_list[2]
    ftp_client = FTP(ftp_ip)
    ftp_client.login(user=ftp_usr, passwd=ftp_pwd)
    ftp_client.cwd('/cp/files/ISTFILES/ISTFILES')
    # print(ftp_client.retrlines('LIST'))
    ftp_client.mlsd(path='/cp/files/ISTFILES/ISTFILES')
    
def main():
    ne_dict = {}
    error_or_not = True
    try:
        with open('config.csv', mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    ne_dict[row["NE name"]] = [row["NE IP"].strip(), row["Username"].strip(), row["Password"].strip()]
        error_or_not = False
    except FileNotFoundError:
        print("Chương trình không tìm thấy file cấu hình (config.csv). Vui lòng kiểm tra lại.")
    except KeyError:
        print("File cấu hình (config.csv) không đúng định dạng mặc định. Vui lòng kiểm tra lại.")

    if not error_or_not:
        for ne in ne_dict:
            if ne.strip()=='':
                print("Tên node mạng để trống. Vui lòng kiểm tra lại file cấu hình (config.csv)")
                error_or_not = True
            elif not validate_ip_address(ne_dict[ne][0]):
                print(f"Vui lòng kiểm tra lại địa chỉ IP của node mạng {ne}")
                error_or_not = True
            elif ne_dict[ne][1]=='' or ne_dict[ne][2]=='':
                print("User name hoặc password node mạng {ne} bỏ trống. Vui lòng kiểm tra lại file cấu hình (config.csv)")
                error_or_not = True
                
    if not error_or_not:
        list_logger = []
        for ne_name in ne_dict:
            logger = axe_logger(ne_name)
            list_logger.append(logger)
        print("Chương trình định kỳ 60 phút lấy file cước")
        doGetChargingFile(ne_dict, list_logger)

def getFileList(cmd_output):
    start = False
    lstFile = []
    for line in cmd_output.splitlines():
        if line.count("END"):
            start = False
        elif start and line.strip() !="":
            # chi lay dung dong co cot DUMPED = NO
            if line.split()[3] == 'NO':
                lstFile.append(line.split()[0])
        elif line.count("SEQNUM"):
            start = True
    return lstFile
        
def telnet_n_getFileList():
    HOST = os.environ.get("HOST_IP")
    user = os.environ.get("username")
    password = os.environ.get("password")

    tn = telnetlib.Telnet(HOST, port=5000)
    tn.read_until(b"USERCODE:",5)
    tn.write(user.encode('ascii') + b"\r\n")
    tn.read_until(b"PASSWORD:",5)
    tn.write(password.encode('ascii') + b"\r\n")
    tn.read_until(b"<")
    tn.write(b"infsp:file=ttfile00,dest=charging;" + b"\r\n")
    cmd_output = tn.read_until(b"<").decode('ascii')
    return getFileList(cmd_output)
    

if __name__ == "__main__":
    greeting = 'Chương trình tự động lấy file cước tổng đài AXE. Copyright: lamlnn@vnpt.vn. All rights reserved.'
    print("-"*100 + "\n" + greeting + "\n" + "-"*100)
    # main()
    infsp = os.environ.get("sample")
    getFileList(infsp)