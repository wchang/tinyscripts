import os,sys
import time
import random
import argparse
import line_profiler
import MySQLdb as mariadb
import multiprocessing
from Queue import PriorityQueue

class Job:
    def __init__(self, year, filepath):
        self.filepath = filepath.strip()
        self.year = year
        return

    def run(self):
        file = open(self.filepath,'r')
        set_autocommit_cmd = ''' set autocommit=0; '''

        print self.filepath

        db_connection = mariadb.connect(host='<host>', user='<user>', db='<dbname>')
        db_cursor = db_connection.cursor()
        db_cursor.execute(set_autocommit_cmd)

        for line in open(self.filepath):
            line = file.readline().strip()

            if "[**]" in line:
               first_line_data = line.split("[")
               snort_alert_id = first_line_data[2].split("]")[0]
               description = first_line_data[2].split("]")[1]

            elif "->" in line:
               date_time = line.split(".")[0].replace('-',' ').replace('/','-')
               date_string =  self.year+"-"+date_time
               utc_time = time.mktime(time.strptime(date_string,'%Y-%m-%d %H:%M:%S'))

               source = line.split()[1]
               source_ip = source.split(":")[0]
               try:
                   source_port = source.split(":")[1]
               except:
                   source_port = ""

               destination = line.split()[3]
               destination_ip = destination.split(":")[0]
               try:
                   destination_port = destination.split(":")[1]
               except:
                   destination_port = ""

            elif "TTL" in line:
               protocol = line.split()[0]

               check_snort_id_cmd = ''' select count, time from network_attack where snort_alert_id="%s" and source_ip="%s" for update;''' %(snort_alert_id, source_ip)
               db_cursor.execute(check_snort_id_cmd)
               id_count_time = db_cursor.fetchone()
               if id_count_time:
                  id_count=id_count_time[0]+1
                  if float(id_count_time[1])<utc_time:
                     update_count_cmd = ''' update network_attack set description="%s",
                                                                      time="%s",
                                                                      source_port="%s",
                                                                      protocol="%s",
                                                                      destination_ip="%s",
                                                                      destination_port="%s",
                                                                      count="%s"
                                                                      where snort_alert_id="%s" and source_ip="%s";
                                        '''%                          (description,
                                                                       utc_time,
                                                                       source_port,
                                                                       protocol,
                                                                       destination_ip,
                                                                       destination_port,
                                                                       id_count,
                                                                       snort_alert_id,
                                                                       source_ip);
                  else:
                     update_count_cmd = ''' update network_attack set count="%s" where snort_alert_id="%s" and source_ip="%s";'''%(id_count, snort_alert_id, source_ip)

                  try:
                     db_cursor.execute(update_count_cmd)
                     db_connection.commit()
                  except:
                     print update_count_cmd

               else:
                  id_count = 1
                  in_data_cmd = ''' insert into network_attack (snort_alert_id,
                                                                description,
                                                                time,
                                                                source_ip,
                                                                source_port,
                                                                protocol,
                                                                destination_ip,
                                                                destination_port,
                                                                count)
                                                        values ("%s","%s","%s","%s","%s","%s","%s","%s","%s");
                                ''' %                          (snort_alert_id,
                                                                description,
                                                                utc_time,
                                                                source_ip,
                                                                source_port,
                                                                protocol,
                                                                destination_ip,
                                                                destination_port,
                                                                id_count);

                  try:
                      db_cursor.execute(in_data_cmd)
                      db_connection.commit()
                  except:
                      print in_data_cmd

        db_cursor.close()
        db_connection.close()
        file.close()
def run_job(*args):
    queue = args[0]
    while queue.qsize() > 0:
          job = queue.get()
          job.run()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), add_help=True)

    parser.add_argument('--year', dest='year', action='store', required=True, help='Please enter the record year')
    parser.add_argument('--datafile_list', dest='datafile_list', action='store', required=True, help='Please enter the list of paths for the data files')
    parser.add_argument('--num_processes', dest='num_processes', action='store', default=1, help='Set up the unmber of processes you are going to use')

    args = parser.parse_args()
    db_queue = multiprocessing.Queue()

    file_list=[]
    files = open(args.datafile_list,'r')
    for line in files.readlines():
        file_list.append(line)
    files.close()

    index = range(len(file_list))
    random.shuffle(index)

    for idx in index:
        db_queue.put(Job(args.year, file_list[idx]))

    for process in range(int(args.num_processes)):
        worker = multiprocessing.Process(target=run_job, args=(db_queue,))
        worker.start()
        time.sleep(5)
