from flask import Flask, request, jsonify, render_template_string
import requests
import json
import os
from datetime import datetime
import threading
import time
import schedule
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# Configurações
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
INSTAGRAM_USER_ID = os.environ.get('INSTAGRAM_USER_ID', '17841459866694291')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

# Configurar Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# Armazenamento em memória
scheduled_posts = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CriTech Scheduler</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --yellow: #F5C400;
            --black: #0a0a0a;
            --dark: #111111;
            --card: #1a1a1a;
            --border: #2a2a2a;
            --text: #ffffff;
            --muted: #888888;
        }
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
        input, textarea, select { width: 100%; background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14px; transition: border-color 0.2s; outline: none; }
        input:focus, textarea:focus { border-color: var(--yellow); }
        textarea { resize: vertical; min-height: 100px; }

        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 18px;
            position: relative;
        }
        .upload-area:hover { border-color: var(--yellow); background: #1a1500; }
        .upload-area.dragover { border-color: var(--yellow); background: #1a1500; }
        .upload-area input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
        .upload-icon { font-size: 36px; margin-bottom: 10px; }
        .upload-text { font-size: 14px; color: var(--muted); }
        .upload-text span { color: var(--yellow); font-weight: 600; }

        .preview-box { background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 16px; min-height: 120px; margin-bottom: 16px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; text-align: center; overflow: hidden; }
        .preview-box img { max-width: 100%; max-height: 200px; border-radius: 8px; object-fit: cover; }
        .preview-box video { max-width: 100%; max-height: 200px; border-radius: 8px; }

        .upload-progress { display: none; background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 16px; }
        .progress-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-top: 8px; }
        .progress-fill { height: 100%; background: var(--yellow); border-radius: 3px; transition: width 0.3s; width: 0%; }
        .progress-text { font-size: 13px; color: var(--muted); }

        .btn { width: 100%; padding: 14px; background: var(--yellow); color: var(--black); border: none; border-radius: 10px; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; cursor: pointer; transition: opacity 0.2s, transform 0.1s; margin-top: 8px; }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-secondary { background: transparent; border: 1px solid var(--border); color: var(--text); }
        .btn-secondary:hover { border-color: var(--yellow); color: var(--yellow); }

        .alert { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; display: none; }
        .alert-success { background: #0a1a0a; color: #4caf50; border: 1px solid #1a3a1a; }
        .alert-error { background: #1a0a0a; color: #f44336; border: 1px solid #3a1a1a; }

        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
        .stat-number { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; color: var(--yellow); }
        .stat-label { font-size: 12px; color: var(--muted); margin-top: 4px; }

        .post-list { display: flex; flex-direction: column; gap: 12px; }
        .post-item { background: var(--black); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; align-items: center; gap: 14px; }
        .post-thumb { width: 48px; height: 48px; background: var(--border); border-radius: 8px; flex-shrink: 0; overflow: hidden; }
        .post-thumb img { width: 100%; height: 100%; object-fit: cover; }
        .post-info { flex: 1; min-width: 0; }
        .post-caption { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
        .post-time { font-size: 11px; color: var(--muted); }
        .post-status { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; flex-shrink: 0; }
        .status-pending { background: #1a1a00; color: var(--yellow); border: 1px solid #333300; }
        .status-published { background: #0a1a0a; color: #4caf50; border: 1px solid #1a3a1a; }
        .status-error { background: #1a0a0a; color: #f44336; border: 1px solid #3a1a1a; }
        .delete-btn { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 16px; padding: 4px; transition: color 0.2s; }
        .delete-btn:hover { color: #f44336; }
        .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
        .empty-state .emoji { font-size: 40px; margin-bottom: 12px; }

        .file-info { background: #1a1500; border: 1px solid #333300; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 13px; color: var(--yellow); display: none; }
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

            <!-- Upload Area -->
            <div class="upload-area" id="upload-area">
                <input type="file" id="file-input" accept="image/*,video/*" onchange="handleFileSelect(this)">
                <div class="upload-icon">📁</div>
                <div class="upload-text">
                    <span>Clique para selecionar</span> ou arraste aqui<br>
                    <small style="color:var(--muted);margin-top:6px;display:block">Fotos e vídeos • Qualidade original mantida</small>
                </div>
            </div>

            <div class="file-info" id="file-info">📎 <span id="file-name"></span></div>

            <div class="upload-progress" id="upload-progress">
                <div class="progress-text" id="progress-text">Enviando para a nuvem...</div>
                <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
            </div>

            <div class="preview-box" id="preview" style="display:none"></div>

            <div class="form-group" id="caption-group">
                <label>Legenda</label>
                <textarea id="caption" placeholder="Escreva a legenda do post...&#10;&#10;Use # para hashtags e @ para menções"></textarea>
            </div>

            <div class="form-group">
                <label>Agendar para (deixe vazio para publicar agora)</label>
                <input type="datetime-local" id="schedule-time">
            </div>

            <button class="btn" id="publish-btn" onclick="handlePublish()" disabled>⚡ Selecione uma mídia primeiro</button>
        </div>

        <div class="card">
            <h2><div class="icon">📋</div> Posts Agendados</h2>
            <div id="posts-list" class="post-list">
                <div class="empty-state"><div class="emoji">📭</div><p>Nenhum post agendado ainda</p></div>
            </div>
        </div>
    </div>
</div>

<script>
    let postType = 'feed';
    let uploadedMediaUrl = null;
    let selectedFile = null;

    function setType(type, btn) {
        postType = type;
        document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('caption-group').style.display = type === 'stories' ? 'none' : 'block';
    }

    function handleFileSelect(input) {
        const file = input.files[0];
        if (!file) return;
        selectedFile = file;

        document.getElementById('file-info').style.display = 'block';
        document.getElementById('file-name').textContent = file.name + ' (' + (file.size / 1024 / 1024).toFixed(1) + ' MB)';

        // Preview local
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('preview');
            preview.style.display = 'flex';
            if (file.type.startsWith('video/')) {
                preview.innerHTML = `<video src="${e.target.result}" style="max-width:100%;max-height:200px;border-radius:8px" controls></video>`;
            } else {
                preview.innerHTML = `<img src="${e.target.result}" style="max-width:100%;max-height:200px;border-radius:8px;object-fit:cover">`;
            }
        };
        reader.readAsDataURL(file);

        // Upload para Cloudinary
        uploadToCloudinary(file);
    }

    async function uploadToCloudinary(file) {
        const btn = document.getElementById('publish-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Enviando mídia...';

        const progress = document.getElementById('upload-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        progress.style.display = 'block';

        // Animação de progresso
        let pct = 0;
        const interval = setInterval(() => {
            pct = Math.min(pct + 5, 85);
            progressFill.style.width = pct + '%';
        }, 200);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            clearInterval(interval);

            if (data.success) {
                uploadedMediaUrl = data.url;
                progressFill.style.width = '100%';
                progressText.textContent = '✅ Mídia enviada com sucesso!';
                progressText.style.color = '#4caf50';

                btn.disabled = false;
                btn.textContent = '🚀 Publicar no Instagram';

                setTimeout(() => { progress.style.display = 'none'; }, 2000);
            } else {
                clearInterval(interval);
                progressText.textContent = '❌ Erro no upload: ' + data.error;
                progressText.style.color = '#f44336';
                btn.textContent = '⚡ Selecione uma mídia primeiro';
            }
        } catch(e) {
            clearInterval(interval);
            progressText.textContent = '❌ Erro de conexão!';
            progressText.style.color = '#f44336';
        }
    }

    async function handlePublish() {
        if (!uploadedMediaUrl) return showAlert('Selecione uma mídia primeiro!', 'error');

        const caption = document.getElementById('caption').value;
        const scheduleTime = document.getElementById('schedule-time').value;
        const btn = document.getElementById('publish-btn');

        btn.disabled = true;

        if (scheduleTime) {
            // Agendar
            btn.textContent = '⏳ Agendando...';
            try {
                const res = await fetch('/schedule', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        media_url: uploadedMediaUrl,
                        caption: caption,
                        schedule_time: scheduleTime,
                        post_type: postType
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showAlert('✅ Post agendado com sucesso!', 'success');
                    resetForm();
                    loadPosts();
                } else {
                    showAlert('Erro: ' + data.error, 'error');
                }
            } catch(e) {
                showAlert('Erro de conexão!', 'error');
            }
        } else {
            // Publicar agora
            btn.textContent = '⏳ Publicando...';
            try {
                const res = await fetch('/publish-now', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        media_url: uploadedMediaUrl,
                        caption: caption,
                        post_type: postType
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showAlert('🎉 Publicado com sucesso no Instagram!', 'success');
                    resetForm();
                    loadPosts();
                } else {
                    showAlert('Erro: ' + data.error, 'error');
                }
            } catch(e) {
                showAlert('Erro de conexão!', 'error');
            }
        }

        btn.disabled = false;
        btn.textContent = '🚀 Publicar no Instagram';
    }

    function resetForm() {
        uploadedMediaUrl = null;
        selectedFile = null;
        document.getElementById('file-input').value = '';
        document.getElementById('caption').value = '';
        document.getElementById('schedule-time').value = '';
        document.getElementById('preview').style.display = 'none';
        document.getElementById('file-info').style.display = 'none';
        document.getElementById('publish-btn').disabled = true;
        document.getElementById('publish-btn').textContent = '⚡ Selecione uma mídia primeiro';
    }

    function showAlert(msg, type) {
        const el = document.getElementById('alert');
        el.textContent = msg;
        el.className = `alert alert-${type}`;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    }

    async function deletePost(id) {
        await fetch(`/delete/${id}`, {method: 'DELETE'});
        loadPosts();
    }

    async function loadPosts() {
        const res = await fetch('/posts');
        const posts = await res.json();

        document.getElementById('stat-pending').textContent = posts.filter(p => p.status === 'pending').length;
        document.getElementById('stat-published').textContent = posts.filter(p => p.status === 'published').length;
        document.getElementById('stat-total').textContent = posts.length;

        const list = document.getElementById('posts-list');
        if (posts.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="emoji">📭</div><p>Nenhum post agendado ainda</p></div>';
            return;
        }

        list.innerHTML = posts.map(p => `
            <div class="post-item">
                <div class="post-thumb">
                    ${p.media_url ? `<img src="${p.media_url}" onerror="this.style.display='none'">` : ''}
                </div>
                <div class="post-info">
                    <div class="post-caption">${p.caption || '(sem legenda)'}</div>
                    <div class="post-time">${p.post_type.toUpperCase()} · ${p.schedule_time || 'Publicado agora'}</div>
                </div>
                <span class="post-status status-${p.status}">
                    ${p.status === 'pending' ? '⏳ Agendado' : p.status === 'published' ? '✅ Publicado' : '❌ Erro'}
                </span>
                <button class="delete-btn" onclick="deletePost(${p.id})">🗑️</button>
            </div>
        `).join('');
    }

    // Drag and drop
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
    setInterval(loadPosts, 30000);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Arquivo inválido'})

        # Verificar se é vídeo ou imagem
        is_video = file.content_type.startswith('video/')
        resource_type = 'video' if is_video else 'image'

        # Upload para Cloudinary com qualidade original
        result = cloudinary.uploader.upload(
            file,
            resource_type=resource_type,
            quality='auto:best',
            folder='critech'
        )

        return jsonify({
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id']
        })

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
    if result['success']:
        post = {
            'id': len(scheduled_posts) + 1,
            'media_url': data.get('media_url'),
            'caption': data.get('caption', ''),
            'schedule_time': None,
            'post_type': data.get('post_type', 'feed'),
            'status': 'published',
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
            return {'success': False, 'error': 'Token de acesso não configurado'}

        if post_type == 'reels':
            container_data = {'media_type': 'REELS', 'video_url': media_url, 'caption': caption, 'access_token': token}
        elif post_type == 'stories':
            if media_url.lower().endswith(('.mp4', '.mov')):
                container_data = {'media_type': 'VIDEO', 'video_url': media_url, 'is_stories': True, 'access_token': token}
            else:
                container_data = {'image_url': media_url, 'is_stories': True, 'access_token': token}
        else:
            container_data = {'image_url': media_url, 'caption': caption, 'access_token': token}

        container_res = requests.post(f'https://graph.instagram.com/v21.0/{user_id}/media', data=container_data)
        container_json = container_res.json()

        if 'id' not in container_json:
            return {'success': False, 'error': str(container_json.get('error', {}).get('message', 'Erro ao criar container'))}

        container_id = container_json['id']

        if post_type in ['reels'] or media_url.lower().endswith(('.mp4', '.mov')):
            time.sleep(15)

        publish_res = requests.post(
            f'https://graph.instagram.com/v21.0/{user_id}/media_publish',
            data={'creation_id': container_id, 'access_token': token}
        )
        publish_json = publish_res.json()

        if 'id' in publish_json:
            return {'success': True, 'post_id': publish_json['id']}
        else:
            return {'success': False, 'error': str(publish_json.get('error', {}).get('message', 'Erro ao publicar'))}

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
            except:
                pass

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
