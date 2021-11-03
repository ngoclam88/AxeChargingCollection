from ftplib import FTP
import os, csv

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

if __name__ == "__main__":
    ftp_ip = "10.204.202.5"
    ftp_usr = "ktm_noc3"
    ftp_pwd = "vnpt@123"
    ftp_client = FTP(ftp_ip)
    ftp_client.login(user=ftp_usr, passwd=ftp_pwd)
    ftp_client.cwd('/cp/files/ISTFILES/ISTFILES')
    # print(ftp_client.pwd())
    print(ftp_client.retrlines('LIST'))

    filename = '20211028162052MSSE3A-BC0+ISTRAFILE00-0000000369.pcap'
    grabFile(ftp_client, filename)
    # print(ftp_client.size(filename))
    ftp_client.quit()
