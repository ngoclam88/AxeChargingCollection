import os, ipaddress, logging, time, telnetlib
from logging.handlers import RotatingFileHandler
from ftplib import FTP
import threading
lock = threading.Lock()
from dotenv import load_dotenv
load_dotenv()

debug_logger = logging.getLogger(f'DebugLogger')
debug_logger.setLevel(logging.DEBUG)
debug_formatter = logging.Formatter('%(asctime)s %(name)s %(message)s')
debug_handler = RotatingFileHandler(filename=f'debug_log.log', maxBytes=10000, backupCount=9) #9 file backup log
debug_handler.setFormatter(debug_formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(debug_formatter)
debug_logger.addHandler(debug_handler)
debug_logger.addHandler(stream_handler)

def grabFile(ftp, filename):
    path = "./CDR"
    os.makedirs(path, exist_ok=True)
    localfile = open(path + "/" + filename, 'wb')
    try:
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
        debug_logger.debug(f"Download {filename} OK")
    except:
        debug_logger.debug (f"Error while getting {filename}")    
    localfile.close()

def validate_ip_address(address):
    try:
        ip = ipaddress.ip_address(address)
        return address
    except ValueError:
        return False

# def axe_logger(nodename):
#     path = "./log/" + nodename
#     os.makedirs(path, exist_ok=True)
#     debug_logger = logging.getLogger(f'DebugLogger_{nodename}')
#     debug_logger.setLevel(logging.DEBUG)
#     debug_formatter = logging.Formatter('%(asctime)s %(name)s %(message)s')
#     debug_handler = RotatingFileHandler(filename=f'{path}/debug_{nodename}.log', maxBytes=10000, backupCount=9) #9 file backup log
#     debug_handler.setFormatter(debug_formatter)
#     stream_handler = logging.StreamHandler()
#     stream_handler.setFormatter(debug_formatter)
#     debug_logger.addHandler(debug_handler)
#     debug_logger.addHandler(stream_handler)
#     return debug_logger

def getChargingFile(ne, lstFile, disk):
        # logger.debug(f"Connecting to {ne_list[0]}")
    ftp_ip = ne[0]
    ftp_usr = ne[1].upper()
    ftp_pwd = ne[2].upper()
    ftp_client = FTP(ftp_ip)
    debug_logger.debug(f"Trying to FTP to node {ftp_ip}")
    ftp_client.login(user=ftp_usr, passwd=ftp_pwd)
    if disk.upper()[0:4] == 'VODA':
        ftp_client.cwd('OD_A')
    elif disk.upper()[0:4] == 'VODB':
        ftp_client.cwd('OD_B')
    else:
        debug_logger.debug("Khong the login vao thu muc chua file cuoc, vui long kiem tra lai thong so vol1 trong file cau hinh")
    for item in lstFile:
        grabFile(ftp_client, 'TTFILE' + item.zfill(6))
    # print(ftp_client.retrlines('LIST'))
    ftp_client.quit()

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
        
def telnet_n_getFileList(host, user, password):
    destname = os.environ.get("dest")
    vol1 = os.environ.get("vol1")
    cmd_infmt = "infmt:dest=" + destname + ",vol1=" + vol1 + ";"
    cmd_infsp = "infsp:file=ttfile00,dest=" + destname + ";"
    if destname.strip() != '' and vol1.strip() != '':
        try:
            debug_logger.debug(f"Trying to telnet to node {host}")
            tn = telnetlib.Telnet(host, port=5000)
            tn.read_until(b"USERCODE:",5)
            tn.write(user.encode('ascii') + b"\r\n")
            tn.read_until(b"PASSWORD:",5)
            tn.write(password.encode('ascii') + b"\r\n")
            login_result = tn.read_some().decode('ascii')
            if login_result.count("AUTHORIZATION FAILURE"):
                debug_logger.debug("Sai ten dang nhap hoac mat khau. Vui long kiem tra lai")
                tn.close()
                input()
                return []
            else:
                tn.read_until(b"<")
                # Lay danh sach file cuoc can lay
                tn.write(cmd_infsp.encode('ascii') + b"\r\n")
                cmd_infsp_out = tn.read_until(b"<").decode('ascii')

                # Chay lenh chuyen file cuoc tu dest sang vol1:
                print(cmd_infmt)
                # tn.write(cmd_infmt.encode('ascii') + b"\r\n")
                # tn.read_until(b"<")

                # Dong ket noi telnet
                tn.close()
                return getFileList(cmd_infsp_out)

        except TimeoutError:
            debug_logger.debug(f"Khong the ket noi den duoc node mang {host}")
            return []
    else:
        debug_logger.debug('Thong so dest hoac vol1 khong duoc de trong. Vui long kiem tra lai')
        return []
        input()
    

if __name__ == "__main__":
    greeting = 'Chương trình tự động lấy file cước tổng đài AXE. Copyright: lamlnn@vnpt.vn. All rights reserved.'
    print("-"*100 + "\n" + greeting + "\n" + "-"*100)
    host = os.environ.get("DiaChiIP")
    user = os.environ.get("tendangnhap")
    password = os.environ.get("matkhau")

    if validate_ip_address(host):
        lstFile = telnet_n_getFileList(host, user, password)
        print(lstFile)
        lstFile = getFileList(os.environ.get("sample"))
        # Neu lstFile khong phai la rong thi thuc hien tiep
        if len(lstFile) != 0:
            # Cho 5 phut thuc hien ftp lay file
            for phut in range(5): 
                time.sleep(1) #Sua cho nay thanh 60s ne
            getChargingFile([host, user, password], lstFile, disk=os.environ.get("vol1"))
    else:
        # print("Dia chi IP khong dung dinh dang. Vui long kiem tra lai")
        debug_logger.debug("Dia chi IP khong dung dinh dang. Vui long kiem tra lai")

        input()    
    # telnet_n_getFileList = os.environ.get("sample")
    

        