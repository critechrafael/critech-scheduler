from flask import Flask, request, jsonify, render_template_string
import requests
import os
from datetime import datetime
import threading
import time
import schedule
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
INSTAGRAM_USER_ID = os.environ.get('INSTAGRAM_USER_ID', '17841459866694291')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

scheduled_posts = []

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CriTech Scheduler</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root { --yellow: #F5C400; --black: #0a0a0a; --dark: #111111; --card: #1a1a1a; --border: #2a2a2a; --text: #ffffff; --muted: #888888; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: var(--black); color: var(--text); font-family: 'DM Sans', sans-serif; min-height: 100vh; }
        header { background: var(--dark); border-bottom: 1px solid var(--border); padding: 20px 40px; display: flex; align-items: center; gap: 16px; }
        .logo { width: 42px; height: 42px; background: var(--yellow); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-family: 'Syne', sans-serif; font-weight: 800; color: var(--black); font-size: 18px; }
        header h1 { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 20px; }
        header span { color: var(--yellow); }
        .badge { background: #1a2a1a; color: #4caf50; border: 1px solid #2a4a2a; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-left: auto; }
        .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } header { padding: 16px 20px; } }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 28px; }
        .card h2 { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 18px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
        .card h2 .icon { width: 32px; height: 32px; background: var(--yellow); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .type-selector { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 18px; }
        .type-btn { padding: 10px; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--muted); cursor: pointer; font-size: 13px; transition: all 0.2s; text-align: center; }
        .type-btn.active { border-color: var(--yellow); color: var(--yellow); background: #1a1500; }
        .form-group { margin-bottom: 18px; }
        label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 8px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
        input, textarea { width: 100%; background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14px; outline: none; transition: border-color 0.2s; }
        input:focus, textarea:focus { border-color: var(--yellow); }
        textarea { resize: vertical; min-height: 100px; }
        .upload-area { border: 2px dashed var(--border); border-radius: 10px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.2s; background: var(--black); position: relative; }
        .upload-area:hover, .upload-area.dragover { border-color: var(--yellow); background: #1a1500; }
        .upload-area input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; padding: 0; border: none; }
        .upload-icon { font-size: 32px; margin-bottom: 8px; }
        .upload-text { font-size: 14px; color: var(--muted); }
        .upload-text span { color: var(--yellow); font-weight: 600; }
        .upload-progress { display: none; margin-top: 12px; }
        .progress-bar { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
        .progress-fill { height: 100%; background: var(--yellow); border-radius: 2px; transition: width 0.3s; width: 0%; }
        .preview-box { background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 16px; min-height: 120px; margin-bottom: 16px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; text-align: center; overflow: hidden; }
        .preview-box img, .preview-box video { max-width: 100%; max-height: 200px; border-radius: 8px; object-fit: cover; }
        .btn { width: 100%; padding: 14px; background: var(--yellow); color: var(--black); border: none; border-radius: 10px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; cursor: pointer; transition: opacity 0.2s, transform 0.1s; margin-top: 8px; }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .alert { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; display: none; word-break: break-word; }
        .alert-success { background: #0a1a0a; color: #4caf50; border: 1px solid #1a3a1a; }
        .alert-error { background: #1a0a0a; color: #f44336; border: 1px solid #3a1a1a; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
        .stat-number { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; color: var(--yellow); }
        .stat-label { font-size: 12px; color: var(--muted); margin-top: 4px; }
        .post-list { display: flex; flex-direction: column; gap: 12px; max-height: 500px; overflow-y: auto; }
        .post-item { background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; align-items: flex-start; gap: 14px; }
        .post-thumb { width: 48px; height: 48px; background: var(--border); border-radius: 8px; flex-shrink: 0; overflow: hidden; }
        .post-thumb img { width: 100%; height: 100%; object-fit: cover; }
        .post-info { flex: 1; min-width: 0; }
        .post-caption { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
        .post-time { font-size: 11px; color: var(--muted); }
        .post-error { font-size: 10px; color: #f44336; margin-top: 4px; word-break: break-word; }
        .post-status { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; flex-shrink: 0; white-space: nowrap; }
        .status-pending { background: #1a1a00; color: var(--yellow); border: 1px solid #333300; }
        .status-published { background: #0a1a0a; color: #4caf50; border: 1px solid #1a3a1a; }
        .status-error { background: #1a0a0a; color: #f44336; border: 1px solid #3a1a1a; }
        .delete-btn { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 16px; padding: 4px; transition: color 0.2s; flex-shrink: 0; }
        .delete-btn:hover { color: #f44336; }
        .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
        .empty-state .emoji { font-size: 40px; margin-bottom: 12px; }
    </style>
</head>
<body>
<header>
    <div class="logo">CT</div>
    <h1>CriTech <span>Scheduler</span></h1>
    <div class="badge">● Instagram Conectado</div>
</header>
<div class="container">
    <div class="stats">
        <div class="stat"><div class="stat-number" id="stat-pending">0</div><div class="stat-label">Agendados</div></div>
        <div class="stat"><div class="stat-number" id="stat-published">0</div><div class="stat-label">Publicados</div></div>
        <div class="stat"><div class="stat-number" id="stat-total">0</div><div class="stat-label">Total</div></div>
    </div>
    <div class="grid">
        <div class="card">
            <h2><div class="icon">✏️</div> Novo Post</h2>
            <div id="alert" class="alert"></div>
            <div class="type-selector">
                <button class="type-btn active" onclick="setType('feed', this)">📸 Feed</button>
                <button class="type-btn" onclick="setType('reels', this)">🎬 Reels</button>
                <button class="type-btn" onclick="setType('stories', this)">⭕ Stories</button>
            </div>
            <div class="form-group">
                <label>📁 Upload do Computador</label>
                <div class="upload-area" id="upload-area">
                    <input type="file" id="file-input" accept="image/*,video/*" onchange="handleFileSelect(this)">
                    <div class="upload-icon">☁️</div>
                    <div class="upload-text">Arraste sua foto ou vídeo aqui<br>ou <span>clique para selecionar</span></div>
                    <div class="upload-progress" id="upload-progress">
                        <div style="font-size:12px;color:var(--muted);margin-bottom:6px" id="upload-status">Enviando...</div>
                        <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
                    </div>
                </div>
            </div>
            <div class="preview-box" id="preview"><span>Prévia aparecerá aqui</span></div>
            <div class="form-group" id="caption-group">
                <label>Legenda</label>
                <textarea id="caption" placeholder="Escreva a legenda...&#10;Use # para hashtags e @ para menções"></textarea>
            </div>
            <div class="form-group">
                <label>Agendar para (deixe vazio para publicar agora)</label>
                <input type="datetime-local" id="schedule-time">
            </div>
            <button class="btn" id="btn-publish" onclick="handlePost()">🚀 Publicar no Instagram</button>
        </div>
        <div class="card">
            <h2><div class="icon">📋</div> Posts Agendados</h2>
            <div id="posts-list" class="post-list">
                <div class="empty-state"><div class="emoji">📭</div><p>Nenhum post ainda</p></div>
            </div>
        </div>
    </div>
</div>
<script>
    let postType = 'feed';
    let uploadedUrl = '';

    function setType(type, btn) {
        postType = type;
        document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('caption-group').style.display = type === 'stories' ? 'none' : 'block';
    }

    async function handleFileSelect(input) {
        const file = input.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('preview');
            if (file.type.startsWith('video/')) {
                preview.innerHTML = `<video src="${e.target.result}" style="max-width:100%;max-height:200px;border-radius:8px" controls></video>`;
            } else {
                preview.innerHTML = `<img src="${e.target.result}" style="max-width:100%;max-height:200px;border-radius:8px;object-fit:cover">`;
            }
        };
        reader.readAsDataURL(file);
        const progress = document.getElementById('upload-progress');
        const progressFill = document.getElementById('progress-fill');
        const uploadStatus = document.getElementById('upload-status');
        progress.style.display = 'block';
        uploadStatus.textContent = 'Enviando para a nuvem...';
        let p = 0;
        const interval = setInterval(() => { p += 5; if (p <= 90) progressFill.style.width = p + '%'; }, 200);
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            clearInterval(interval);
            if (data.success) {
                uploadedUrl = data.url;
                progressFill.style.width = '100%';
                uploadStatus.textContent = '✅ Pronto para publicar!';
            } else {
                uploadStatus.textContent = '❌ Erro: ' + data.error;
            }
        } catch(e) {
            clearInterval(interval);
            uploadStatus.textContent = '❌ Erro de conexão!';
        }
    }

    function showAlert(msg, type) {
        const el = document.getElementById('alert');
        el.textContent = msg;
        el.className = `alert alert-${type}`;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 10000);
    }

    async function handlePost() {
        if (!uploadedUrl) return showAlert('Faça o upload de uma imagem ou vídeo primeiro!', 'error');
        const scheduleTime = document.getElementById('schedule-time').value;
        const caption = document.getElementById('caption').value;
        const btn = document.getElementById('btn-publish');
        btn.disabled = true;

        if (scheduleTime) {
            btn.textContent = 'Agendando...';
            try {
                const res = await fetch('/schedule', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ media_url: uploadedUrl, caption, schedule_time: scheduleTime, post_type: postType })
                });
                const data = await res.json();
                if (data.success) { showAlert('✅ Post agendado com sucesso!', 'success'); resetForm(); loadPosts(); }
                else showAlert('Erro: ' + data.error, 'error');
            } catch(e) { showAlert('Erro de conexão!', 'error'); }
        } else {
            btn.textContent = 'Publicando...';
            try {
                const res = await fetch('/publish-now', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ media_url: uploadedUrl, caption, post_type: postType })
                });
                const data = await res.json();
                if (data.success) { showAlert('🎉 Publicado com sucesso no Instagram!', 'success'); resetForm(); loadPosts(); }
                else showAlert('❌ Erro da API Instagram: ' + data.error, 'error');
            } catch(e) { showAlert('Erro de conexão!', 'error'); }
        }
        btn.disabled = false;
        btn.textContent = '🚀 Publicar no Instagram';
    }

    function resetForm() {
        uploadedUrl = '';
        document.getElementById('caption').value = '';
        document.getElementById('preview').innerHTML = '<span>Prévia aparecerá aqui</span>';
        document.getElementById('upload-progress').style.display = 'none';
        document.getElementById('file-input').value = '';
        document.getElementById('schedule-time').value = '';
    }

    async function deletePost(id) {
        await fetch('/delete/' + id, {method: 'DELETE'});
        loadPosts();
    }

    async function loadPosts() {
        try {
            const res = await fetch('/posts');
            const posts = await res.json();
            document.getElementById('stat-pending').textContent = posts.filter(p => p.status === 'pending').length;
            document.getElementById('stat-published').textContent = posts.filter(p => p.status === 'published').length;
            document.getElementById('stat-total').textContent = posts.length;
            const list = document.getElementById('posts-list');
            if (posts.length === 0) {
                list.innerHTML = '<div class="empty-state"><div class="emoji">📭</div><p>Nenhum post ainda</p></div>';
                return;
            }
            list.innerHTML = posts.slice().reverse().map(p => `
                <div class="post-item">
                    <div class="post-thumb">${p.media_url ? `<img src="${p.media_url}" onerror="this.style.display='none'">` : ''}</div>
                    <div class="post-info">
                        <div class="post-caption">${p.caption || '(sem legenda)'}</div>
                        <div class="post-time">${p.post_type.toUpperCase()} · ${p.schedule_time ? p.schedule_time.replace('T', ' ') : 'Imediato'}</div>
                        ${p.error_msg ? `<div class="post-error">⚠️ ${p.error_msg}</div>` : ''}
                    </div>
                    <span class="post-status status-${p.status}">
                        ${p.status === 'pending' ? '⏳' : p.status === 'published' ? '✅' : '❌'}
                    </span>
                    <button class="delete-btn" onclick="deletePost(${p.id})">🗑️</button>
                </div>
            `).join('');
        } catch(e) {}
    }

    const uploadArea = document.getElementById('upload-area');
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) {
            const input = document.getElementById('file-input');
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            handleFileSelect(input);
        }
    });

    loadPosts();
    setInterval(loadPosts, 15000);
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'})
        file = request.files['file']
        resource_type = 'video' if file.content_type.startswith('video/') else 'image'
        result = cloudinary.uploader.upload(
            file,
            resource_type=resource_type,
            quality='auto:best',
            folder='critech-scheduler'
        )
        return jsonify({'success': True, 'url': result['secure_url']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/posts', methods=['GET'])
def get_posts():
    return jsonify(scheduled_posts)

@app.route('/schedule', methods=['POST'])
def schedule_post():
    data = request.json
    post = {
        'id': len(scheduled_posts) + 1,
        'media_url': data.get('media_url'),
        'caption': data.get('caption', ''),
        'schedule_time': data.get('schedule_time'),
        'post_type': data.get('post_type', 'feed'),
        'status': 'pending',
        'error_msg': None,
        'created_at': datetime.now().isoformat()
    }
    scheduled_posts.append(post)
    return jsonify({'success': True, 'post': post})

@app.route('/publish-now', methods=['POST'])
def publish_now():
    data = request.json
    result = publish_to_instagram(
        data.get('media_url'),
        data.get('caption', ''),
        data.get('post_type', 'feed')
    )
    post = {
        'id': len(scheduled_posts) + 1,
        'media_url': data.get('media_url'),
        'caption': data.get('caption', ''),
        'schedule_time': None,
        'post_type': data.get('post_type', 'feed'),
        'status': 'published' if result['success'] else 'error',
        'error_msg': result.get('error') if not result['success'] else None,
        'created_at': datetime.now().isoformat()
    }
    scheduled_posts.append(post)
    return jsonify(result)

@app.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global scheduled_posts
    scheduled_posts = [p for p in scheduled_posts if p['id'] != post_id]
    return jsonify({'success': True})

def publish_to_instagram(media_url, caption, post_type):
    try:
        token = ACCESS_TOKEN
        user_id = INSTAGRAM_USER_ID

        if not token:
            return {'success': False, 'error': 'Token nao configurado'}

        is_video = any(media_url.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.wmv'])

        if post_type == 'stories':
            if is_video:
                params = {'media_type': 'STORIES', 'video_url': media_url, 'access_token': token}
            else:
                params = {'media_type': 'STORIES', 'image_url': media_url, 'access_token': token}
        elif post_type == 'reels':
            params = {'media_type': 'REELS', 'video_url': media_url, 'caption': caption, 'access_token': token}
        else:
            if is_video:
                params = {'media_type': 'VIDEO', 'video_url': media_url, 'caption': caption, 'access_token': token}
            else:
                params = {'image_url': media_url, 'caption': caption, 'access_token': token}

        container_res = requests.post(
            f'https://graph.instagram.com/v21.0/{user_id}/media',
            data=params, timeout=30
        )
        container_json = container_res.json()

        if 'id' not in container_json:
            error_msg = container_json.get('error', {}).get('message', str(container_json))
            return {'success': False, 'error': error_msg}

        container_id = container_json['id']

        if is_video or post_type == 'reels':
            time.sleep(15)

        publish_res = requests.post(
            f'https://graph.instagram.com/v21.0/{user_id}/media_publish',
            data={'creation_id': container_id, 'access_token': token},
            timeout=30
        )
        publish_json = publish_res.json()

        if 'id' in publish_json:
            return {'success': True, 'post_id': publish_json['id']}
        else:
            error_msg = publish_json.get('error', {}).get('message', str(publish_json))
            return {'success': False, 'error': error_msg}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_scheduled_posts():
    now = datetime.now()
    for post in scheduled_posts:
        if post['status'] == 'pending' and post['schedule_time']:
            try:
                scheduled_time = datetime.fromisoformat(post['schedule_time'])
                if now >= scheduled_time:
                    result = publish_to_instagram(post['media_url'], post['caption'], post['post_type'])
                    post['status'] = 'published' if result['success'] else 'error'
                    post['error_msg'] = result.get('error') if not result['success'] else None
            except Exception as e:
                post['status'] = 'error'
                post['error_msg'] = str(e)

def run_scheduler():
    schedule.every(1).minutes.do(check_scheduled_posts)
    while True:
        schedule.run_pending()
        time.sleep(30)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
