from genericpath import isdir, isfile
import subprocess
from sys import stderr, stdout
from flask import Blueprint, request, render_template
from flask_restful import abort
from werkzeug.utils import secure_filename
from . import app
import os

procs = Blueprint('procs', __name__)


@procs.route('/', methods = ['GET'])
def hello():
    return {'test': True}, 200

@procs.route('/upld', methods = ['POST'])
def upload_file():
    app.logger.info(f"INFO start upload")
    upload_dir_base = os.getenv('UPLOAD_DIR')
    app.logger.info(f"INFO upload base dir {upload_dir_base}")

    if not os.path.isdir(upload_dir_base):
        try:
            os.makedirs(upload_dir_base)
        except OSError as err_os:
            app.logger.info(err_os)

    if request.method == 'POST':
        f = request.files['myfile']
        file_name = secure_filename(f.filename)
        if not file_name.endswith('mp4'):
            return {'error': f'{file_name} must ends with mp4'}
        save_dir = os.path.join(upload_dir_base, os.path.splitext(file_name)[0])
        
        try:
            os.makedirs(save_dir)
        except OSError as err_os_name:
            app.logger.info(err_os_name)
            abort(404)
        else:
            app.logger.info(f"INFO Directory created {save_dir}")

        try:
            file_to_save = os.path.join(save_dir, file_name)
            f.save(file_to_save)
        except OSError as err_os_name:
            app.logger.info(err_os_name)
            abort(404)
        else:
            app.logger.info(f"INFO File saved {file_to_save}")

        ffmpeg_run(save_dir, file_name)
        return 'file uploaded successfully'


def ffmpeg_run(directory, file):

    ffmpeg_bin = os.getenv('FFMPEG')

    if not os.path.isfile(ffmpeg_bin):
        app.logger.info(f"ERROR ffmpeg not found {ffmpeg_bin}")
        abort(404)

    ffmpeg_cmd = [
        ffmpeg_bin, '-i', os.path.join(directory, file),
        "-hide_banner", "-loglevel", "quiet",
        '-filter_complex',
        '[0:v]split=3[v1][v2][v3];[v1]copy[v1out];[v2]scale=w=1280:h=720[v2out];[v3]scale=w=640:h=360[v3out]',
        "-map", "[v1out]", 
        "-c:v:0", "libx264", 
        "-x264-params", "nal-hrd=cbr:force-cfr=1", 
        "-b:v:0", "5M", 
        "-maxrate:v:0", "5M", 
        "-minrate:v:0", "5M", 
        "-bufsize:v:0", "10M", 
        "-preset", "slow", 
        "-g", "48",
        "-sc_threshold", "0",
        "-keyint_min", "48",
        "-map", "[v2out]", 
        "-c:v:1", "libx264", 
        "-x264-params", "nal-hrd=cbr:force-cfr=1", 
        "-b:v:1", "3M", 
        "-maxrate:v:1", "3M", 
        "-minrate:v:1", "3M", 
        "-bufsize:v:1", "3M", 
        "-preset", "slow", 
        "-g", "48", 
        "-sc_threshold", "0", 
        "-keyint_min", "48",
        "-map", "[v3out]", 
        "-c:v:2", "libx264", 
        "-x264-params", "nal-hrd=cbr:force-cfr=1", 
        "-b:v:2", "1M", 
        "-maxrate:v:2", "1M", 
        "-minrate:v:2", "1M", 
        "-bufsize:v:2", "1M", 
        "-preset", "slow", 
        "-g", "48", 
        "-sc_threshold", "0", 
        "-keyint_min", "48",
        "-map", "a:0", 
        "-c:a:0", "aac", 
        "-b:a:0", "96k", 
        "-ac", "2", 
        "-map", "a:0", 
        "-c:a:1", "aac", 
        "-b:a:1", "96k", 
        "-ac", "2", 
        "-map", "a:0", 
        "-c:a:2", "aac", 
        "-b:a:2", "48k", 
        "-ac", "2",
        "-t", "30",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_playlist_type", "vod",
        "-hls_flags", "independent_segments",
        "-hls_segment_type", "mpegts",
        "-hls_segment_filename", os.path.join(directory, "stream_%v/data%02d.ts"),
        "-master_pl_name", os.path.join(directory, "master.m3u8"),
        "-var_stream_map", 'v:0,a:0 v:1,a:1 v:2,a:2',
        os.path.join(directory, "stream_%v.m3u8")
    ]

    print(ffmpeg_cmd)
    try:
        probe_output = subprocess.run(ffmpeg_cmd,
                                      universal_newlines=True)
                                    #   stderr=subprocess.PIPE,
                                    #   stdout=subprocess.PIPE)
        
        out_dict = {"status": True, "data": probe_output.stdout}
    except subprocess.CalledProcessError as es:
        out_dict = {"status": False, "msg": es}
    
    return out_dict