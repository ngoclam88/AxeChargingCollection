import os, csv, ipaddress, logging, time, datetime, sched
from logging.handlers import RotatingFileHandler
from ftplib import FTP

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
    return {'debug_logger':debug_logger}

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
        for ne in ne_dict:
            logger = axe_logger(ne)
            list_logger.append(logger)
        print("Chương trình định kỳ 60 phút lấy file cước")

if __name__ == "__main__":
    greeting = 'Chương trình tự động lấy file cước tổng đài AXE. Copyright: lamlnn@vnpt.vn. All rights reserved.'
    print("-"*100 + "\n" + greeting + "\n" + "-"*100)
    main()