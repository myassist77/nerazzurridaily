"""YouTube publishing helpers for the Composio REMOTE WORKBENCH (they need its
run_composio_tool / proxy_execute / get_mount_file_* globals). Load with:

    exec(open('/home/user/nd-social/tools/nd_publish.py').read())          # gh_commit, wait_live, brevo_today_campaign
    exec(open('/home/user/nd-social/tools/nd_social_publish.py').read())   # everything below

then, in the 6:45 AM social run:

    vid   = yt_upload('pack/ND-2026-09-21-ed20-slug.mp4', title, description, tags, privacy='unlisted')
    yt_thumb(vid, 'pack/ND-2026-09-21-ed20-slug-thumb-16x9.png')
    cid   = yt_comment(vid, pinned_text)          # works on unlisted/public, 404s while private
    state_write(20, {...})                         # data/social-ed20.json, committed with the MP4

and in the 9:00 AM flip run:

    yt_privacy(vid, 'public')

Rules baked in: uploads are never public on first write (the 9:00 task flips them, which is the
owner's veto window); nothing here deletes a video; a failure raises so the caller can report it.
Proven against the live channel Sept 20, 2026: upload + thumbnail work; a comment on a PRIVATE
video returns 404 videoNotFound, which is why the default privacy is 'unlisted', not 'private'.
"""
import json, os, shutil, time

YT_ACCOUNT = 'youtube_verse-achy'
CHANNEL_ID = 'UCn2IfD6wnrqCNx9PefPFmkQ'
CATEGORY_SPORTS = '17'
MOUNT = '/mnt/files/nd-social'          # the only place get_mount_file_* can see
YT_API = 'https://www.googleapis.com/youtube/v3'


def _unwrap2(x):
    while isinstance(x, dict) and 'data' in x and isinstance(x['data'], dict):
        x = x['data']
    return x or {}


def _stage(path):
    """Copy a build artifact into the cloud-backed mount so it can be handed to Composio."""
    os.makedirs(MOUNT, exist_ok=True)
    dst = os.path.join(MOUNT, os.path.basename(path))
    if os.path.abspath(path) != os.path.abspath(dst):
        shutil.copyfile(path, dst)
    return dst


def _s3key(path):
    k, e = get_mount_file_s3_key(_stage(path))
    if e or not k:
        raise RuntimeError(f's3key {path}: {e or "empty"}')
    return k


def _pub_url(path):
    u, e = get_mount_file_url(_stage(path))
    if e or not u:
        raise RuntimeError(f'public url {path}: {e or "empty"}')
    return u


def _yt(slug, args):
    r, e = run_composio_tool(slug, args, print_schema_for_tool=False, account=YT_ACCOUNT)
    if e:
        raise RuntimeError(f'{slug}: {e[:400]}')
    return _unwrap2(r)


def yt_upload(mp4, title, description, tags, privacy='unlisted', category=CATEGORY_SPORTS):
    """Upload the short. NEVER pass privacy='public' here — the 9:00 task flips it."""
    if privacy not in ('unlisted', 'private'):
        raise ValueError("first upload is 'unlisted' (or 'private'); the flip task makes it public")
    if len(title) > 100:
        raise ValueError(f'title is {len(title)} chars, YouTube caps it at 100')
    if len(description.encode()) > 5000:
        raise ValueError('description over 5000 bytes')
    d = _yt('YOUTUBE_UPLOAD_VIDEO', {
        'title': title, 'description': description, 'tags': list(tags), 'categoryId': str(category),
        'privacyStatus': privacy,
        'videoFilePath': {'name': os.path.basename(mp4), 'mimetype': 'video/mp4', 's3key': _s3key(mp4)}})
    vid = (d.get('response_data') or d).get('id')
    if not vid:
        raise RuntimeError(f'upload returned no video id: {str(d)[:300]}')
    return vid


def yt_thumb(video_id, png_16x9):
    """Custom thumbnail from a public URL. 16:9 only — Shorts' 9:16 thumbnail is Studio/YPP only."""
    return _yt('YOUTUBE_UPDATE_THUMBNAIL', {'videoId': video_id, 'thumbnailUrl': _pub_url(png_16x9)})


def yt_comment(video_id, text):
    """Top-level comment. Pinning it has no API — the owner taps that, or it stays unpinned."""
    d = _yt('YOUTUBE_POST_COMMENT', {'videoId': video_id, 'channelId': CHANNEL_ID, 'textOriginal': text})
    return (d.get('response_data') or d).get('id')


def yt_privacy(video_id, status):
    if status not in ('public', 'unlisted', 'private'):
        raise ValueError(status)
    return _yt('YOUTUBE_UPDATE_VIDEO', {'video_id': video_id, 'privacy_status': status})


def yt_status(video_id):
    """{'privacyStatus','uploadStatus','title','seconds'} straight from the API — never assumed."""
    r, e = proxy_execute(method='GET', endpoint=f'{YT_API}/videos', toolkit='youtube',
                         query_params={'part': 'status,snippet,contentDetails', 'id': video_id})
    if e:
        raise RuntimeError(f'videos.list: {e[:300]}')
    items = _unwrap2(r).get('items') or []
    if not items:
        return None
    it = items[0]
    return {'privacyStatus': it['status'].get('privacyStatus'), 'uploadStatus': it['status'].get('uploadStatus'),
            'title': it['snippet'].get('title'), 'duration': it.get('contentDetails', {}).get('duration')}


def yt_url(video_id):
    return f'https://www.youtube.com/shorts/{video_id}'


# ---- the day's social state, committed to the repo so the 9:00 flip task can read it ----

def state_path(n):
    return f'data/social-ed{n}.json'


def state_write(n, obj, root=None):
    """Write data/social-ed{N}.json into the checkout. Commit it with gh_commit()."""
    root = root or os.environ.get('ND_SOCIAL_ROOT', '/home/user/nd-social')
    p = os.path.join(root, state_path(n))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p, 'w'), indent=2, ensure_ascii=False)
    return p


def state_read(n):
    """Read it back from the published repo (raw), so the flip task needs no checkout."""
    import requests
    u = f'https://raw.githubusercontent.com/myassist77/nerazzurridaily/main/{state_path(n)}'
    r = requests.get(u, timeout=30)
    return r.json() if r.status_code == 200 else None


def latest_edition():
    """Highest edition number published in the repo, from sitemap.xml."""
    import re, requests
    x = requests.get('https://raw.githubusercontent.com/myassist77/nerazzurridaily/main/sitemap.xml', timeout=30).text
    ns = [int(m) for m in re.findall(r'/p/edition-(\d+)/', x)]
    if not ns:
        raise RuntimeError('no editions in sitemap.xml')
    return max(ns)
