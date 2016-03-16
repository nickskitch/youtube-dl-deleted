#!/usr/bin/env python
__author__ = 'Nick'


import os
import sys
import argparse
import yaml
import argparse
import subprocess
import signal
import time
import glob
import shutil
import datetime
from time import gmtime, strftime

script_base_dir = os.path.dirname(os.path.realpath(__file__))
config_yaml_path='./config'
default_config_yaml_path='config.yaml'

# todo: fix countdown timer to make it run on config value
# todo: credentials file into config
# todo: get script into source control

def main():
    global default_config_yaml_path

    parse_args()
    while True:
        config_yaml = parse_yaml(default_config_yaml_path)

        for channel_id in config_yaml['channelIds']:
            youtube_dl(channel_id['channel_name'],channel_id['channel_url'],str(config_yaml['download_settings'][0]['number_of_downloads']))
            check_for_deleted(channel_id['channel_name'],channel_id['channel_url'],str(config_yaml['download_settings'][0]['number_of_downloads']))
            cleanup(channel_id['channel_name'],str(config_yaml['download_settings'][0]['number_of_downloads']))
            print(str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))+'anti hammer sleep for 36 secs.. ')
            time.sleep(36) # anti hammer
        print(str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))+' sleeping for 20 mins..')
        time.sleep(1200) # 20 mins
    print ('complete')

def parse_args():
    parser = argparse.ArgumentParser(description='upload deleted youtube videos when found')
    parser.add_argument("-c", "--config_yaml",nargs="+", help='name of the config.yaml in the ./config dir. e.g. config.yaml')
    args = parser.parse_args()

    if args.config_yaml:
        config_yaml_path = args.config_yaml

    if not args.config_yaml:
        config_yaml_path = default_config_yaml_path

    return config_yaml_path

def parse_yaml(config_yaml_path):
    # read stage yaml into memory for later use
    print("parse_yaml: " + config_yaml_path)
    with open(os.path.join("./config/",config_yaml_path), 'r') as f:
        config_yaml = yaml.safe_load(f)
        f.close()
    return config_yaml

def youtube_dl(channel_name, channel_url, max_downloads):
    global script_base_dir

    path = os.path.join('./data/', channel_name + '/work')
    print(path)
    if not os.path.isdir(path):
        print('dir not found, creating: ' + path)
        os.system('mkdir -p "'+ path + '"')

    os.chdir(path)

    print('checking for new content: ' + channel_name)
    cmd = 'youtube-dl -f bestvideo[ext!=webm]+bestaudio[ext!=webm]/best[ext!=webm] --max-downloads ' + max_downloads + ' -citw "' + channel_url + '"'
    os.system(cmd)


    os.chdir(script_base_dir)

def check_for_deleted(channel_name, channel_url, max_downloads):
    global script_base_dir
    path = os.path.join('./data/', channel_name + '/work')
    path_deleted = os.path.join('./data/', channel_name + '/deleted')

    if not os.path.isdir(path): os.system('mkdir -p "'+ path + '"')
    if not os.path.isdir(path_deleted): os.system('mkdir -p "'+ path_deleted + '"')
    os.chdir(path)


    print('check_for_deleted videos : '+channel_name)
    cmd = 'youtube-dl -citw "' + channel_url + '" --get-filename'

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    files = glob.glob("*.mp4")

    counter=1
    finished=False
    ## iterate through mp4 files and try to find them on channel to find out which files can be deleted
    while True and finished==False:
        counter=int(counter)+1
        if counter >= 10: finished=True
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() != None:
            break
        if not files: break

        sys.stdout.write('.')
        for file in files:
            #upload_youtube(file,str(channel_name).title())   #  good for testing
            file_noext = os.path.splitext(os.path.basename(file))[0]

            if file_noext in nextline:
                files.remove(file)
                # break if all files accounted for

        sys.stdout.flush()

    # kill the process
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except:
        pass

    # upload files that were not found on users channel
    for file in files:


        from_path = os.path.join(script_base_dir,'./data/'+ channel_name + '/work')
        from_path=os.path.join(from_path ,file)

        to_path=os.path.join(script_base_dir , './data/'+ channel_name + '/deleted')
        to_path=os.path.join(to_path ,file)

        if not os.path.isfile(to_path):
            # move the file to the deleted folder and upload to youtube
            print('from : '+ from_path + ' \n\nto : '+to_path)
            shutil.move(from_path, to_path)

            # strip off eronious crap from file name, proper case channel name, then upload to youtube
            upload_youtube(file,channel_name)
            time.sleep(5)
        else:
            os.remove(file)

    os.chdir(script_base_dir)

def cleanup(channel_name,max_downloads):
    #ls -ltr -A1
    path = os.path.join('./data/', channel_name + '/work')

    os.chdir(path)
    files = glob.glob("*.mp4")
    files.sort(key=os.path.getmtime)
    files.reverse()
    files_to_keep = files[:int(max_downloads)]
    print('keeping files: '+ str(files_to_keep))
    for file in files:
        if file not in files_to_keep:
            print('cleaning up: ' + file)
            os.remove(file)

    os.chdir(script_base_dir)

def upload_youtube(file,channel_name):
    global script_base_dir

    print('upload_youtube: '+str(channel_name).title()+' '+file)
    path=script_base_dir
    os.chdir(path)

    file_noext = os.path.splitext(os.path.basename(file))[0]


    creds=os.path.join(script_base_dir,'Led_creds.json')
    title=str(channel_name).title() + ' - '+ file_noext[:-(len(file_noext)-file_noext.rfind('-'))]

    cmd='youtube-upload' +' --title="'+title+'" --credentials-file='+creds+' "' + script_base_dir+'/data/'+channel_name+'/deleted/'+ str(file)+'"'

    try:
        #os.system(python_bin+" "+ script_file+cmd)
        os.system(cmd)
    except:
        pass


if __name__ == "__main__":
    main()




