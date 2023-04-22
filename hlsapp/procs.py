from curses.ascii import isdigit
from functools import wraps
from genericpath import isfile
from http.client import REQUESTED_RANGE_NOT_SATISFIABLE
from flask import Blueprint, request, abort
from werkzeug.utils import secure_filename
from . import app
import os
import re
import subprocess
import requests
import shutil


procs = Blueprint('procs', __name__)


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == os.getenv('API_KEY'):
            return view_function(*args, **kwargs)
        else:
            app.logger.info(f"ERROR in authentication {request.headers.get('x-api-key')}")
            abort(401, "password")
    return decorated_function


@procs.route('/upld', methods = ['POST'])
@require_appkey
def upload_file():
    app.logger.info(f"INFO start upload")
    upload_dir_base = os.getenv('UPLOAD_DIR')
    tmp_dir = os.getenv('TMP_DIR')
    app.logger.info(f"INFO upload base dir {upload_dir_base}, {tmp_dir}")

    if not upload_dir_base.endswith('/'):
        upload_dir_base = f"{upload_dir_base}/"

    if not os.path.isdir(upload_dir_base):
        app.logger.info(f"ERROR directory {upload_dir_base} does not exist")
        abort(500, f"ERROR directory {upload_dir_base} does not exist")

    if not os.path.isdir(tmp_dir):
        app.logger.info(f"ERROR directory {tmp_dir} does not exist")
        abort(500, f"ERROR directory {tmp_dir} does not exist")

    input_data_url = request.form['videoUrl']
    post_id = request.form['postId']
    app.logger.info(f"INFO input data {input_data_url} {post_id}")

    file = input_data_url.replace('https://gospodari.com/wp-content/uploads/', upload_dir_base)
    if not os.path.isfile(file):
        abort(404, file)

    file_name_base = os.path.basename(file)
    file_name = secure_filename(file_name_base).replace(' ', '_').lower()
    file_name_tmp = f"tmp_{post_id}_{file_name}"
    file_name_enc = f"enc_{post_id}_{file_name}"

    try:
        file_tmp_to_save = os.path.join(tmp_dir, file_name_tmp)
        file_enc_to_save = os.path.join(tmp_dir, file_name_enc)

        if not file_tmp_to_save.endswith('mp4'):
            abort(404, "file must ends with mp4")
        if os.path.isfile(file_enc_to_save):
            app.logger.info(f"ERROR file {file_enc_to_save} alredy exists")
            abort(500, f"ERROR file {file_name} alredy exists")
        
        shutil.copyfile(file, file_tmp_to_save)
        os.rename(file_tmp_to_save, file_enc_to_save)
    except OSError as err_os_name:
        app.logger.info(err_os_name)
        abort(500)
    else:
        app.logger.info(f"INFO File saved {file_enc_to_save}")
        return '', 200


    # file_name = secure_filename(f.filename).replace(' ', '_').lower()
    # file_name_tmp = f"tmp_{post_id}_{file_name}"
    # file_name_enc = f"enc_{post_id}_{file_name}"
    # try:
    #     file_tmp_to_save = os.path.join(upload_dir_base, file_name_tmp)
    #     file_enc_to_save = os.path.join(upload_dir_base, file_name_enc)
    #     if not file_tmp_to_save.endswith('mp4'):
    #         abort(404, "file must ends with mp4")
    #     if os.path.isfile(file_enc_to_save):
    #         app.logger.info(f"ERROR file {file_enc_to_save} alredy exists")
    #         abort(500, f"ERROR file {file_name} alredy exists")
    #     f.save(file_tmp_to_save)
    #     os.rename(file_tmp_to_save, file_enc_to_save)
    # except OSError as err_os_name:
    #     app.logger.info(err_os_name)
    #     abort(500)
    # else:
    #     app.logger.info(f"INFO File saved {file_enc_to_save}")
    #     return '', 200


@procs.route('/start', methods = ['GET'])
@require_appkey
def start_encoding():
    pid_file = os.getenv('PID_FILE')
    if os.path.isfile(pid_file):
        msg = f"PID file found {pid_file} process is running"
        app.logger.info(msg)
        abort(403, msg)
    else:
        try:
            with open(pid_file, "w") as pid_handler:
                pass
        except OSError as oe:
            msg = f"ERROR could not create pid file {pid_file}, {oe}"
            app.logger.info(msg)
            abort(500, msg)

    upload_dir_base = os.getenv('TMP_DIR')
    files_in_tmp = os.listdir(upload_dir_base)
    files_to_encode = list(filter(lambda x: x.startswith('enc_'), files_in_tmp))

    dst_dir_base = os.getenv('STORAGE_DIR')
    
    try:
        os.makedirs(dst_dir_base, exist_ok=True)
        app.logger.info(f"INFO directory {dst_dir_base}")
    except OSError as oe:
        app.logger.info(oe)
        abort(500, oe)

    if len(files_to_encode) > 0:
        for file in files_to_encode:
            post_id = re.search('enc_(\d+)_', file).group(1)
            file_name = re.search('enc_\d+_(.*)', file).group(1)
            dst_dir_name = re.search('enc_\d+_(.*).mp4', file).group(1)
            dst_dir = os.path.join(dst_dir_base, dst_dir_name)
            dst_file = os.path.join(dst_dir, file_name)
            enc_file = os.path.join(upload_dir_base, file)
            try:
                os.makedirs(dst_dir, exist_ok=True)
                app.logger.info(f"INFO directory {dst_dir}")
                shutil.move(enc_file, dst_file)
            except OSError as oe:
                app.logger.info(oe)
                abort(500, oe)
            ffmpeg_run(dst_dir, file_name)
            hls_url = f"{os.getenv('HLS_HOST')}/{dst_dir_name}/master.m3u8"
            app.logger.info(f"INFO hls url {hls_url}")
            connect_api(hls_url, post_id)
        os.remove(pid_file)
        return '', 200
    else:
        print(len(list(files_to_encode)))
        os.remove(pid_file)
        return '', 200


def connect_api(hls_url, post_id):
    header = {"x-api-key" : os.getenv('REMOTE_KEY')}
    url = f"{os.getenv('REMOTE_API')}/{post_id}"
    request_post = requests.post(url, headers=header, data={'url': hls_url})
    if request_post.status_code != 200:
        app.logger.info(f"ERROR respond code from {url} is {request_post.status_code}")
        abort(500, f"Remote status {request_post.status_code}")
    else:
        app.logger.info(f"INFO log {request_post.text}")

#     dir_name = os.path.splitext(file_name)[0]
#     save_dir = os.path.join(upload_dir_base, dir_name)
    
#     try:
#         os.makedirs(save_dir)
#     except OSError as err_os_name:
#         app.logger.info(err_os_name)
#         abort(500)
#     else:
#         app.logger.info(f"INFO Directory created {save_dir}")

#     try:
#         file_to_save = os.path.join(save_dir, file_name)
#         f.save(file_to_save)
#     except OSError as err_os_name:
#         app.logger.info(err_os_name)
#         abort(500)
#     else:
#         app.logger.info(f"INFO File saved {file_to_save}")

#     ffmpeg_run(save_dir, file_name)
#     hls_url = f"{os.getenv('HLS_HOST')}/{dir_name}/master.m3u8"

#     try:
#         request_response = requests.head(hls_url)
#         return_status = request_response.status_code
#     except requests.exceptions.ConnectionError as ce:
#         app.logger.info(f"ERROR {ce}")
#         abort(404, description="could not connect to m3u8")
    
#     if return_status == 200:
#         app.logger.info(f"INFO Success {hls_url}")
#         return hls_url
#     else:
#         app.logger.info(f"ERROR status code of {hls_url} is {return_status}")
#         abort(404, description=f"m3u8 response is {return_status}")


def ffmpeg_run(directory, file):

    ffmpeg_bin = os.getenv('FFMPEG')
    if not os.path.isfile(ffmpeg_bin):
        app.logger.info(f"ERROR ffmpeg not found {ffmpeg_bin}")
        abort(404)

    ffmpeg_cmd = [
        ffmpeg_bin, '-i', os.path.join(directory, file),
        "-hide_banner", "-loglevel", "quiet",
        '-filter_complex',
        '[0:v]yadif,split=3[v1][v2][v3];[v1]copy[v1out];[v2]scale=w=1280:h=720[v2out];[v3]scale=w=640:h=360[v3out]',
        "-map", "[v1out]", 
        "-c:v:0", "libx264", 
        # "-x264-params", "nal-hrd=cbr:force-cfr=1", 
        "-b:v:0", "4M", 
        "-maxrate:v:0", "4M", 
        "-minrate:v:0", "4M", 
        "-bufsize:v:0", "8M", 
        "-preset", "veryfast", 
        "-g", "48",
        "-sc_threshold", "0",
        "-keyint_min", "48",
        "-map", "[v2out]", 
        "-c:v:1", "libx264", 
        # "-x264-params", "nal-hrd=cbr:force-cfr=1", 
        "-b:v:1", "2M", 
        "-maxrate:v:1", "2M", 
        "-minrate:v:1", "2M", 
        "-bufsize:v:1", "2M", 
        "-preset", "veryfast", 
        "-g", "48", 
        "-sc_threshold", "0", 
        "-keyint_min", "48",
        "-map", "[v3out]", 
        "-c:v:2", "libx264", 
        # "-x264-params", "nal-hrd=cbr:force-cfr=1", 
        "-b:v:2", "1M", 
        "-maxrate:v:2", "1M", 
        "-minrate:v:2", "1M", 
        "-bufsize:v:2", "1M", 
        "-preset", "veryfast", 
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
        # "-t", "10",
        "-f", "hls",
        "-hls_time", "10",
        "-hls_playlist_type", "vod",
        "-hls_flags", "independent_segments",
        "-hls_segment_type", "mpegts",
        "-hls_segment_filename", "stream_%v/data%02d.ts",
        "-master_pl_name", "master.m3u8",
        "-use_localtime_mkdir", "1",
        "-var_stream_map", 'v:0,a:0 v:1,a:1 v:2,a:2',
        os.path.join(directory, "stream_%v.m3u8")
    ]

    try:
        os.chdir(directory)
        subprocess.run(ffmpeg_cmd, universal_newlines=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
    except subprocess.CalledProcessError as es:
        app.logger.info(f"{es}")
        abort(404)