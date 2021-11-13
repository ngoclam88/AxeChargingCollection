import os, ipaddress, logging, time, datetime, sched, telnetlib
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
    HOST = os.environ.get("DiaChiIP")
    user = os.environ.get("tendangnhap")
    password = os.environ.get("matkhau")
    destname = os.environ.get("dest")
    vol1 = os.environ.get("vol1")
    cmd_infmt = "infmt:dest=" + destname + ",vol1=" + vol1 + ";"
    if validate_ip_address(HOST):
        if destname.strip() != '' and vol1.strip() != '':
            try:
                tn = telnetlib.Telnet(HOST, port=5000)
                tn.read_until(b"USERCODE:",5)
                tn.write(user.encode('ascii') + b"\r\n")
                tn.read_until(b"PASSWORD:",5)
                tn.write(password.encode('ascii') + b"\r\n")
                login_result = tn.read_some().decode('ascii')
                if login_result.count("AUTHORIZATION FAILURE"):
                    print("Sai ten dang nhap hoac mat khau. Vui long kiem tra lai")
                    tn.close()
                    input()
                else:
                    tn.read_until(b"<")
                    # Lay danh sach file cuoc can lay
                    tn.write(b"infsp:file=ttfile00,dest=charging;" + b"\r\n")
                    cmd_infsp_out = tn.read_until(b"<").decode('ascii')

                    # Chay lenh chuyen file cuoc tu dest sang vol1:
                    print(cmd_infmt)
                    # tn.write(cmd_infmt.encode('ascii') + b"\r\n")
                    # tn.read_until(b"<")

                    # Dong ket noi telnet
                    tn.close()
                    return getFileList(cmd_infsp_out)

            except TimeoutError:
                print(f"Khong the ket noi den duoc node mang {HOST}")
                return []
        else:
            print('Thong so dest hoac vol1 khong duoc de trong. Vui long kiem tra lai')
            input()
    else:
        print("Dia chi IP khong dung dinh dang. Vui long kiem tra lai")
        input()
    

if __name__ == "__main__":
    greeting = 'Chương trình tự động lấy file cước tổng đài AXE. Copyright: lamlnn@vnpt.vn. All rights reserved.'
    print("-"*100 + "\n" + greeting + "\n" + "-"*100)
    # main()
    # telnet_n_getFileList = os.environ.get("sample")
    # lstFile = getFileList(os.environ.get("sample"))
    lstFile = telnet_n_getFileList()

    # Neu lstFile khong phai la rong thi thuc hien tiep
    if not len(lstFile):
        pass