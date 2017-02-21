import os,sys
import time
import argparse
import MySQLdb as mariadb

def generate_csv(datafile, year):

    file_in = open(datafile,'r')
    file_out = open('network_attack.csv','w')

    for line in open(datafile):
        line = file_in.readline()
        if "[**]" in line:
           snort_alert_id = line.split()[1].strip('[').strip(']')
        elif "->" in line:
           date_time = line.split(".")[0].replace('-',' ').replace('/','-')
           date_string =  year+"-"+date_time
           utc_time = time.mktime(time.strptime(date_string,'%Y-%m-%d %H:%M:%S'))

           source = line.split()[1]
           source_ip = source.split(":")[0]
           source_port = source.split(":")[1]

           destination = line.split()[3]
           destination_ip = destination.split(":")[0]
           destination_port = destination.split(":")[1]

        elif "TTL" in line:
           protocol = line.split()[0]
           file_out_str = snort_alert_id + ";" + str(utc_time) + ";" + source_ip + ";" + source_port + ";" + protocol + ";"+ destination_ip + ";" + destination_port + "\n"

           file_out.write(file_out_str)
    file_in.close()
    file_out.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), add_help=True)

    parser.add_argument('--year', dest='year', action='store', required=True, help='Please enter the record year')
    parser.add_argument('--datafile', dest='datafile', action='store', required=True, help='Please enter the path of the data file')

    args = parser.parse_args()

    generate_csv(datafile=args.datafile, year=args.year)

    db_connection = mariadb.connect(host='<hostname>', user='<username>', db='<databasename>')
    cursor = db_connection.cursor()

    create_tmpdb_cmd = '''load data infile "/path/of/network_attack.csv" into table network_attack_tmp fields terminated by ';'; '''
    cursor.execute(create_tmpdb_cmd)
    db_connection.commit()

    q_distinct_cmd = ''' select distinct(snort_alert_id) from network_attack_tmp; '''
    cursor.execute(q_distinct_cmd)

    dist_snort_id = cursor.fetchall()

    for snort_id in dist_snort_id:
        q_utc_last_cmd = ''' select * from network_attack_tmp where snort_alert_id="%s" order by date_time_utc desc; '''%(snort_id[0])
        q_count_cmd = ''' select count(*) from network_attack_tmp where snort_alert_id="%s"; '''%(snort_id[0])

        cursor.execute(q_utc_last_cmd)
        data_utc_last = cursor.fetchone()

        cursor.execute(q_count_cmd)
        count = cursor.fetchone()

        check_snort_id_cmd = ''' select count from network_attack where snort_alert_id="%s" ;''' %(data_utc_last[0])
        cursor.execute(check_snort_id_cmd)
        old_count = cursor.fetchone()

        if old_count:
           new_count = old_count[0] + count[0]
           update_count_cmd = ''' update network_attack set count="%s", date_time_utc="%s" where snort_alert_id="%s";'''%(new_count, data_utc_last[1], data_utc_last[0])
           cursor.execute(update_count_cmd)
           db_connection.commit()
        else:
           in_data_cmd = ''' insert into network_attack (snort_alert_id,
                                                         date_time_utc,
                                                         source_ip,
                                                         source_port,
                                                         protocol,
                                                         destination_ip,
                                                         destination_port,
                                                         count)
                                                 values ("%s","%s","%s","%s","%s","%s","%s","%s");
                         ''' %                          (data_utc_last[0],
                                                         data_utc_last[1],
                                                         data_utc_last[2],
                                                         data_utc_last[3],
                                                         data_utc_last[4],
                                                         data_utc_last[5],
                                                         data_utc_last[6],
                                                         count[0]);
           cursor.execute(in_data_cmd)
           db_connection.commit()

    drop_tmpdb_cmd = ''' delete from network_attack_tmp; '''
    cursor.execute(drop_tmpdb_cmd)
    db_connection.commit()

    cursor.close()
